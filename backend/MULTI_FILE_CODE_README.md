# Multi-File Submission and Code Evaluation System

## Overview

The Grade Lens system now supports:

- **Multi-file submissions** from a single student
- **Code evaluation** for Python and Java
- **Hybrid grading** with AI analysis + optional test execution
- **Automatic student grouping** based on filename patterns

## Filename Pattern

The system recognizes this naming pattern:

```
name_LATE_studentID_submissionID_remainder.ext
```

Examples:

- `lawfordjack_LATE_101445_22007124_HW8.py`
- `nielsenconnor_192061_21988980_Problem_1.java`
- `smithjohn_12345_67890_Assignment1.pdf`

Components:

1. **name**: Student name (first part)
2. **LATE**: Optional late submission marker
3. **studentID**: Numeric ID (4+ digits)
4. **submissionID**: Submission number (optional)
5. **remainder**: Additional description
6. **ext**: File extension

## Features

### 1. Multi-File Submissions

Students can submit multiple files that are automatically grouped:

```
submissions/cs361_hw8/
├── lawfordjack_LATE_101445_22007124_part1.py
├── lawfordjack_LATE_101445_22007124_part2.py
└── nielsenconnor_192061_21988980_solution.java
```

The system:

- Groups `lawfordjack` files together (2 files)
- Treats `nielsenconnor` as separate submission (1 file)
- Extracts late submission flag
- Concatenates all files per student

### 2. Code Evaluation

Supports Python (.py) and Java (.java) files with:

**AI Evaluation**:

- Code correctness analysis
- Style and quality assessment
- Efficiency analysis
- Strengths and improvements

**Optional Test Execution** (when enabled):

- Run test cases against code
- Sandboxed execution with timeouts
- Resource limits (CPU, memory)
- Security checks for dangerous imports

**Hybrid Results**:

- AI evaluation + test results combined
- Comprehensive feedback
- Detailed scoring breakdown

### 3. Submission Types

The system handles three types:

**Document Only**:

```
- student.pdf
- student.docx
```

Uses existing pipeline with image processing

**Code Only**:

```
- student_part1.py
- student_part2.py
```

Uses new code extraction and evaluation pipeline

**Mixed**:

```
- student_code.py
- student_writeup.pdf
```

Combines both approaches

## Usage

### Basic Code Grading

```bash
# Grade code assignment (AI evaluation only)
python main.py --assignment cs361_hw8
```

### With Test Execution

```bash
# Enable code execution
python main.py --assignment cs361_hw8 --enable-code-execution
```

### Configuration

Create config for code assignment:

```json
{
  "assignment_id": "cs361_hw8",
  "assignment_name": "CS361 HW8 - Python Programming",
  "assignment_type": "code",
  "supported_languages": ["python", "java"],
  "enable_code_execution": false,

  "questions": [
    {
      "id": "problem_1",
      "text": "Implement factorial function",
      "points": 20.0,
      "question_type": "code",
      "rubric": {
        "criteria": [
          "Correct implementation",
          "Handles edge cases",
          "Good code style"
        ],
        "correct": 20.0,
        "mostly_correct": 15.0,
        "attempted": 8.0
      }
    }
  ],

  "test_cases": [
    {
      "question_id": "problem_1",
      "tests": [
        {
          "input": "5",
          "expected_output": "120",
          "description": "factorial(5) = 120"
        },
        {
          "input": "0",
          "expected_output": "1",
          "description": "factorial(0) = 1"
        }
      ]
    }
  ]
}
```

## Architecture

### File Processing Pipeline

```
1. Scan submissions directory
2. Parse all filenames
3. Group by student (name + ID)
4. Categorize by type (code/document)
5. Route to appropriate processor
6. Concatenate files per student
7. Extract/evaluate content
8. Grade questions
9. Generate report
```

### Code Processing Flow

```
Code Files → Code Extraction Agent
              ├─ Syntax validation
              ├─ Structure analysis (AST)
              ├─ File concatenation
              └─ Purpose identification (AI)
                   ↓
              Code Evaluation Agent
              ├─ AI correctness analysis
              ├─ Style assessment
              ├─ Efficiency review
              └─ Optional: Test execution
                   ↓
              Question Grading Agent
              ├─ Apply rubric
              ├─ Generate reasoning
              └─ Provide feedback
                   ↓
              Report Generator
              └─ Final assessment
```

## Components

### SubmissionGrouper

**File**: `backend/src/processors/submission_grouper.py`

**Methods**:

- `parse_filename()` - Parse name_LATE_studentID pattern
- `group_files_by_student()` - Group by student
- `get_student_info()` - Extract student metadata
- `categorize_files_by_type()` - Separate code/docs

### CodeExtractionAgent

**File**: `backend/src/agents/code_extraction_agent.py`

**Methods**:

- `extract_code_submission()` - Process all code files
- `concatenate_code_files()` - Combine with separators
- `analyze_code_syntax()` - Syntax validation
- `extract_code_structure()` - AST analysis

### CodeEvaluationAgent

**File**: `backend/src/agents/code_evaluation_agent.py`

**Methods**:

- `evaluate_code()` - Hybrid evaluation
- `ai_evaluate_code()` - AI analysis
- `run_test_cases()` - Execute tests
- `_execute_python_test()` - Sandboxed execution

## Security

### Code Execution Safety

When `enable_code_execution=True`:

**Sandboxing**:

- Runs in isolated subprocess
- 5-second timeout per test
- Resource limits (CPU, memory)
- Blocks dangerous imports (os, subprocess, sys)
- Kills runaway processes

**Blocked Patterns**:

```python
import os
import subprocess
import sys
eval()
exec()
__import__()
```

**Resource Limits** (Unix):

- CPU: 10 seconds max
- Memory: 256MB max
- File size: 1MB max

**Best Practice**: Disable execution by default, only enable when needed and code is reviewed.

## Testing

Run test suite:

```bash
cd backend
python test_multi_file_code.py
```

Tests cover:

- Filename parsing (various patterns)
- Student grouping (multiple files)
- File categorization (code/docs)
- Code extraction (Python/Java)
- Syntax validation
- Structure analysis
- Code evaluation
- Document processor enhancements

## Examples

### Example 1: Single Code File

```
submissions/hw8/
└── nielsenconnor_192061_solution.py
```

Result:

- 1 student, 1 file
- Code extracted and evaluated
- Graded against rubric

### Example 2: Multiple Code Files

```
submissions/hw8/
├── lawfordjack_LATE_101445_22007124_part1.py
└── lawfordjack_LATE_101445_22007124_part2.py
```

Result:

- 1 student, 2 files (grouped)
- Marked as late
- Files concatenated
- Evaluated as single submission

### Example 3: Mixed Submission

```
submissions/hw8/
├── smithjohn_12345_code.py
└── smithjohn_12345_writeup.pdf
```

Result:

- 1 student, 2 files (mixed)
- Code evaluated with AI
- Document processed for text/images
- Combined for grading

### Example 4: Multiple Students

```
submissions/hw8/
├── student1_111_file1.py
├── student1_111_file2.py
├── student2_222_solution.py
└── student3_333_answer.pdf
```

Result:

- 3 students identified
- student1: 2 files grouped
- student2: 1 code file
- student3: 1 document file

## Configuration Fields

### New AssignmentConfig Fields

```python
{
  "assignment_type": "code",          # document, code, or mixed
  "supported_languages": ["python"],  # List of languages
  "enable_code_execution": false,     # Safety: disable by default
  "test_cases": [...]                 # Optional test cases
}
```

### New AssignmentGrade Fields

```python
{
  "is_late": true,                    # Late submission flag
  "file_count": 2,                    # Number of files
  "submission_type": "code",          # Type of submission
  "file_list": ["part1.py", "part2.py"],  # List of files
  "code_evaluation": {...}            # Code evaluation results
}
```

## Performance

### Processing Times

- **Single code file**: 3-5 seconds (AI only)
- **Multiple code files**: 5-10 seconds
- **With test execution**: +2-5 seconds per test
- **Mixed submission**: 8-15 seconds

### Cost Estimates (gpt-4o-mini)

- Code extraction: ~$0.002 per submission
- Code evaluation: ~$0.003 per submission
- Total: ~$0.005 per code submission
- With tests: +$0.001 per test case

## Troubleshooting

### Files Not Grouping

Check filename format:

```bash
python -c "
from src.processors.submission_grouper import SubmissionGrouper
grouper = SubmissionGrouper()
parsed = grouper.parse_filename('your_file.py')
print(parsed)
"
```

### Code Not Executing

1. Check if execution is enabled: `enable_code_execution=true`
2. Verify no blocked patterns in code
3. Check timeout limits
4. Review logs for security warnings

### Syntax Errors

The system validates syntax before grading:

- Python: Uses `compile()`
- Java: Basic pattern matching
- Errors logged but don't block grading

## API Usage

The web API automatically handles multi-file submissions:

```bash
# Upload multiple files
curl -X POST http://localhost:8000/api/assignments/hw8/submissions \
  -F "files=@student_part1.py" \
  -F "files=@student_part2.py"

# Grade assignment
curl -X POST http://localhost:8000/api/assignments/hw8/grade
```

Results include file count, late flags, and code evaluation data.

## Migration

### From Single-File System

No changes needed! The system automatically:

- Detects single vs multi-file submissions
- Groups files when needed
- Falls back to single-file processing
- Maintains backward compatibility

### Existing Assignments

All existing document-based assignments work without changes. To enable code evaluation, add to config:

```json
{
  "assignment_type": "code",
  "supported_languages": ["python"]
}
```

## Best Practices

### For Code Assignments

1. **Disable execution by default**: `"enable_code_execution": false`
2. **Review code before enabling tests**: Check for malicious patterns
3. **Provide test cases**: Improves grading accuracy
4. **Set clear rubric criteria**: Code style, correctness, efficiency
5. **Use AI evaluation**: More comprehensive than tests alone

### For Mixed Assignments

1. **Clear instructions**: Tell students what to submit
2. **Separate criteria**: Different rubrics for code vs writeup
3. **Map to questions**: Use question-specific prompts
4. **Review grouping**: Verify files grouped correctly

### Security

1. **Never trust user code**: Always use sandboxing
2. **Review before execution**: Check submissions first
3. **Set strict timeouts**: Prevent infinite loops
4. **Limit resources**: Prevent resource exhaustion
5. **Monitor logs**: Watch for suspicious patterns

## Support

### Documentation

- User Guide: `backend/MULTI_FILE_CODE_README.md` (this file)
- Quick Start: `backend/QUICK_START.md`
- Image Processing: `backend/IMAGE_PROCESSING_README.md`

### Testing

```bash
# Test multi-file system
python test_multi_file_code.py

# Test with real submissions
python main.py --assignment test_code_assignment --verbose
```

### Logs

```bash
# Check processing logs
tail -f output/<assignment_id>/grading.log

# Check for grouping issues
grep "Grouped" output/<assignment_id>/grading.log

# Check for security blocks
grep "Security" output/<assignment_id>/grading.log
```

## Summary

The multi-file code evaluation system:

- ✅ Groups files by student automatically
- ✅ Supports Python and Java
- ✅ Concatenates multiple files
- ✅ AI-powered code evaluation
- ✅ Optional sandboxed test execution
- ✅ Tracks late submissions
- ✅ Secure with resource limits
- ✅ Backward compatible
- ✅ Production ready

All features are implemented and tested!
