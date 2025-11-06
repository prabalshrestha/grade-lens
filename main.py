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

from config import OPENAI_API_KEY, OPENAI_MODEL, SUBMISSIONS_BASE_DIR, OUTPUT_BASE_DIR, ASSIGNMENTS_BASE_DIR
from src.processors.document_processor import DocumentProcessor
from src.processors.input_processor import InputProcessor
from src.agents.qa_grading_agent import QAGradingAgent
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
    ):
        self.assignment_id = assignment_id
        self.submissions_base_dir = submissions_base_dir
        self.output_base_dir = output_base_dir

        # Initialize components
        self.input_processor = InputProcessor(assignments_base_dir)
        self.doc_processor = DocumentProcessor()
        self.grading_agent = QAGradingAgent(OPENAI_API_KEY, model=OPENAI_MODEL)
        self.output_manager = OutputManager(output_base_dir)

        # Load assignment configuration
        self.assignment_config: Optional[AssignmentConfig] = None

    def load_assignment_config(self) -> bool:
        """Load and validate assignment configuration"""
        logger.info(f"Loading assignment configuration: {self.assignment_id}")

        self.assignment_config = self.input_processor.load_assignment(self.assignment_id)

        if not self.assignment_config:
            logger.error(f"Failed to load assignment: {self.assignment_id}")
            return False

        logger.info(f"Assignment loaded: {self.assignment_config.assignment_name}")
        logger.info(f"Total questions: {len(self.assignment_config.questions)}")
        logger.info(f"Total points: {self.assignment_config.total_points}")

        return True

    def get_submissions_directory(self) -> str:
        """Get the submissions directory for this assignment"""
        return os.path.join(self.submissions_base_dir, self.assignment_id)

    def setup_logging(self):
        """Setup assignment-specific logging"""
        # Create output directory
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
        logger.info(f"Starting grading workflow for: {self.assignment_config.assignment_name}")
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

                # Extract text from document
                submission_text = self.doc_processor.extract_text_from_file(file_path)

                if not submission_text.strip():
                    logger.warning(f"No text extracted from {filename}")
                    # Create grade for empty submission
                    grade = self.grading_agent.grade_empty_submission(
                        self.assignment_config,
                        student_name,
                        student_id,
                        filename,
                    )
                else:
                    # Grade the submission
                    grade = self.grading_agent.grade_submission(
                        self.assignment_config,
                        student_name,
                        submission_text,
                        student_id,
                        filename,
                    )

                if grade:
                    grades.append(grade)
                    logger.info(
                        f"Grade: {grade.total_score}/{grade.max_score} "
                        f"({grade.get_percentage():.1f}%)"
                    )
                else:
                    logger.error(f"Failed to grade submission: {filename}")

            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}", exc_info=True)
                # Create error grade
                student_name = QAGradingAgent.extract_student_name(os.path.basename(file_path))
                student_id = QAGradingAgent.extract_student_id(os.path.basename(file_path))
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
            saved_files = self.output_manager.save_results(
                self.assignment_id,
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
        print(f"  2. Add student submissions to: {os.path.join(SUBMISSIONS_BASE_DIR, assignment_id)}/")
        print(f"  3. Run: python main.py --assignment {assignment_id}")
    else:
        print(f"\n✗ Failed to create assignment template")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Grade Lens - AI-Powered Assignment Grading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available assignments
  python main.py --list

  # Grade a specific assignment
  python main.py --assignment cs361_hw5

  # Create a new assignment template
  python main.py --create my_assignment --questions 3
        """,
    )

    parser.add_argument(
        "--assignment",
        "-a",
        type=str,
        help="Assignment ID to grade",
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

    # Handle grading
    if args.assignment:
        workflow = GradingWorkflow(args.assignment)
        success = workflow.run()
        return 0 if success else 1

    # No command specified
    parser.print_help()
    print("\nTip: Use --list to see available assignments")
    return 1


if __name__ == "__main__":
    sys.exit(main())
