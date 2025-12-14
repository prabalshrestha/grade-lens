#!/usr/bin/env python3
"""
Main workflow for grading assignments using the flexible Grade Lens system
"""

import os
import sys
import argparse
import logging
from typing import List, Optional
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
    ):
        self.assignment_id = assignment_id
        self.submissions_base_dir = submissions_base_dir
        self.output_base_dir = output_base_dir
        self.answer_key_pdf = answer_key_pdf
        self.grading_mode = grading_mode
        self.enable_image_processing = enable_image_processing

        # Initialize components
        self.input_processor = InputProcessor(assignments_base_dir)
        self.doc_processor = DocumentProcessor()
        self.grading_agent = QAGradingAgent(
            OPENAI_API_KEY, model=OPENAI_MODEL, grading_mode=grading_mode
        )
        self.output_manager = OutputManager(output_base_dir)

        # Initialize new multi-stage components
        from src.agents.answer_extraction_agent import AnswerExtractionAgent
        from src.agents.report_generator import ReportGenerator

        self.answer_extractor = AnswerExtractionAgent(
            OPENAI_API_KEY,
            model=OPENAI_MODEL,
            enable_image_processing=enable_image_processing,
        )
        self.report_generator = ReportGenerator(
            OPENAI_API_KEY,
            model=OPENAI_MODEL,
        )

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
        """Process all submissions for the assignment"""
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

        # Get all submission files
        submission_files = self.doc_processor.get_all_submissions(submissions_dir)
        logger.info(f"Found {len(submission_files)} submissions to process")

        if not submission_files:
            logger.warning("No submission files found!")
            return []

        # Process each submission
        grades = []
        for i, file_path in enumerate(submission_files, 1):
            try:
                filename = os.path.basename(file_path)
                logger.info(f"\n[{i}/{len(submission_files)}] Processing: {filename}")

                # Extract student information
                student_name = QAGradingAgent.extract_student_name(filename)
                student_id = QAGradingAgent.extract_student_id(filename)

                logger.info(f"Student: {student_name} (ID: {student_id})")

                # Check if file is empty
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    logger.warning(f"Empty file: {filename}")
                    grade = self.grading_agent.grade_empty_submission(
                        self.assignment_config,
                        student_name,
                        student_id,
                        filename,
                    )
                    grades.append(grade)
                    continue

                # ========== NEW 3-STAGE PIPELINE ==========

                # STAGE 1: Extract answers from text and images
                logger.info("Stage 1: Extracting answers...")
                extracted_answers = self.answer_extractor.extract_answers(
                    file_path, self.assignment_config
                )

                # Check if any answers were extracted
                has_content = any(
                    answer_data.get("text", "").strip()
                    for answer_data in extracted_answers.values()
                )

                if not has_content:
                    logger.warning(f"No content extracted from {filename}")
                    grade = self.grading_agent.grade_empty_submission(
                        self.assignment_config,
                        student_name,
                        student_id,
                        filename,
                    )
                    grades.append(grade)
                    continue

                # STAGE 2: Grade each question individually
                logger.info("Stage 2: Grading individual questions...")
                grade = self.grading_agent.grade_submission_with_extraction(
                    self.assignment_config,
                    student_name,
                    extracted_answers,
                    student_id,
                    filename,
                )

                if not grade:
                    logger.error(f"Failed to grade submission: {filename}")
                    continue

                # STAGE 3: Generate comprehensive report
                logger.info("Stage 3: Generating report...")
                report_data = self.report_generator.generate_report(
                    grade.questions, self.assignment_config, student_name
                )

                # Update grade with report data
                grade.overall_comment = report_data["overall_comment"]
                grade.strengths = report_data["strengths"]
                grade.areas_for_improvement = report_data["areas_for_improvement"]
                grade.requires_human_review = report_data["requires_human_review"]
                grade.review_reason = report_data["review_reason"]

                # ==========================================

                if grade:
                    grades.append(grade)
                    logger.info(
                        f"Grade: {grade.total_score}/{grade.max_score} "
                        f"({grade.get_percentage():.1f}%)"
                    )
                    if grade.requires_human_review:
                        logger.warning(f"⚠️  Flagged for review: {grade.review_reason}")
                else:
                    logger.error(f"Failed to grade submission: {filename}")

            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}", exc_info=True)
                # Create error grade
                student_name = QAGradingAgent.extract_student_name(
                    os.path.basename(file_path)
                )
                student_id = QAGradingAgent.extract_student_id(
                    os.path.basename(file_path)
                )
                error_grade = self.grading_agent._create_error_grade(
                    self.assignment_config,
                    student_name,
                    student_id,
                    os.path.basename(file_path),
                )
                grades.append(error_grade)

        logger.info("\n" + "=" * 80)
        logger.info(f"Completed grading {len(grades)} submissions")
        logger.info("=" * 80)

        return grades

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
        )
        success = workflow.run()
        return 0 if success else 1

    # No command specified
    parser.print_help()
    print("\nTip: Use --list to see available assignments")
    return 1


if __name__ == "__main__":
    sys.exit(main())
