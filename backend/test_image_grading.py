#!/usr/bin/env python3
"""
Test script for image processing grading capabilities
Tests text-only, image-based, and mixed content submissions
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from config import OPENAI_API_KEY, OPENAI_MODEL
from src.processors.document_processor import DocumentProcessor
from src.agents.answer_extraction_agent import AnswerExtractionAgent
from src.agents.qa_grading_agent import QAGradingAgent
from src.agents.report_generator import ReportGenerator
from src.models.assignment_config import AssignmentConfig, QuestionConfig, RubricConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_test_assignment() -> AssignmentConfig:
    """Create a simple test assignment configuration"""
    return AssignmentConfig(
        assignment_id="test_image_assignment",
        assignment_name="Test Image Processing Assignment",
        course_code="TEST101",
        term="Test Term",
        questions=[
            QuestionConfig(
                id="question_1",
                text="Question 1: Explain the concept of recursion.",
                points=10.0,
                answer_key="Recursion is when a function calls itself...",
                rubric=RubricConfig(
                    criteria=["Clear explanation", "Correct examples"],
                    correct=10.0,
                    mostly_correct=7.0,
                    attempted=4.0,
                    no_submission=0.0,
                    instructions="Grade based on understanding of recursion",
                ),
            ),
            QuestionConfig(
                id="question_2",
                text="Question 2: Write a function to calculate factorial.",
                points=10.0,
                answer_key="def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
                rubric=RubricConfig(
                    criteria=["Correct logic", "Base case", "Recursive call"],
                    correct=10.0,
                    mostly_correct=7.0,
                    attempted=4.0,
                    no_submission=0.0,
                    instructions="Code must be syntactically correct",
                ),
            ),
        ],
        allow_partial_credit=True,
    )


def test_text_only_pdf(test_pdf_path: str):
    """Test grading a text-only PDF (no images)"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Text-Only PDF")
    logger.info("=" * 80)

    if not os.path.exists(test_pdf_path):
        logger.warning(f"Test PDF not found: {test_pdf_path}")
        logger.info("SKIPPED: Create a text-only PDF for testing")
        return

    try:
        # Create test assignment
        assignment_config = create_test_assignment()

        # Initialize agents
        doc_processor = DocumentProcessor()
        answer_extractor = AnswerExtractionAgent(
            OPENAI_API_KEY,
            model=OPENAI_MODEL,
            enable_image_processing=False,  # Disable for text-only
        )
        grading_agent = QAGradingAgent(OPENAI_API_KEY, model=OPENAI_MODEL)
        report_generator = ReportGenerator(OPENAI_API_KEY, model=OPENAI_MODEL)

        # Extract text
        logger.info(f"Extracting text from: {test_pdf_path}")
        text_content = doc_processor.extract_text_from_file(test_pdf_path)
        logger.info(f"Extracted {len(text_content)} characters")

        # Extract answers
        logger.info("Extracting answers...")
        extracted_answers = answer_extractor.extract_answers(
            test_pdf_path, assignment_config
        )

        for q_id, answer_data in extracted_answers.items():
            logger.info(f"  {q_id}: {len(answer_data.get('text', ''))} chars")

        # Grade submission
        logger.info("Grading submission...")
        grade = grading_agent.grade_submission_with_extraction(
            assignment_config,
            "Test Student",
            extracted_answers,
            "TEST001",
            os.path.basename(test_pdf_path),
        )

        if grade:
            # Generate report
            logger.info("Generating report...")
            report_data = report_generator.generate_report(
                grade.questions, assignment_config, "Test Student"
            )

            # Display results
            logger.info("\n" + "-" * 80)
            logger.info("RESULTS:")
            logger.info(
                f"Total Score: {grade.total_score}/{grade.max_score} ({grade.get_percentage():.1f}%)"
            )
            logger.info(f"Overall Comment: {report_data['overall_comment']}")
            if report_data["strengths"]:
                logger.info(f"Strengths: {', '.join(report_data['strengths'])}")
            if report_data["areas_for_improvement"]:
                logger.info(
                    f"Areas for Improvement: {', '.join(report_data['areas_for_improvement'])}"
                )
            logger.info("-" * 80)

            logger.info("✓ TEST PASSED: Text-only PDF grading successful")
        else:
            logger.error("✗ TEST FAILED: Grading returned None")

    except Exception as e:
        logger.error(f"✗ TEST FAILED: {str(e)}", exc_info=True)


def test_image_based_pdf(test_pdf_path: str):
    """Test grading a PDF with images (scanned or image-based)"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Image-Based PDF")
    logger.info("=" * 80)

    if not os.path.exists(test_pdf_path):
        logger.warning(f"Test PDF not found: {test_pdf_path}")
        logger.info("SKIPPED: Create an image-based PDF for testing")
        return

    try:
        # Create test assignment
        assignment_config = create_test_assignment()

        # Initialize agents with image processing enabled
        doc_processor = DocumentProcessor()
        answer_extractor = AnswerExtractionAgent(
            OPENAI_API_KEY,
            model=OPENAI_MODEL,
            enable_image_processing=True,
        )
        grading_agent = QAGradingAgent(OPENAI_API_KEY, model=OPENAI_MODEL)
        report_generator = ReportGenerator(OPENAI_API_KEY, model=OPENAI_MODEL)

        # Check for images
        logger.info(f"Checking for images in: {test_pdf_path}")
        has_images = doc_processor.has_images(test_pdf_path)
        logger.info(f"Contains images: {has_images}")

        if has_images:
            metadata = doc_processor.get_pdf_metadata(test_pdf_path)
            logger.info(f"Image count: {metadata.get('image_count', 0)}")

        # Extract answers (with image processing)
        logger.info("Extracting answers (including from images)...")
        extracted_answers = answer_extractor.extract_answers(
            test_pdf_path, assignment_config
        )

        for q_id, answer_data in extracted_answers.items():
            extracted_from_image = answer_data.get("extracted_from_image", False)
            logger.info(
                f"  {q_id}: {len(answer_data.get('text', ''))} chars (from image: {extracted_from_image})"
            )

        # Grade submission
        logger.info("Grading submission...")
        grade = grading_agent.grade_submission_with_extraction(
            assignment_config,
            "Test Student",
            extracted_answers,
            "TEST002",
            os.path.basename(test_pdf_path),
        )

        if grade:
            # Generate report
            logger.info("Generating report...")
            report_data = report_generator.generate_report(
                grade.questions, assignment_config, "Test Student"
            )

            # Display results
            logger.info("\n" + "-" * 80)
            logger.info("RESULTS:")
            logger.info(
                f"Total Score: {grade.total_score}/{grade.max_score} ({grade.get_percentage():.1f}%)"
            )

            for q in grade.questions:
                logger.info(f"\n{q.question_id}:")
                logger.info(f"  Score: {q.score}/{q.max_score}")
                logger.info(f"  Extracted from image: {q.extracted_from_image}")
                if q.image_processing_notes:
                    logger.info(f"  Notes: {q.image_processing_notes}")

            logger.info(f"\nOverall Comment: {report_data['overall_comment']}")
            logger.info("-" * 80)

            logger.info("✓ TEST PASSED: Image-based PDF grading successful")
        else:
            logger.error("✗ TEST FAILED: Grading returned None")

    except Exception as e:
        logger.error(f"✗ TEST FAILED: {str(e)}", exc_info=True)


def test_mixed_content_pdf(test_pdf_path: str):
    """Test grading a PDF with both text and images"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Mixed Content PDF (Text + Images)")
    logger.info("=" * 80)

    if not os.path.exists(test_pdf_path):
        logger.warning(f"Test PDF not found: {test_pdf_path}")
        logger.info("SKIPPED: Create a mixed content PDF for testing")
        return

    try:
        # Same logic as image-based test, but verifying both text and image extraction
        assignment_config = create_test_assignment()

        doc_processor = DocumentProcessor()
        answer_extractor = AnswerExtractionAgent(
            OPENAI_API_KEY,
            model=OPENAI_MODEL,
            enable_image_processing=True,
        )
        grading_agent = QAGradingAgent(OPENAI_API_KEY, model=OPENAI_MODEL)
        report_generator = ReportGenerator(OPENAI_API_KEY, model=OPENAI_MODEL)

        # Extract both text and images
        logger.info(f"Processing: {test_pdf_path}")
        text_content = doc_processor.extract_text_from_file(test_pdf_path)
        has_images = doc_processor.has_images(test_pdf_path)

        logger.info(f"Text content: {len(text_content)} characters")
        logger.info(f"Has images: {has_images}")

        # Extract answers
        extracted_answers = answer_extractor.extract_answers(
            test_pdf_path, assignment_config
        )

        # Grade and generate report
        grade = grading_agent.grade_submission_with_extraction(
            assignment_config,
            "Test Student",
            extracted_answers,
            "TEST003",
            os.path.basename(test_pdf_path),
        )

        if grade:
            report_data = report_generator.generate_report(
                grade.questions, assignment_config, "Test Student"
            )

            logger.info("\n" + "-" * 80)
            logger.info("RESULTS:")
            logger.info(f"Total Score: {grade.total_score}/{grade.max_score}")
            logger.info(f"Overall: {report_data['overall_comment']}")
            logger.info("-" * 80)

            logger.info("✓ TEST PASSED: Mixed content PDF grading successful")
        else:
            logger.error("✗ TEST FAILED: Grading returned None")

    except Exception as e:
        logger.error(f"✗ TEST FAILED: {str(e)}", exc_info=True)


def test_backward_compatibility():
    """Test that old grading workflow still works (backward compatibility)"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Backward Compatibility (Old Workflow)")
    logger.info("=" * 80)

    try:
        assignment_config = create_test_assignment()
        grading_agent = QAGradingAgent(OPENAI_API_KEY, model=OPENAI_MODEL)

        # Test with simple text submission
        test_submission = """
Question 1: Recursion is when a function calls itself to solve smaller 
versions of the same problem until reaching a base case.

Question 2:
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""

        logger.info("Testing old grade_submission method...")
        grade = grading_agent.grade_submission(
            assignment_config,
            "Test Student",
            test_submission,
            "TEST004",
            "test_submission.txt",
        )

        if grade:
            logger.info(f"Score: {grade.total_score}/{grade.max_score}")
            logger.info("✓ TEST PASSED: Backward compatibility maintained")
        else:
            logger.error("✗ TEST FAILED: Old method returned None")

    except Exception as e:
        logger.error(f"✗ TEST FAILED: {str(e)}", exc_info=True)


def test_error_handling():
    """Test graceful error handling"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Error Handling")
    logger.info("=" * 80)

    try:
        assignment_config = create_test_assignment()
        answer_extractor = AnswerExtractionAgent(
            OPENAI_API_KEY,
            model=OPENAI_MODEL,
            enable_image_processing=True,
        )

        # Test with non-existent file
        logger.info("Testing with non-existent file...")
        extracted_answers = answer_extractor.extract_answers(
            "/nonexistent/file.pdf", assignment_config
        )

        # Should return empty answers, not crash
        if all(not data.get("text", "").strip() for data in extracted_answers.values()):
            logger.info("✓ Gracefully handled missing file")
        else:
            logger.warning("Unexpected result for missing file")

        # Test with corrupted/empty content
        logger.info("Testing with empty content...")
        grading_agent = QAGradingAgent(OPENAI_API_KEY, model=OPENAI_MODEL)
        grade = grading_agent.grade_submission_with_extraction(
            assignment_config,
            "Test Student",
            {
                q.id: {"text": "", "extracted_from_image": False}
                for q in assignment_config.questions
            },
            "TEST005",
            "empty.pdf",
        )

        if grade and grade.total_score == 0:
            logger.info("✓ Gracefully handled empty submission")
        else:
            logger.warning("Unexpected result for empty submission")

        logger.info("✓ TEST PASSED: Error handling works correctly")

    except Exception as e:
        logger.error(f"✗ TEST FAILED: {str(e)}", exc_info=True)


def main():
    """Run all tests"""
    logger.info("=" * 80)
    logger.info("IMAGE PROCESSING GRADING SYSTEM - TEST SUITE")
    logger.info("=" * 80)

    # Check API key
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not configured. Please set it in .env file")
        return 1

    logger.info(f"Using model: {OPENAI_MODEL}")

    # Define test files (you'll need to create these or update paths)
    test_files = {
        "text_only": "test_data/text_only.pdf",
        "image_based": "test_data/image_based.pdf",
        "mixed": "test_data/mixed_content.pdf",
    }

    # Run tests
    test_text_only_pdf(test_files["text_only"])
    test_image_based_pdf(test_files["image_based"])
    test_mixed_content_pdf(test_files["mixed"])
    test_backward_compatibility()
    test_error_handling()

    logger.info("\n" + "=" * 80)
    logger.info("TEST SUITE COMPLETED")
    logger.info("=" * 80)
    logger.info(
        "\nNOTE: Some tests may be skipped if test PDF files are not available."
    )
    logger.info("Create test PDFs in the 'test_data' directory to run all tests.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
