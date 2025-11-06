#!/usr/bin/env python3
"""
Test script to validate the Grade Lens system structure and imports
Run this with: python test_system.py
"""

import os
import sys
import json

def test_directory_structure():
    """Test that all required directories exist"""
    print("Testing directory structure...")
    
    required_dirs = [
        "src",
        "src/agents",
        "src/models",
        "src/processors",
        "src/utils",
        "assignments",
        "assignments/cs361_hw5",
        "assignments/example_assignment",
        "submissions",
        "submissions/cs361_hw5",
        "output",
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} - MISSING")
            return False
    
    return True

def test_source_files():
    """Test that all source files exist"""
    print("\nTesting source files...")
    
    required_files = [
        "src/__init__.py",
        "src/models/__init__.py",
        "src/models/assignment_config.py",
        "src/models/grading_result.py",
        "src/agents/__init__.py",
        "src/agents/qa_grading_agent.py",
        "src/processors/__init__.py",
        "src/processors/document_processor.py",
        "src/processors/input_processor.py",
        "src/utils/__init__.py",
        "src/utils/output_manager.py",
        "src/utils/prompt_builder.py",
        "config.py",
        "main.py",
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - MISSING")
            return False
    
    return True

def test_assignment_configs():
    """Test that assignment configurations are valid JSON"""
    print("\nTesting assignment configurations...")
    
    assignments = ["cs361_hw5", "example_assignment"]
    
    for assignment_id in assignments:
        config_path = f"assignments/{assignment_id}/config.json"
        
        if not os.path.exists(config_path):
            print(f"  ✗ {config_path} - MISSING")
            return False
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = ["assignment_id", "assignment_name", "questions"]
            for field in required_fields:
                if field not in config:
                    print(f"  ✗ {config_path} - Missing field: {field}")
                    return False
            
            # Validate questions
            if len(config["questions"]) == 0:
                print(f"  ✗ {config_path} - No questions defined")
                return False
            
            print(f"  ✓ {config_path} ({len(config['questions'])} questions)")
            
        except json.JSONDecodeError as e:
            print(f"  ✗ {config_path} - Invalid JSON: {e}")
            return False
    
    return True

def test_submissions():
    """Test that submissions directory has files"""
    print("\nTesting submissions...")
    
    submissions_dir = "submissions/cs361_hw5"
    
    if not os.path.exists(submissions_dir):
        print(f"  ✗ {submissions_dir} - MISSING")
        return False
    
    files = [f for f in os.listdir(submissions_dir) 
             if f.endswith(('.pdf', '.docx', '.txt'))]
    
    print(f"  ✓ Found {len(files)} submission files in {submissions_dir}")
    
    if len(files) > 0:
        print(f"    Sample: {files[0]}")
    
    return True

def test_imports():
    """Test that modules can be imported"""
    print("\nTesting module imports...")
    
    # Add src to path
    sys.path.insert(0, 'src')
    
    try:
        # Test data models
        from src.models.assignment_config import AssignmentConfig, QuestionConfig, RubricConfig
        print("  ✓ Models imported successfully")
        
        from src.models.grading_result import AssignmentGrade, QuestionGrade
        print("  ✓ Grading result models imported successfully")
        
        # Test processors
        from src.processors.document_processor import DocumentProcessor
        print("  ✓ Document processor imported successfully")
        
        from src.processors.input_processor import InputProcessor
        print("  ✓ Input processor imported successfully")
        
        # Test utilities
        from src.utils.prompt_builder import PromptBuilder
        print("  ✓ Prompt builder imported successfully")
        
        from src.utils.output_manager import OutputManager
        print("  ✓ Output manager imported successfully")
        
        # Test agents (may fail if LangChain not installed)
        try:
            from src.agents.qa_grading_agent import QAGradingAgent
            print("  ✓ QA grading agent imported successfully")
        except ImportError as e:
            print(f"  ⚠ QA grading agent import failed (expected if LangChain not installed): {e}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False

def test_assignment_loading():
    """Test loading assignment configuration"""
    print("\nTesting assignment loading...")
    
    sys.path.insert(0, 'src')
    
    try:
        from src.processors.input_processor import InputProcessor
        
        processor = InputProcessor("assignments")
        
        # List assignments
        assignments = processor.list_available_assignments()
        print(f"  ✓ Found {len(assignments)} assignments: {assignments}")
        
        # Load cs361_hw5
        config = processor.load_assignment("cs361_hw5")
        if config:
            print(f"  ✓ Loaded cs361_hw5:")
            print(f"    - Name: {config.assignment_name}")
            print(f"    - Questions: {len(config.questions)}")
            print(f"    - Total Points: {config.total_points}")
        else:
            print(f"  ✗ Failed to load cs361_hw5")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Assignment loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Grade Lens System Validation")
    print("=" * 60)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Source Files", test_source_files),
        ("Assignment Configs", test_assignment_configs),
        ("Submissions", test_submissions),
        ("Module Imports", test_imports),
        ("Assignment Loading", test_assignment_loading),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} - EXCEPTION: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Ensure OpenAI API key is set in .env file")
        print("  2. Run: python main.py --list")
        print("  3. Run: python main.py --assignment cs361_hw5")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

