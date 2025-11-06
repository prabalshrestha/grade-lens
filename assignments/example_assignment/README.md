# Example Assignment Template

This is a template for creating new assignments in the Grade Lens system.

## How to Use This Template

### 1. Create a New Assignment

```bash
# Option 1: Copy this template
cp -r assignments/example_assignment assignments/my_new_assignment

# Option 2: Use the CLI command
python main.py --create my_new_assignment --questions 3
```

### 2. Edit `config.json`

The configuration file defines your assignment. Key fields:

#### Assignment Metadata
```json
{
  "assignment_id": "unique_identifier",
  "assignment_name": "Human-readable name",
  "course_code": "CS XXX",
  "term": "Fall 2025"
}
```

#### Questions
Each question should have:
- `id`: Unique identifier (e.g., "question_1")
- `text`: The question prompt
- `points`: Maximum points for this question
- `answer_key`: (Optional) Model answer for reference
- `question_type`: Type of question (essay, short_answer, proof, etc.)
- `rubric`: (Optional) Question-specific rubric

Example question:
```json
{
  "id": "question_1",
  "text": "What is the time complexity of merge sort?",
  "points": 10.0,
  "answer_key": "O(n log n) in all cases...",
  "question_type": "short_answer",
  "rubric": {
    "no_submission": 0.0,
    "attempted": 5.0,
    "mostly_correct": 8.0,
    "correct": 10.0,
    "criteria": ["correct_complexity", "proper_explanation"]
  }
}
```

#### General Rubric
Applies to all questions unless overridden:
```json
{
  "general_rubric": {
    "no_submission": 0.0,
    "attempted": null,
    "mostly_correct": null,
    "correct": null,
    "instructions": "Grade based on correctness and completeness",
    "criteria": ["correctness", "completeness", "clarity"]
  }
}
```

### 3. Add Student Submissions

Place student submissions in: `submissions/{assignment_id}/`

Supported formats: PDF, DOCX, TXT

### 4. Run Grading

```bash
python main.py --assignment my_new_assignment
```

### 5. View Results

Results are saved in: `output/{assignment_id}/`

Files generated:
- `grading_results_TIMESTAMP.csv` - Spreadsheet format
- `grading_results_detailed_TIMESTAMP.json` - Complete data
- `grading_summary_TIMESTAMP.json` - Statistics
- `grading.log` - Processing log

## Advanced Configuration

### Answer Keys

You can provide answer keys in three ways:

1. **Inline in config.json:**
```json
"answer_key": "The answer is..."
```

2. **Reference a file:**
```json
"answer_key_file": "answer_key.pdf"
```

3. **Per-question files:**
```json
"questions": [
  {
    "id": "q1",
    "answer_key_file": "q1_answer.pdf"
  }
]
```

### Rubric Options

#### Numeric Scoring
```json
"rubric": {
  "no_submission": 0.0,
  "attempted": 5.0,
  "mostly_correct": 8.0,
  "correct": 10.0
}
```

#### Custom Scoring Rules
```json
"rubric": {
  "custom_scoring": {
    "excellent": 10.0,
    "good": 8.0,
    "fair": 6.0,
    "poor": 3.0
  }
}
```

#### Criteria-Based
```json
"rubric": {
  "criteria": [
    "proper_terminology",
    "complete_explanation",
    "correct_examples",
    "clear_writing"
  ]
}
```

### Grading Instructions

Provide specific guidance for the AI grader:
```json
"grading_instructions": "Pay special attention to mathematical notation. Deduct points for unclear explanations even if the final answer is correct."
```

## Tips for Effective Grading

1. **Be Specific**: Detailed rubrics lead to better grading
2. **Provide Examples**: Answer keys help consistency
3. **Define Criteria**: List what makes a good answer
4. **Test First**: Run on a few submissions to validate
5. **Review Outputs**: Check the first few results for quality

## File Structure

```
assignments/my_assignment/
├── config.json          # Main configuration (required)
├── README.md           # Documentation (optional)
├── questions.pdf       # Question document (optional)
├── answer_key.pdf      # Answer key (optional)
└── rubric.json        # Separate rubric (optional)
```

## Example Workflow

```bash
# 1. List available assignments
python main.py --list

# 2. Create new assignment
python main.py --create cs101_midterm --questions 5

# 3. Edit the configuration
# Edit assignments/cs101_midterm/config.json

# 4. Add submissions
# Copy student files to submissions/cs101_midterm/

# 5. Grade
python main.py --assignment cs101_midterm

# 6. Review results
# Check output/cs101_midterm/grading_results_latest.csv
```

## Troubleshooting

**Problem:** Assignment not found  
**Solution:** Check that `config.json` exists in `assignments/{assignment_id}/`

**Problem:** No submissions graded  
**Solution:** Verify submissions are in `submissions/{assignment_id}/` with supported extensions (.pdf, .docx, .txt)

**Problem:** Poor grading quality  
**Solution:** 
- Add more detailed rubric criteria
- Include answer key for reference
- Provide specific grading instructions
- Try a more powerful model (gpt-4o instead of gpt-4o-mini)

## Need Help?

Check the main README.md or examine the `cs361_hw5` example for a real-world configuration.

