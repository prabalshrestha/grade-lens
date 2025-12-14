#!/usr/bin/env python3
"""
Main workflow for grading assignments using the flexible Grade Lens system
"""

import os
import sys
import argparse
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    SUBMISSIONS_BASE_DIR,
    OUTPUT_BASE_DIR,
    ASSIGNMENTS_BASE_DIR,
)
from src.processors.document_processor import DocumentProcessor
from src.processors.input_processor import InputProcessor
from src.agents.qa_grading_agent import QAGradingAgent
from src.agents.config_generator_agent import ConfigGeneratorAgent
from src.utils.output_manager import OutputManager
from src.models.assignment_config import AssignmentConfig
from src.models.grading_result import AssignmentGrade

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class GradingWorkflow:
    """Main workflow for processing and grading submissions"""

    def __init__(
        self,
        assignment_id: str,
        submissions_base_dir: str = SUBMISSIONS_BASE_DIR,
        output_base_dir: str = OUTPUT_BASE_DIR,
        assignments_base_dir: str = ASSIGNMENTS_BASE_DIR,
        answer_key_pdf: Optional[str] = None,
        grading_mode: str = "full",
        enable_image_processing: bool = True,
        enable_code_execution: bool = False,
    ):
        self.assignment_id = assignment_id
        self.submissions_base_dir = submissions_base_dir
        self.output_base_dir = output_base_dir
        self.answer_key_pdf = answer_key_pdf
        self.grading_mode = grading_mode
        self.enable_image_processing = enable_image_processing
        self.enable_code_execution = enable_code_execution

        # Initialize components
        self.input_processor = InputProcessor(assignments_base_dir)
        self.doc_processor = DocumentProcessor()
        self.grading_agent = QAGradingAgent(
            OPENAI_API_KEY, model=OPENAI_MODEL, grading_mode=grading_mode
        )
        self.output_manager = OutputManager(output_base_dir)

        # Initialize multi-stage components
        from src.agents.answer_extraction_agent import AnswerExtractionAgent
        from src.agents.report_generator import ReportGenerator
        from src.agents.code_extraction_agent import CodeExtractionAgent
        from src.agents.code_evaluation_agent import CodeEvaluationAgent
        from src.processors.submission_grouper import SubmissionGrouper

        self.answer_extractor = AnswerExtractionAgent(
            OPENAI_API_KEY,
            model=OPENAI_MODEL,
            enable_image_processing=enable_image_processing,
        )
        self.report_generator = ReportGenerator(
            OPENAI_API_KEY,
            model=OPENAI_MODEL,
        )

        # Initialize code processing components
        self.code_extractor = CodeExtractionAgent(
            OPENAI_API_KEY,
            model=OPENAI_MODEL,
        )
        self.code_evaluator = CodeEvaluationAgent(
            OPENAI_API_KEY,
            model=OPENAI_MODEL,
            enable_execution=enable_code_execution,
        )
        self.submission_grouper = SubmissionGrouper()

        # Load assignment configuration
        self.assignment_config: Optional[AssignmentConfig] = None

    def load_assignment_config(self) -> bool:
        """Load and validate assignment configuration"""
        logger.info(f"Loading assignment configuration: {self.assignment_id}")

        self.assignment_config = self.input_processor.load_assignment(
            self.assignment_id
        )

        if not self.assignment_config:
            logger.error(f"Failed to load assignment: {self.assignment_id}")
            return False

        # Load answer key PDF if provided via command line
        if self.answer_key_pdf:
            if not os.path.exists(self.answer_key_pdf):
                logger.error(f"Answer key PDF not found: {self.answer_key_pdf}")
                return False

            logger.info(f"Loading answer key from: {self.answer_key_pdf}")
            answer_key_text = self.doc_processor.extract_text_from_file(
                self.answer_key_pdf
            )

            if answer_key_text:
                # Override/set the answer key text in config
                self.assignment_config.answer_key_text = answer_key_text
                logger.info(f"✓ Answer key loaded ({len(answer_key_text)} characters)")
            else:
                logger.warning("Could not extract text from answer key PDF")

        # Log if answer key is available
        if self.assignment_config.answer_key_text:
            logger.info("✓ Answer key available for grading reference")
        else:
            logger.info("ℹ No answer key provided (grading without reference)")

        logger.info(f"Assignment loaded: {self.assignment_config.assignment_name}")
        logger.info(f"Total questions: {len(self.assignment_config.questions)}")
        logger.info(f"Total points: {self.assignment_config.total_points}")
        logger.info(f"Grading mode: {self.grading_mode}")

        return True

    def get_submissions_directory(self) -> str:
        """Get the submissions directory for this assignment"""
        return os.path.join(self.submissions_base_dir, self.assignment_id)

    def setup_logging(self):
        """Setup assignment-specific logging"""
        # Create output directory (include grading mode if not full)
        if self.grading_mode != "full":
            output_dir = os.path.join(
                self.output_base_dir, f"{self.assignment_id}_{self.grading_mode}"
            )
        else:
            output_dir = os.path.join(self.output_base_dir, self.assignment_id)
        os.makedirs(output_dir, exist_ok=True)

        # Add file handler for this assignment
        log_file = os.path.join(output_dir, "grading.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(file_handler)

        logger.info(f"Logging to: {log_file}")

    def process_all_submissions(self) -> List[AssignmentGrade]:
        """Process all submissions for the assignment (with multi-file support)"""
        if not self.assignment_config:
            logger.error("Assignment configuration not loaded")
            return []

        # Setup logging
        self.setup_logging()

        logger.info("=" * 80)
        logger.info(
            f"Starting grading workflow for: {self.assignment_config.assignment_name}"
        )
        logger.info("=" * 80)

        # Get submissions directory
        submissions_dir = self.get_submissions_directory()

        if not os.path.exists(submissions_dir):
            logger.error(f"Submissions directory not found: {submissions_dir}")
            logger.error(f"Please create the directory and add submissions")
            return []

        # Get all submission files (including code files)
        submission_files = self.doc_processor.get_all_submissions(
            submissions_dir, extensions=[".pdf", ".docx", ".txt", ".py", ".java"]
        )
        logger.info(f"Found {len(submission_files)} file(s) to process")

        if not submission_files:
            logger.warning("No submission files found!")
            return []

        # Group files by student
        student_groups = self.submission_grouper.group_files_by_student(
            submission_files
        )
        logger.info(f"Grouped into {len(student_groups)} student submission(s)")

        # Process each student's group
        grades = []
        for i, (student_key, file_paths) in enumerate(student_groups.items(), 1):
            try:
                logger.info(f"\n[{i}/{len(student_groups)}] Processing: {student_key}")
                logger.info(
                    f"  Files ({len(file_paths)}): {[os.path.basename(f) for f in file_paths]}"
                )

                # Get student info from group
                student_info = self.submission_grouper.get_student_info(file_paths)
                student_name = student_info["student_name"]
                student_id = student_info["student_id"]
                is_late = student_info["is_late"]

                if is_late:
                    logger.info(f"  ⚠️  Marked as LATE submission")

                # Categorize files by type
                categorized = self.submission_grouper.categorize_files_by_type(
                    file_paths
                )
                code_files = categorized["code"]
                doc_files = categorized["document"]

                logger.info(
                    f"  Code files: {len(code_files)}, Document files: {len(doc_files)}"
                )

                # Process based on file types
                if code_files and not doc_files:
                    # Pure code submission
                    grade = self._grade_code_submission(
                        code_files, student_name, student_id, is_late
                    )
                elif doc_files and not code_files:
                    # Pure document submission (existing logic)
                    grade = self._grade_document_submission(
                        doc_files, student_name, student_id, is_late
                    )
                else:
                    # Mixed submission
                    grade = self._grade_mixed_submission(
                        code_files, doc_files, student_name, student_id, is_late
                    )

                if grade:
                    # Add file list
                    grade.file_list = [os.path.basename(f) for f in file_paths]
                    grades.append(grade)
                    logger.info(
                        f"Grade: {grade.total_score}/{grade.max_score} "
                        f"({grade.get_percentage():.1f}%)"
                    )
                    if grade.requires_human_review:
                        logger.warning(f"⚠️  Flagged for review: {grade.review_reason}")
                else:
                    logger.error(f"Failed to grade submission: {student_key}")

            except Exception as e:
                logger.error(f"Error processing {student_key}: {str(e)}", exc_info=True)
                # Create error grade
                error_grade = self.grading_agent._create_error_grade(
                    self.assignment_config,
                    student_info.get("student_name", "unknown"),
                    student_info.get("student_id", "unknown"),
                    f"{len(file_paths)} files",
                )
                grades.append(error_grade)

        logger.info("\n" + "=" * 80)
        logger.info(f"Completed grading {len(grades)} submission(s)")
        logger.info("=" * 80)

        return grades

    def _grade_code_submission(
        self, code_files: List[str], student_name: str, student_id: str, is_late: bool
    ) -> Optional[AssignmentGrade]:
        """Grade pure code submission"""
        logger.info("  Type: Code submission")

        try:
            # Extract code
            logger.info("  Stage 1: Extracting code...")
            code_submission = self.code_extractor.extract_code_submission(
                code_files, self.assignment_config
            )

            # Evaluate with hybrid approach
            logger.info("  Stage 2: Evaluating code...")
            code_evaluation = self.code_evaluator.evaluate_code(
                code_submission,
                self.assignment_config,
                test_cases=self.assignment_config.test_cases,
            )

            # Convert to standard format for grading
            logger.info("  Stage 3: Grading questions...")
            extracted_answers = self._convert_code_to_answers(
                code_submission, code_evaluation
            )

            # Use existing pipeline
            grade = self.grading_agent.grade_submission_with_extraction(
                self.assignment_config,
                student_name,
                extracted_answers,
                student_id,
                f"{len(code_files)} code file(s)",
            )

            if not grade:
                return None

            # Generate report
            logger.info("  Stage 4: Generating report...")
            report_data = self.report_generator.generate_report(
                grade.questions, self.assignment_config, student_name
            )

            # Update grade with report and code-specific data
            grade.overall_comment = report_data["overall_comment"]
            grade.strengths = report_data["strengths"]
            grade.areas_for_improvement = report_data["areas_for_improvement"]
            grade.requires_human_review = report_data["requires_human_review"]
            grade.review_reason = report_data["review_reason"]

            grade.is_late = is_late
            grade.file_count = len(code_files)
            grade.submission_type = "code"
            grade.code_evaluation = code_evaluation

            return grade

        except Exception as e:
            logger.error(f"Error grading code submission: {str(e)}", exc_info=True)
            return None

    def _grade_document_submission(
        self, doc_files: List[str], student_name: str, student_id: str, is_late: bool
    ) -> Optional[AssignmentGrade]:
        """Grade document submission (existing logic, adapted for multi-file)"""
        logger.info("  Type: Document submission")

        try:
            # Process all document files and combine their content
            if len(doc_files) == 1:
                # Single file - use existing pipeline
                primary_file = doc_files[0]

                # Check if file is empty
                file_size = os.path.getsize(primary_file)
                if file_size == 0:
                    logger.warning(f"  Empty file: {os.path.basename(primary_file)}")
                    grade = self.grading_agent.grade_empty_submission(
                        self.assignment_config,
                        student_name,
                        student_id,
                        os.path.basename(primary_file),
                    )
                    grade.is_late = is_late
                    grade.file_count = len(doc_files)
                    return grade

                # STAGE 1: Extract answers from single file
                logger.info("  Stage 1: Extracting answers...")
                extracted_answers = self.answer_extractor.extract_answers(
                    primary_file, self.assignment_config
                )
            else:
                # Multiple files - extract from each and combine
                logger.info(f"  Processing {len(doc_files)} document files...")

                all_extracted_answers = {}

                # Extract from each file
                for idx, doc_file in enumerate(doc_files, 1):
                    filename = os.path.basename(doc_file)
                    logger.info(f"    File {idx}/{len(doc_files)}: {filename}")

                    # Check if file is empty
                    file_size = os.path.getsize(doc_file)
                    if file_size == 0:
                        logger.warning(f"      Empty file, skipping")
                        continue

                    # Extract answers from this file
                    file_answers = self.answer_extractor.extract_answers(
                        doc_file, self.assignment_config
                    )

                    # Store with file context
                    for question_id, answer_data in file_answers.items():
                        if question_id not in all_extracted_answers:
                            all_extracted_answers[question_id] = {
                                "text": "",
                                "extracted_from_image": False,
                                "extraction_notes": f"Multi-file submission ({len(doc_files)} files)",
                            }

                        # Append answer from this file
                        if answer_data.get("text", "").strip():
                            all_extracted_answers[question_id][
                                "text"
                            ] += f"\n\n--- From {filename} ---\n{answer_data['text']}"

                        # Track if any came from images
                        if answer_data.get("extracted_from_image"):
                            all_extracted_answers[question_id][
                                "extracted_from_image"
                            ] = True

                extracted_answers = all_extracted_answers
                logger.info("  Combined answers from all files")

            # Check if any answers were extracted
            has_content = any(
                answer_data.get("text", "").strip()
                for answer_data in extracted_answers.values()
            )

            if not has_content:
                logger.warning(f"  No content extracted")
                submission_desc = (
                    f"{len(doc_files)} file(s)"
                    if len(doc_files) > 1
                    else os.path.basename(doc_files[0])
                )
                grade = self.grading_agent.grade_empty_submission(
                    self.assignment_config,
                    student_name,
                    student_id,
                    submission_desc,
                )
                grade.is_late = is_late
                grade.file_count = len(doc_files)
                return grade

            # STAGE 2: Grade each question individually
            logger.info("  Stage 2: Grading individual questions...")
            submission_desc = (
                f"{len(doc_files)} file(s)"
                if len(doc_files) > 1
                else os.path.basename(doc_files[0])
            )
            grade = self.grading_agent.grade_submission_with_extraction(
                self.assignment_config,
                student_name,
                extracted_answers,
                student_id,
                submission_desc,
            )

            if not grade:
                return None

            # STAGE 3: Generate comprehensive report
            logger.info("  Stage 3: Generating report...")
            report_data = self.report_generator.generate_report(
                grade.questions, self.assignment_config, student_name
            )

            # Update grade with report data
            grade.overall_comment = report_data["overall_comment"]
            grade.strengths = report_data["strengths"]
            grade.areas_for_improvement = report_data["areas_for_improvement"]
            grade.requires_human_review = report_data["requires_human_review"]
            grade.review_reason = report_data["review_reason"]

            grade.is_late = is_late
            grade.file_count = len(doc_files)
            grade.submission_type = "document"

            return grade

        except Exception as e:
            logger.error(f"Error grading document submission: {str(e)}", exc_info=True)
            return None

    def _grade_mixed_submission(
        self,
        code_files: List[str],
        doc_files: List[str],
        student_name: str,
        student_id: str,
        is_late: bool,
    ) -> Optional[AssignmentGrade]:
        """Grade submission with both code and documents"""
        logger.info("  Type: Mixed submission (code + documents)")

        try:
            # For mixed submissions, concatenate everything
            logger.info("  Stage 1: Extracting from all files...")

            # Extract from code files
            code_submission = self.code_extractor.extract_code_submission(
                code_files, self.assignment_config
            )

            # Extract from document files
            doc_text = ""
            for doc_file in doc_files:
                text = self.doc_processor.extract_text_from_file(doc_file)
                doc_text += (
                    f"\n\n--- Document: {os.path.basename(doc_file)} ---\n{text}"
                )

            # Combine content
            combined_content = code_submission["combined_code"] + "\n\n" + doc_text

            # Create temporary extracted answers with combined content
            # Let AI map content to questions
            extracted_answers = {}
            for question in self.assignment_config.questions:
                extracted_answers[question.id] = {
                    "text": combined_content,
                    "extracted_from_image": False,
                    "extraction_notes": f"Mixed submission: {len(code_files)} code + {len(doc_files)} document file(s)",
                }

            # Grade
            logger.info("  Stage 2: Grading questions...")
            grade = self.grading_agent.grade_submission_with_extraction(
                self.assignment_config,
                student_name,
                extracted_answers,
                student_id,
                f"{len(code_files) + len(doc_files)} files",
            )

            if not grade:
                return None

            # Generate report
            logger.info("  Stage 3: Generating report...")
            report_data = self.report_generator.generate_report(
                grade.questions, self.assignment_config, student_name
            )

            # Update grade
            grade.overall_comment = report_data["overall_comment"]
            grade.strengths = report_data["strengths"]
            grade.areas_for_improvement = report_data["areas_for_improvement"]
            grade.requires_human_review = report_data["requires_human_review"]
            grade.review_reason = report_data["review_reason"]

            grade.is_late = is_late
            grade.file_count = len(code_files) + len(doc_files)
            grade.submission_type = "mixed"

            return grade

        except Exception as e:
            logger.error(f"Error grading mixed submission: {str(e)}", exc_info=True)
            return None

    def _convert_code_to_answers(
        self, code_submission: dict, code_evaluation: dict
    ) -> Dict[str, Dict[str, Any]]:
        """Convert code submission to extracted answers format"""
        # Create answer entries for each question
        # For code assignments, typically all code answers all questions
        extracted_answers = {}

        combined_code = code_submission.get("combined_code", "")
        analysis = code_submission.get("analysis", "")
        ai_eval = code_evaluation.get("ai_evaluation", {})

        # Combine code, analysis, and evaluation
        full_content = f"{combined_code}\n\nCode Analysis:\n{analysis}"

        if ai_eval:
            full_content += f"\n\nAI Evaluation:\n{str(ai_eval)}"

        for question in self.assignment_config.questions:
            extracted_answers[question.id] = {
                "text": full_content,
                "extracted_from_image": False,
                "extraction_notes": f"Code submission with {code_submission.get('file_count', 0)} file(s)",
            }

        return extracted_answers

    def save_results(self, grades: List[AssignmentGrade]):
        """Save grading results"""
        if not grades:
            logger.warning("No grades to save")
            return

        logger.info("\nSaving results...")

        try:
            # Use modified assignment_id with grading mode suffix if not full
            output_id = (
                f"{self.assignment_id}_{self.grading_mode}"
                if self.grading_mode != "full"
                else self.assignment_id
            )

            saved_files = self.output_manager.save_results(
                output_id,
                grades,
                include_csv=True,
                include_json=True,
                include_detailed_json=True,
            )

            logger.info("\nOutput files created:")
            for format_name, file_path in saved_files.items():
                logger.info(f"  - {format_name}: {file_path}")

        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            raise

    def print_summary(self, grades: List[AssignmentGrade]):
        """Print summary statistics"""
        self.output_manager.print_summary(grades)

    def run(self):
        """Run the complete grading workflow"""
        try:
            # Load assignment configuration
            if not self.load_assignment_config():
                return False

            # Process all submissions
            grades = self.process_all_submissions()

            if not grades:
                logger.warning("No grades generated")
                return False

            # Save results
            self.save_results(grades)

            # Print summary
            self.print_summary(grades)

            logger.info("\n✓ Grading workflow completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Fatal error in grading workflow: {str(e)}", exc_info=True)
            return False


def list_assignments(assignments_base_dir: str = ASSIGNMENTS_BASE_DIR):
    """List all available assignments"""
    processor = InputProcessor(assignments_base_dir)
    assignments = processor.list_available_assignments()

    if not assignments:
        print("No assignments found.")
        print(f"Create assignments in: {assignments_base_dir}/")
        return

    print("\nAvailable Assignments:")
    print("-" * 60)

    for assignment_id in assignments:
        config = processor.load_assignment(assignment_id)
        if config:
            print(f"  {assignment_id}")
            print(f"    Name: {config.assignment_name}")
            print(f"    Questions: {len(config.questions)}")
            print(f"    Total Points: {config.total_points}")
            print()


def create_assignment_template(assignment_id: str, num_questions: int = 2):
    """Create a new assignment template"""
    processor = InputProcessor(ASSIGNMENTS_BASE_DIR)

    if processor.create_assignment_template(assignment_id, num_questions):
        print(f"\n✓ Created assignment template: {assignment_id}")
        print(f"  Location: {os.path.join(ASSIGNMENTS_BASE_DIR, assignment_id)}")
        print(f"\nNext steps:")
        print(f"  1. Edit config.json to customize the assignment")
        print(
            f"  2. Add student submissions to: {os.path.join(SUBMISSIONS_BASE_DIR, assignment_id)}/"
        )
        print(f"  3. Run: python main.py --assignment {assignment_id}")
    else:
        print(f"\n✗ Failed to create assignment template")


def generate_config_from_pdf(
    assignment_id: str,
    assignment_name: str,
    questions_pdf: str,
    answer_key_pdf: Optional[str] = None,
    course_code: Optional[str] = None,
    term: Optional[str] = None,
    auto_approve: bool = False,
):
    """Generate assignment configuration from PDF files"""

    print("\n" + "=" * 80)
    print("ASSIGNMENT CONFIG GENERATOR")
    print("=" * 80)
    print(f"Assignment ID: {assignment_id}")
    print(f"Assignment Name: {assignment_name}")
    print(f"Questions PDF: {questions_pdf}")
    print(f"Answer Key PDF: {answer_key_pdf or 'Not provided'}")
    print(f"Course: {course_code or 'Not specified'}")
    print(f"Term: {term or 'Not specified'}")
    print("=" * 80)

    # Check if files exist
    if not os.path.exists(questions_pdf):
        print(f"\n✗ Questions PDF not found: {questions_pdf}")
        return 1

    if answer_key_pdf and not os.path.exists(answer_key_pdf):
        print(f"\n✗ Answer key PDF not found: {answer_key_pdf}")
        return 1

    # Check if assignment already exists
    assignment_dir = os.path.join(ASSIGNMENTS_BASE_DIR, assignment_id)
    if os.path.exists(assignment_dir):
        print(f"\n⚠ Warning: Assignment '{assignment_id}' already exists")
        response = input("Overwrite existing configuration? (yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            print("Cancelled.")
            return 1

    try:
        # Initialize config generator
        print("\nInitializing config generator agent...")
        generator = ConfigGeneratorAgent(OPENAI_API_KEY, model=OPENAI_MODEL)

        # Generate configuration
        print("Analyzing PDFs and generating configuration...")
        print("(This may take 30-60 seconds depending on document length)")

        config = generator.generate_config(
            assignment_id=assignment_id,
            assignment_name=assignment_name,
            questions_pdf_path=questions_pdf,
            answer_key_pdf_path=answer_key_pdf,
            course_code=course_code,
            term=term,
        )

        # Validate configuration
        print("\nValidating generated configuration...")
        is_valid, issues = generator.validate_config(config)

        if not is_valid:
            print("\n⚠ Configuration validation failed:")
            for issue in issues:
                print(f"  - {issue}")
            print("\nPlease review and fix these issues manually.")

        # Show preview
        print("\n" + generator.preview_config(config))

        # Ask for approval (unless auto-approve)
        if not auto_approve:
            print("\n" + "=" * 80)
            print("Review the configuration above.")
            print("=" * 80)
            response = (
                input("\nSave this configuration? (yes/no/edit): ").strip().lower()
            )

            if response in ["no", "n"]:
                print("Configuration not saved.")
                return 1
            elif response in ["edit", "e"]:
                print(
                    "\n✓ Configuration will be saved. You can edit it manually after."
                )

        # Create assignment directory
        os.makedirs(assignment_dir, exist_ok=True)

        # Create submissions directory
        submissions_dir = os.path.join(SUBMISSIONS_BASE_DIR, assignment_id)
        os.makedirs(submissions_dir, exist_ok=True)

        # Save configuration
        config_path = os.path.join(assignment_dir, "config.json")
        generator.save_config(config, config_path, pretty=True)

        # Create README
        readme_path = os.path.join(assignment_dir, "README.md")
        with open(readme_path, "w") as f:
            f.write(f"# {assignment_name}\n\n")
            f.write(f"**Course:** {course_code or 'N/A'}  \n")
            f.write(f"**Term:** {term or 'N/A'}  \n")
            f.write(f"**Total Points:** {config.get('total_points', 0)}  \n\n")
            f.write(f"## Questions\n\n")
            f.write(
                f"This assignment has {len(config.get('questions', []))} questions.\n\n"
            )
            f.write(f"## Usage\n\n")
            f.write(
                f"1. Place student submissions in: `submissions/{assignment_id}/`\n"
            )
            f.write(f"2. Run grading: `python main.py --assignment {assignment_id}`\n")
            f.write(f"3. View results in: `output/{assignment_id}/`\n\n")
            f.write(f"## Configuration\n\n")
            f.write(
                f"Generated automatically from PDFs. Review and edit `config.json` if needed.\n"
            )

        print("\n" + "=" * 80)
        print("✓ SUCCESS")
        print("=" * 80)
        print(f"Configuration saved to: {config_path}")
        print(f"Assignment directory: {assignment_dir}")
        print(f"Submissions directory: {submissions_dir}")

        if not is_valid:
            print("\n⚠ Note: Please review and fix validation issues in config.json")

        print("\n" + "Next steps:")
        print(f"  1. Review/edit: {config_path}")
        print(f"  2. Add student submissions to: {submissions_dir}/")
        print(f"  3. Run: python main.py --assignment {assignment_id}")

        return 0

    except Exception as e:
        logger.error(f"Error generating configuration: {str(e)}", exc_info=True)
        print(f"\n✗ Error: {str(e)}")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Grade Lens - AI-Powered Assignment Grading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available assignments
  python main.py --list

  # Grade a specific assignment (default: full mode with answer key)
  python main.py --assignment cs361_hw5

  # Grade with basic rubric only (no criteria, no instructions, no answer key)
  python main.py --assignment cs361_hw7 --grading-mode basic

  # Grade with rubric + criteria + instructions (no answer key)
  python main.py --assignment cs361_hw7 --grading-mode standard

  # Grade with everything including answer key (default)
  python main.py --assignment cs361_hw7 --grading-mode full

  # Grade with answer key PDF (for better accuracy)
  python main.py --assignment cs361_hw6 --with-answer-key answers.pdf

  # Create a new assignment template (manual)
  python main.py --create my_assignment --questions 3

  # Generate config from PDFs (automatic)
  python main.py --generate-config cs361_hw6 \\
    --name "CS361 HW6" \\
    --questions-pdf homework6_questions.pdf \\
    --answer-key-pdf homework6_answers.pdf \\
    --course CS361 \\
    --term "Fall 2025"
        """,
    )

    parser.add_argument(
        "--assignment",
        "-a",
        type=str,
        help="Assignment ID to grade",
    )

    parser.add_argument(
        "--with-answer-key",
        type=str,
        metavar="PDF_PATH",
        help="Path to answer key PDF to use for grading (overrides config)",
    )

    parser.add_argument(
        "--grading-mode",
        type=str,
        choices=["basic", "standard", "full"],
        default="full",
        help="Grading mode: basic (rubric only), standard (rubric + criteria + instructions), full (everything including answer key)",
    )

    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all available assignments",
    )

    parser.add_argument(
        "--create",
        "-c",
        type=str,
        help="Create a new assignment template with the given ID",
    )

    parser.add_argument(
        "--generate-config",
        "-g",
        type=str,
        metavar="ASSIGNMENT_ID",
        help="Generate assignment config from PDF files (requires --name and --questions-pdf)",
    )

    parser.add_argument(
        "--name",
        "-n",
        type=str,
        help="Assignment name (used with --generate-config)",
    )

    parser.add_argument(
        "--questions-pdf",
        type=str,
        help="Path to questions PDF file (used with --generate-config)",
    )

    parser.add_argument(
        "--answer-key-pdf",
        type=str,
        help="Path to answer key PDF file (optional, used with --generate-config)",
    )

    parser.add_argument(
        "--course",
        type=str,
        help="Course code (optional, used with --generate-config)",
    )

    parser.add_argument(
        "--term",
        type=str,
        help="Academic term (optional, used with --generate-config)",
    )

    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Skip configuration review prompt (used with --generate-config)",
    )

    parser.add_argument(
        "--questions",
        "-q",
        type=int,
        default=2,
        help="Number of questions for new assignment template (default: 2)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--enable-code-execution",
        action="store_true",
        help="Enable code execution for test cases (disabled by default for security)",
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check API key
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not found. Please set it in your .env file")
        return 1

    # Handle list command
    if args.list:
        list_assignments()
        return 0

    # Handle create command
    if args.create:
        create_assignment_template(args.create, args.questions)
        return 0

    # Handle generate-config command
    if args.generate_config:
        # Validate required arguments
        if not args.name:
            logger.error("--name is required when using --generate-config")
            print("Error: --name is required when using --generate-config")
            return 1

        if not args.questions_pdf:
            logger.error("--questions-pdf is required when using --generate-config")
            print("Error: --questions-pdf is required when using --generate-config")
            return 1

        return generate_config_from_pdf(
            assignment_id=args.generate_config,
            assignment_name=args.name,
            questions_pdf=args.questions_pdf,
            answer_key_pdf=args.answer_key_pdf,
            course_code=args.course,
            term=args.term,
            auto_approve=args.auto_approve,
        )

    # Handle grading
    if args.assignment:
        workflow = GradingWorkflow(
            args.assignment,
            answer_key_pdf=args.with_answer_key,
            grading_mode=args.grading_mode,
            enable_code_execution=args.enable_code_execution,
        )
        success = workflow.run()
        return 0 if success else 1

    # No command specified
    parser.print_help()
    print("\nTip: Use --list to see available assignments")
    return 1


if __name__ == "__main__":
    sys.exit(main())
