# Example Code Assignment

This is an example configuration for a code-based assignment demonstrating:

- Multiple programming questions
- Code evaluation rubrics
- Optional test cases
- Multi-file submission support

## Structure

- `config.json` - Assignment configuration with test cases
- This README

## Usage

1. Place student submissions in: `submissions/example_code_assignment/`

Student submissions can be:

- Single file: `studentname_12345_solution.py`
- Multiple files: `studentname_12345_part1.py`, `studentname_12345_part2.py`

2. Run grading:

```bash
cd backend
python main.py --assignment example_code_assignment
```

## Features Demonstrated

1. **Code Questions**: Two programming problems
2. **Rubrics**: Specific criteria for code evaluation
3. **Test Cases**: Optional automated testing (disabled by default for security)
4. **Multi-File**: System automatically groups files by student
5. **Late Detection**: Filename parsing detects LATE marker

## Filename Format

Expected format: `name_LATE_studentID_submissionID_description`

Examples:

- `lawfordjack_LATE_101445_22007124_HW8.py`
- `nielsenconnor_192061_21988980_solution.py`
- `smithjohn_12345_factorial.py`

## Test Cases

Test cases are configured in `config.json` but execution is **disabled by default** for security. To enable:

```bash
python main.py --assignment example_code_assignment --enable-code-execution
```

**Warning**: Only enable test execution with trusted code. The system includes sandboxing but additional security measures are recommended.

## Output

Results include:

- Code syntax validation
- Structure analysis (functions, classes)
- AI evaluation (correctness, style, efficiency)
- Test results (if execution enabled)
- Standard grading report

View results:

```bash
cat output/example_code_assignment/grading_results_latest.csv
```
