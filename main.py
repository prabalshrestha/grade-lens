#!/usr/bin/env python3
"""
Main workflow for grading CS361 HW5 submissions using LangChain and OpenAI
"""

import os
import logging
from typing import List
from config import OPENAI_API_KEY, SUBMISSIONS_DIR, OUTPUT_CSV, OUTPUT_DIR
from document_processor import DocumentProcessor
from grading_agent import GradingAgent
from csv_manager import CSVManager

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(OUTPUT_DIR, "grading.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class GradingWorkflow:
    """Main workflow for processing and grading submissions"""

    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.grading_agent = GradingAgent(OPENAI_API_KEY)
        self.csv_manager = CSVManager(OUTPUT_CSV)

        # Define the questions for CS361 HW5
        self.questions = [
            "question_1",  # Pumping lemma proof (15 points)
            "question_2",  # Regularity proof (15 points)
        ]

    def process_all_submissions(self):
        """Process all submissions in the directory"""
        logger.info("Starting grading workflow...")

        # Get all submission files
        submission_files = self.document_processor.get_all_submissions(SUBMISSIONS_DIR)
        logger.info(f"Found {len(submission_files)} submissions to process")

        if not submission_files:
            logger.warning("No submission files found!")
            return

        # Process each submission
        for i, file_path in enumerate(submission_files, 1):
            try:
                logger.info(
                    f"Processing {i}/{len(submission_files)}: {os.path.basename(file_path)}"
                )

                # Extract student name from filename
                filename = os.path.basename(file_path)
                student_name = self.grading_agent.extract_student_name(filename)

                # Extract text from document
                submission_text = self.document_processor.extract_text_from_file(
                    file_path
                )

                if not submission_text.strip():
                    logger.warning(f"No text extracted from {filename}")
                    # Create default grading for empty submissions
                    grading_result = self._create_empty_grading()
                    total_score = 0.0
                else:
                    # Grade the submission
                    grading_result = self.grading_agent.grade_submission(
                        student_name, submission_text, self.questions
                    )
                    total_score = self.grading_agent.calculate_total_score(
                        grading_result
                    )

                # Add to CSV manager
                self.csv_manager.add_grading_result(
                    student_name, filename, grading_result, total_score
                )

                logger.info(
                    f"Completed grading for {student_name}: {total_score} points"
                )

            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                # Add error entry to results
                student_name = self.grading_agent.extract_student_name(
                    os.path.basename(file_path)
                )
                error_grading = self._create_error_grading()
                self.csv_manager.add_grading_result(
                    student_name, os.path.basename(file_path), error_grading, 0.0
                )

        # Save results to CSV
        logger.info("Saving results to CSV...")
        self.csv_manager.save_to_csv()

        # Print summary statistics
        stats = self.csv_manager.get_summary_stats()
        self._print_summary(stats)

        logger.info("Grading workflow completed!")

    def _create_empty_grading(self) -> dict:
        """Create grading for empty submissions"""
        grading = {}
        for question in self.questions:
            grading[question] = {
                "score": 0,
                "reasoning": "No submission or empty submission",
            }
        return grading

    def _create_error_grading(self) -> dict:
        """Create grading for submissions that couldn't be processed"""
        grading = {}
        for question in self.questions:
            grading[question] = {"score": 0, "reasoning": "Error processing submission"}
        return grading

    def _print_summary(self, stats: dict):
        """Print summary statistics"""
        print("\n" + "=" * 50)
        print("GRADING SUMMARY")
        print("=" * 50)
        print(f"Total students graded: {stats.get('total_students', 0)}")
        print(f"Average score: {stats.get('average_score', 0):.2f}")
        print(f"Highest score: {stats.get('highest_score', 0):.2f}")
        print(f"Lowest score: {stats.get('lowest_score', 0):.2f}")
        print(f"Students with zero points: {stats.get('students_with_zero', 0)}")
        print(f"Students with full marks: {stats.get('students_with_full_marks', 0)}")
        print("=" * 50)


def main():
    """Main entry point"""
    try:
        # Check if API key is set
        if not OPENAI_API_KEY:
            logger.error(
                "OPENAI_API_KEY not found. Please set it in your environment or .env file"
            )
            return

        # Check if submissions directory exists
        if not os.path.exists(SUBMISSIONS_DIR):
            logger.error(f"Submissions directory '{SUBMISSIONS_DIR}' not found!")
            return

        # Create and run workflow
        workflow = GradingWorkflow()
        workflow.process_all_submissions()

    except Exception as e:
        logger.error(f"Fatal error in main workflow: {str(e)}")
        raise


if __name__ == "__main__":
    main()
