#!/usr/bin/env python3
"""
Test script to verify the grading system setup
"""

import os
import sys
from config import OPENAI_API_KEY, SUBMISSIONS_DIR, OUTPUT_CSV
from document_processor import DocumentProcessor


def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage
        import pandas as pd
        import PyPDF2
        from docx import Document

        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_config():
    """Test configuration"""
    print("Testing configuration...")
    if not OPENAI_API_KEY:
        print("✗ OPENAI_API_KEY not set")
        return False
    else:
        print("✓ OPENAI_API_KEY is set")

    if not os.path.exists(SUBMISSIONS_DIR):
        print(f"✗ Submissions directory '{SUBMISSIONS_DIR}' not found")
        return False
    else:
        print(f"✓ Submissions directory found")

    return True


def test_document_processor():
    """Test document processor"""
    print("Testing document processor...")
    try:
        processor = DocumentProcessor()
        submissions = processor.get_all_submissions(SUBMISSIONS_DIR)
        print(f"✓ Found {len(submissions)} submissions")

        if submissions:
            # Test text extraction on first file
            test_file = submissions[0]
            print(f"Testing text extraction on: {os.path.basename(test_file)}")
            text = processor.extract_text_from_file(test_file)
            if text:
                print(f"✓ Text extraction successful ({len(text)} characters)")
            else:
                print("⚠ Text extraction returned empty result")

        return True
    except Exception as e:
        print(f"✗ Document processor error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("GRADING SYSTEM SETUP TEST")
    print("=" * 50)

    tests = [test_imports, test_config, test_document_processor]

    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"TESTS PASSED: {passed}/{len(tests)}")
    print("=" * 50)

    if passed == len(tests):
        print("✓ All tests passed! System is ready to use.")
        print("\nTo run the grading workflow:")
        print("python main.py")
    else:
        print(
            "✗ Some tests failed. Please fix the issues before running the grading workflow."
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
