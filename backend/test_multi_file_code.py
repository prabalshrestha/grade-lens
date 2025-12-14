#!/usr/bin/env python3
"""
Test script for multi-file submission and code evaluation
Tests student grouping, code extraction, and hybrid evaluation
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from config import OPENAI_API_KEY, OPENAI_MODEL
from src.processors.submission_grouper import SubmissionGrouper
from src.processors.document_processor import DocumentProcessor
from src.agents.code_extraction_agent import CodeExtractionAgent
from src.agents.code_evaluation_agent import CodeEvaluationAgent
from src.models.assignment_config import AssignmentConfig, QuestionConfig, RubricConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_filename_parsing():
    """Test parsing of various filename patterns"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Filename Parsing")
    logger.info("=" * 80)

    grouper = SubmissionGrouper()

    test_cases = [
        "lawfordjack_LATE_101445_22007124_HW8.py",
        "nielsenconnor_192061_21988980_Problem_1.java",
        "smithjohn_12345_67890_Assignment1.pdf",
        "doejane_123456_solution.py",
        "simple_file.txt",
    ]

    for filename in test_cases:
        parsed = grouper.parse_filename(filename)
        logger.info(f"\nFilename: {filename}")
        logger.info(f"  Student: {parsed['student_name']}")
        logger.info(f"  ID: {parsed['student_id']}")
        logger.info(f"  Late: {parsed['is_late']}")
        logger.info(f"  Extension: {parsed['extension']}")

    logger.info("\n✓ TEST PASSED: Filename parsing completed")


def test_student_grouping():
    """Test grouping multiple files by student"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Student Grouping")
    logger.info("=" * 80)

    grouper = SubmissionGrouper()

    # Simulate files from multiple students
    test_files = [
        "/path/lawfordjack_LATE_101445_22007124_HW8_part1.py",
        "/path/lawfordjack_LATE_101445_22007124_HW8_part2.py",
        "/path/nielsenconnor_192061_21988980_Problem_1.java",
        "/path/nielsenconnor_192061_21988980_Problem_2.java",
        "/path/nielsenconnor_192061_21988980_readme.txt",
        "/path/smithjohn_12345_67890_solution.py",
    ]

    grouped = grouper.group_files_by_student(test_files)

    logger.info(f"\nGrouped {len(test_files)} files into {len(grouped)} students")
    for student_key, files in grouped.items():
        logger.info(f"\n{student_key}:")
        for f in files:
            logger.info(f"  - {os.path.basename(f)}")

    # Verify expected grouping
    assert len(grouped) == 3, f"Expected 3 groups, got {len(grouped)}"
    assert len(grouped["lawfordjack_101445"]) == 2, "Expected 2 files for lawfordjack"
    assert (
        len(grouped["nielsenconnor_192061"]) == 3
    ), "Expected 3 files for nielsenconnor"
    assert len(grouped["smithjohn_12345"]) == 1, "Expected 1 file for smithjohn"

    logger.info("\n✓ TEST PASSED: Student grouping works correctly")


def test_file_categorization():
    """Test categorizing files by type"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: File Categorization")
    logger.info("=" * 80)

    grouper = SubmissionGrouper()

    test_files = [
        "/path/solution.py",
        "/path/helper.java",
        "/path/readme.pdf",
        "/path/notes.txt",
        "/path/diagram.png",
    ]

    categorized = grouper.categorize_files_by_type(test_files)

    logger.info(f"\nCode files: {len(categorized['code'])}")
    for f in categorized["code"]:
        logger.info(f"  - {os.path.basename(f)}")

    logger.info(f"\nDocument files: {len(categorized['document'])}")
    for f in categorized["document"]:
        logger.info(f"  - {os.path.basename(f)}")

    logger.info(f"\nOther files: {len(categorized['other'])}")
    for f in categorized["other"]:
        logger.info(f"  - {os.path.basename(f)}")

    assert len(categorized["code"]) == 2, "Expected 2 code files"
    assert len(categorized["document"]) == 2, "Expected 2 document files"
    assert len(categorized["other"]) == 1, "Expected 1 other file"

    logger.info("\n✓ TEST PASSED: File categorization works correctly")


def test_code_extraction():
    """Test extracting Python and Java code"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Code Extraction")
    logger.info("=" * 80)

    # Create a simple test assignment
    assignment_config = AssignmentConfig(
        assignment_id="test_code",
        assignment_name="Test Code Assignment",
        assignment_type="code",
        questions=[
            QuestionConfig(
                id="question_1",
                text="Implement factorial",
                points=10.0,
            )
        ],
    )

    # Create temporary Python file
    test_code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

# Test
print(factorial(5))
"""

    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        extractor = CodeExtractionAgent(OPENAI_API_KEY, model=OPENAI_MODEL)

        result = extractor.extract_code_submission([temp_file], assignment_config)

        logger.info(f"\nExtracted {result['file_count']} file(s)")
        logger.info(f"Languages: {result['languages']}")
        logger.info(f"Total lines: {result['total_lines']}")
        logger.info(f"Analysis: {result['analysis'][:200]}...")

        assert result["file_count"] == 1
        assert "python" in result["languages"]
        assert result["total_lines"] > 0

        logger.info("\n✓ TEST PASSED: Code extraction works correctly")

    finally:
        os.unlink(temp_file)


def test_code_syntax_validation():
    """Test syntax validation for code"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Code Syntax Validation")
    logger.info("=" * 80)

    extractor = CodeExtractionAgent(OPENAI_API_KEY, model=OPENAI_MODEL)

    # Valid Python code
    valid_code = "def hello():\n    print('Hello')"
    result = extractor.analyze_code_syntax(valid_code, "python")
    logger.info(f"Valid Python: {result['valid']} (errors: {result['errors']})")
    assert result["valid"] == True

    # Invalid Python code
    invalid_code = "def hello(\n    print 'Hello'"
    result = extractor.analyze_code_syntax(invalid_code, "python")
    logger.info(f"Invalid Python: {result['valid']} (errors: {len(result['errors'])})")
    assert result["valid"] == False

    logger.info("\n✓ TEST PASSED: Syntax validation works correctly")


def test_code_structure_extraction():
    """Test extracting code structure (functions, classes)"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 6: Code Structure Extraction")
    logger.info("=" * 80)

    extractor = CodeExtractionAgent(OPENAI_API_KEY, model=OPENAI_MODEL)

    test_code = """
import math

class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def main():
    calc = Calculator()
    print(calc.add(2, 3))
"""

    structure = extractor.extract_code_structure(test_code, "python")

    logger.info(f"\nFunctions found: {structure['functions']}")
    logger.info(f"Classes found: {structure['classes']}")
    logger.info(f"Imports found: {structure['imports']}")
    logger.info(f"Main found: {structure['main_found']}")

    assert "Calculator" in structure["classes"]
    assert "factorial" in structure["functions"]
    assert "main" in structure["functions"]
    assert "math" in structure["imports"]

    logger.info("\n✓ TEST PASSED: Structure extraction works correctly")


def test_code_evaluation():
    """Test hybrid code evaluation (AI only, no execution for safety)"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 7: Code Evaluation")
    logger.info("=" * 80)

    # Create test assignment
    assignment_config = AssignmentConfig(
        assignment_id="test_code_eval",
        assignment_name="Test Code Evaluation",
        assignment_type="code",
        questions=[
            QuestionConfig(
                id="question_1",
                text="Write a function to calculate factorial",
                points=10.0,
                rubric=RubricConfig(
                    criteria=[
                        "Correct implementation",
                        "Handles base case",
                        "Good code style",
                    ],
                    correct=10.0,
                    mostly_correct=7.0,
                    attempted=4.0,
                ),
            )
        ],
    )

    # Sample code
    code_submission = {
        "files": [
            {
                "filename": "factorial.py",
                "content": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
                "language": "python",
                "syntax_valid": True,
            }
        ],
        "combined_code": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
        "languages": ["python"],
        "file_count": 1,
    }

    evaluator = CodeEvaluationAgent(
        OPENAI_API_KEY,
        model=OPENAI_MODEL,
        enable_execution=False,  # Disable for testing
    )

    result = evaluator.evaluate_code(
        code_submission, assignment_config, test_cases=None
    )

    logger.info(f"\nEvaluation completed")
    logger.info(f"AI Evaluation: {result.get('ai_evaluation', {})}")
    logger.info(f"Overall Assessment: {result.get('overall_assessment', '')[:200]}...")

    assert "ai_evaluation" in result

    logger.info("\n✓ TEST PASSED: Code evaluation works correctly")


def test_document_processor_code_support():
    """Test DocumentProcessor with code files"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 8: DocumentProcessor Code Support")
    logger.info("=" * 80)

    processor = DocumentProcessor()

    # Create test files
    import tempfile

    # Python file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def test():\n    pass")
        py_file = f.name

    # Java file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
        f.write("public class Test {\n    public static void main(String[] args) {}\n}")
        java_file = f.name

    try:
        # Test is_code_file
        assert processor.is_code_file(py_file) == True
        assert processor.is_code_file(java_file) == True
        assert processor.is_code_file("test.pdf") == False

        logger.info("✓ is_code_file() works correctly")

        # Test extraction
        py_text = processor.extract_text_from_file(py_file)
        java_text = processor.extract_text_from_file(java_file)

        assert "def test():" in py_text
        assert "public class Test" in java_text

        logger.info("✓ Code file extraction works correctly")

        logger.info("\n✓ TEST PASSED: DocumentProcessor code support works")

    finally:
        os.unlink(py_file)
        os.unlink(java_file)


def main():
    """Run all tests"""
    logger.info("=" * 80)
    logger.info("MULTI-FILE CODE EVALUATION - TEST SUITE")
    logger.info("=" * 80)

    # Check API key
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not configured. Please set it in .env file")
        logger.info("Some tests will be skipped")

    logger.info(f"Using model: {OPENAI_MODEL}")

    try:
        # Run tests
        test_filename_parsing()
        test_student_grouping()
        test_file_categorization()
        test_document_processor_code_support()

        # Tests requiring API key
        if OPENAI_API_KEY:
            test_code_extraction()
            test_code_syntax_validation()
            test_code_structure_extraction()
            test_code_evaluation()
        else:
            logger.info("\nSkipping API-dependent tests (no API key)")

        logger.info("\n" + "=" * 80)
        logger.info("TEST SUITE COMPLETED")
        logger.info("=" * 80)
        logger.info("\n✓ All tests passed!")

        return 0

    except AssertionError as e:
        logger.error(f"\n✗ TEST FAILED: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"\n✗ UNEXPECTED ERROR: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
