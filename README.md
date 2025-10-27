# CS361 HW5 Grading System

An automated grading system using LangChain and OpenAI to grade student submissions for CS361 HW5.

## Features

- **Automated Document Processing**: Extracts text from PDF and DOCX files
- **AI-Powered Grading**: Uses OpenAI GPT-4 for intelligent grading
- **Flexible Grading Criteria** (per question - 15 points each):
  - No submission: 0 points
  - Attempted: 7.5 points (half marks - 50% of 15 points)
  - Correct solution: 15 points (full marks)
  - Mostly correct but incomplete: 14 points (deduct 1 point)
- **CSV Output**: Generates detailed grading results in CSV format
- **Comprehensive Logging**: Tracks all grading activities

## Setup

1. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Set OpenAI Configuration**:
   Create a `.env` file in the project root:

   ```
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   ```

   Available models: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`

3. **Configure Questions**:
   Edit the `questions` list in `main.py` to match your assignment questions.

## Usage

1. **Place submissions** in the `submissions` directory
2. **Run the grading workflow**:
   ```bash
   python main.py
   ```

## Output Files

- `grading_results.csv`: Main results file with scores, reasoning, and Canvas SpeedGrader URLs
- `grading_results_detailed.json`: Detailed JSON results for reference
- `grading.log`: Comprehensive logging of the grading process

### CSV Columns:

- `student_name`: Student's name extracted from filename
- `filename`: Original submission filename
- `student_id`: Student ID extracted from filename (2nd part)
- `url`: Canvas SpeedGrader URL for direct grading access
- `total_score`: Total points earned
- `question_1_score`, `question_1_reasoning`: Question 1 details
- `question_2_score`, `question_2_reasoning`: Question 2 details

## File Structure

```
grader/
├── main.py                 # Main workflow
├── config.py              # Configuration settings
├── document_processor.py   # Document text extraction
├── grading_agent.py       # LangChain grading agent
├── csv_manager.py         # CSV output management
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── submissions/      # Student submissions directory
```

## Assignment Details

**CS361 HW5 - Two Questions (15 points each, 30 points total):**

1. **Question 1 (15 pts)**: Use the pumping lemma to prove the following language is not regular:
   L1 = {w over {a,b,c} | w has twice the number of a's as b's.}

2. **Question 2 (15 pts)**: Prove the language L2 defined below is either regular or not regular.
   L2 = {w over {a,b} | w has the same number of a's and b's, and |w| <=2}

## Grading Criteria

The system implements the following grading criteria (per question):

1. **No submission for a question**: 0 points
2. **Student attempted the question**: 7.5 points (half marks - 50% of 15 points)
3. **Student completely solved correctly**: 15 points (full marks)
4. **Student got most right but incomplete**: 14 points (deduct 1 point)

## Customization

- **Questions**: Modify the `questions` list in `main.py`
- **Grading criteria**: Update the system prompt in `grading_agent.py`
- **Output format**: Customize the CSV structure in `csv_manager.py`

## Error Handling

The system includes comprehensive error handling:

- Invalid file formats are skipped with warnings
- API errors are logged and handled gracefully
- Empty submissions receive zero points
- Processing errors are tracked in the results

## Logging

All activities are logged to both console and `grading.log` file, including:

- Processing status for each submission
- Grading results and scores
- Errors and warnings
- Summary statistics
