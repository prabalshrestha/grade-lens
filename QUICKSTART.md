# Quick Start Guide

## Ready to Grade CS361 HW5!

Your system is set up and ready to grade 55 student submissions for CS361 HW5.

## Steps to Run

### 1. Activate Virtual Environment
```bash
cd /Users/prabalshrestha/Documents/BSU/grade-lens
source venv/bin/activate
```

### 2. Verify Environment
```bash
# List available assignments
python main.py --list
```

You should see:
```
Available Assignments:
------------------------------------------------------------
  cs361_hw5
    Name: CS361 HW5 - Automata Theory
    Questions: 2
    Total Points: 30.0

  example_assignment
    Name: Example Assignment Template
    Questions: 3
    Total Points: 35.0
```

### 3. Grade CS361 HW5
```bash
python main.py --assignment cs361_hw5
```

This will:
- Process all 55 submissions in `submissions/cs361_hw5/`
- Grade using the configured rubric
- Generate detailed output files

### 4. View Results

Results are saved in `output/cs361_hw5/`:

**CSV File** (Open in Excel/Google Sheets):
```
output/cs361_hw5/grading_results_latest.csv
```
Contains:
- Student names and IDs
- Total scores and percentages
- Letter grades
- Per-question scores and reasoning

**Detailed JSON** (For analysis):
```
output/cs361_hw5/grading_results_detailed_TIMESTAMP.json
```

**Summary Statistics**:
```
output/cs361_hw5/grading_summary_TIMESTAMP.json
```

**Log File**:
```
output/cs361_hw5/grading.log
```

## What Each File Contains

### grading_results_latest.csv
Spreadsheet-friendly format:
- `student_name`, `student_id`
- `total_score`, `max_score`, `percentage`, `letter_grade`
- `question_1_score`, `question_1_reasoning`
- `question_2_score`, `question_2_reasoning`
- `overall_comment`

### grading_results_detailed_TIMESTAMP.json
Complete grading data:
```json
{
  "grading_session": {
    "timestamp": "2025-11-06T...",
    "total_submissions": 55
  },
  "results": [
    {
      "student_name": "...",
      "total_score": 28.5,
      "max_score": 30,
      "questions": [...],
      "overall_comment": "..."
    }
  ]
}
```

### grading_summary_TIMESTAMP.json
Statistics:
```json
{
  "statistics": {
    "total_submissions": 55,
    "average_score": 24.5,
    "average_percentage": 81.67,
    "highest_score": 30,
    "lowest_score": 0
  },
  "grade_distribution": {
    "A": 15,
    "B": 20,
    "C": 12,
    "D": 5,
    "F": 3
  },
  "question_statistics": {...}
}
```

## Assignment Configuration

The CS361 HW5 assignment is configured in:
```
assignments/cs361_hw5/config.json
```

**Question 1** (15 points):
- Pumping lemma proof
- Rubric: 0 (no submission), 7.5 (attempted), 14 (mostly correct), 15 (correct)

**Question 2** (15 points):
- Regular language proof
- Same rubric structure

## Common Commands

### List Assignments
```bash
python main.py --list
```

### Grade Specific Assignment
```bash
python main.py --assignment cs361_hw5
```

### Create New Assignment
```bash
python main.py --create my_new_hw --questions 3
```

### Verbose Output (for debugging)
```bash
python main.py --assignment cs361_hw5 --verbose
```

### Get Help
```bash
python main.py --help
```

## Tips for First Run

1. **Review Sample Results First**
   - After grading, open the CSV file
   - Check the first few results for quality
   - Review the reasoning provided

2. **Adjust if Needed**
   - If grading seems too harsh/lenient, adjust rubric in `assignments/cs361_hw5/config.json`
   - Re-run grading with updated configuration

3. **Use Verbose Mode**
   - Add `--verbose` flag to see detailed processing
   - Helpful for debugging any issues

4. **Check Logs**
   - Review `output/cs361_hw5/grading.log` for any warnings or errors

## Expected Runtime

- **Per submission**: ~5-10 seconds (depending on LLM model)
- **55 submissions**: ~5-10 minutes total
- Using `gpt-4o-mini` (default) is faster and cheaper
- Can use `gpt-4o` for better quality (set in `.env`)

## Troubleshooting

### "OPENAI_API_KEY not found"
```bash
# Create .env file with:
echo "OPENAI_API_KEY=sk-..." > .env
```

### "Assignment not found"
```bash
# List available assignments
python main.py --list

# Check assignment directory exists
ls -la assignments/
```

### "No submissions found"
```bash
# Verify submissions are in correct directory
ls submissions/cs361_hw5/

# Should show 55 PDF/DOCX files
```

### Poor grading quality
- Try using `gpt-4o` instead of `gpt-4o-mini`
- Add more detailed rubric criteria
- Include answer key for reference

## Creating New Assignments

1. **Use Template**
```bash
python main.py --create midterm_exam --questions 5
```

2. **Edit Configuration**
```bash
# Edit assignments/midterm_exam/config.json
# Define questions, points, rubrics
```

3. **Add Submissions**
```bash
# Copy student files to:
# submissions/midterm_exam/
```

4. **Grade**
```bash
python main.py --assignment midterm_exam
```

## Next Steps After Grading

1. **Review Results**
   - Open CSV in spreadsheet software
   - Spot-check reasoning for accuracy
   - Look for patterns in errors

2. **Statistical Analysis**
   - Review summary JSON for class statistics
   - Identify difficult questions (low averages)
   - Check grade distribution

3. **Export for Canvas**
   - CSV can be imported to Canvas gradebook
   - Add student IDs column if needed

4. **Manual Review**
   - Flag any suspicious grades for human review
   - Check submissions with very high or very low scores

## Support

- **Documentation**: See `README.md` and `assignments/example_assignment/README.md`
- **Examples**: Check `assignments/cs361_hw5/` for working configuration
- **Validation**: Run `python test_system.py` to verify setup

## Ready to Grade!

You're all set. Just run:

```bash
source venv/bin/activate
python main.py --assignment cs361_hw5
```

Good luck! 🎓

