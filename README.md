# Grade Lens - AI-Powered Assignment Grading System

A flexible, AI-powered grading system for question-answer assignments with support for custom rubrics, answer keys, and detailed feedback.

## Features

- **Flexible Assignment Configuration**: Define assignments with custom questions, rubrics, and grading criteria
- **Dynamic Prompt Generation**: Automatically generates grading prompts based on assignment configuration
- **Support for Answer Keys**: Optional answer keys for reference grading
- **Multiple Output Formats**: JSON (detailed), CSV (spreadsheet), and summary statistics
- **Assignment Management**: Easy CLI for managing multiple assignments
- **Detailed Feedback**: Per-question scores with reasoning and constructive feedback
- **Template System**: Quick start with example templates

## Quick Start

### 1. Installation

```bash
# Clone the repository
cd grade-lens

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Configure Your First Assignment

```bash
# Option 1: Use existing template
cp -r assignments/example_assignment assignments/my_assignment

# Option 2: Create new template via CLI
python main.py --create my_assignment --questions 3
```

Edit `assignments/my_assignment/config.json` to customize your assignment.

### 3. Add Student Submissions

Place student submissions in: `submissions/my_assignment/`

Supported formats: PDF, DOCX, TXT

### 4. Run Grading

```bash
# Grade a specific assignment
python main.py --assignment my_assignment

# List available assignments
python main.py --list

# Get help
python main.py --help
```

### 5. View Results

Results are saved in `output/my_assignment/`:
- `grading_results_TIMESTAMP.csv` - Spreadsheet format
- `grading_results_detailed_TIMESTAMP.json` - Complete grading data
- `grading_summary_TIMESTAMP.json` - Statistics and analytics
- `grading.log` - Processing log

## Project Structure

```
grade-lens/
├── src/                      # Core source code
│   ├── agents/              # Grading agents
│   │   └── qa_grading_agent.py
│   ├── models/              # Data models
│   │   ├── assignment_config.py
│   │   └── grading_result.py
│   ├── processors/          # Document and input processing
│   │   ├── document_processor.py
│   │   └── input_processor.py
│   └── utils/               # Utilities
│       ├── output_manager.py
│       └── prompt_builder.py
├── assignments/             # Assignment configurations
│   ├── cs361_hw5/          # Example assignment
│   └── example_assignment/ # Template
├── submissions/            # Student submissions (per assignment)
│   └── {assignment_id}/
├── output/                 # Grading results (per assignment)
│   └── {assignment_id}/
├── config.py               # Global configuration
├── main.py                 # Main entry point
└── requirements.txt        # Dependencies
```

## Configuration

### Environment Variables

Create a `.env` file:

```env
# Required
OPENAI_API_KEY=your_api_key_here

# Optional
OPENAI_MODEL=gpt-4o-mini
ASSIGNMENTS_BASE_DIR=assignments
SUBMISSIONS_BASE_DIR=submissions
OUTPUT_BASE_DIR=output
LOG_LEVEL=INFO
LLM_TEMPERATURE=0.1
```

### Assignment Configuration

Each assignment needs a `config.json` file in `assignments/{assignment_id}/`:

```json
{
  "assignment_id": "unique_id",
  "assignment_name": "Assignment Title",
  "course_code": "CS XXX",
  "term": "Fall 2025",
  "questions": [
    {
      "id": "question_1",
      "text": "Your question here...",
      "points": 10.0,
      "answer_key": "Optional model answer",
      "rubric": {
        "no_submission": 0.0,
        "attempted": 5.0,
        "mostly_correct": 8.0,
        "correct": 10.0,
        "criteria": ["criterion1", "criterion2"]
      }
    }
  ],
  "general_rubric": {
    "instructions": "General grading guidelines..."
  },
  "allow_partial_credit": true
}
```

See `assignments/example_assignment/README.md` for detailed configuration options.

## Usage Examples

### List Available Assignments

```bash
python main.py --list
```

### Create New Assignment

```bash
python main.py --create midterm_exam --questions 5
```

### Grade Assignment

```bash
python main.py --assignment cs361_hw5
```

### Verbose Logging

```bash
python main.py --assignment cs361_hw5 --verbose
```

## Grading Rubrics

### Standard Rubric (Per Question)

```json
{
  "no_submission": 0.0,
  "attempted": 5.0,      // Partial understanding
  "mostly_correct": 8.0,  // Minor errors
  "correct": 10.0         // Fully correct
}
```

### Custom Rubric

```json
{
  "criteria": [
    "proper_terminology",
    "complete_explanation",
    "correct_examples"
  ],
  "custom_scoring": {
    "excellent": 10,
    "good": 8,
    "fair": 6
  }
}
```

## Output Formats

### CSV Output

Flattened format suitable for spreadsheets:
- Student information
- Total score and percentage
- Per-question scores and reasoning
- Letter grades

### Detailed JSON

Complete grading data including:
- All scores and feedback
- Timestamp and metadata
- Criteria met/missed
- Review flags

### Summary JSON

Statistical analysis:
- Class statistics (average, median, range)
- Grade distribution
- Per-question analytics
- Students requiring review

## Advanced Features

### Answer Keys

Provide answer keys for reference:

```json
{
  "questions": [
    {
      "id": "q1",
      "text": "Question...",
      "answer_key": "Model answer here..."
    }
  ]
}
```

Or reference a file:

```json
{
  "answer_key_file": "answer_key.pdf"
}
```

### Question-Specific Rubrics

Override general rubric per question:

```json
{
  "questions": [
    {
      "id": "q1",
      "rubric": {
        "criteria": ["specific_to_this_question"]
      }
    }
  ]
}
```

### Grading Instructions

Provide specific guidance:

```json
{
  "grading_instructions": "Pay special attention to mathematical notation. Award partial credit for correct approach even if final answer is wrong."
}
```

## Model Selection

Supported models:
- `gpt-4o-mini` (default, fast and cost-effective)
- `gpt-4o` (more capable, higher cost)
- `gpt-4-turbo` (balanced option)

Change in `.env`:
```env
OPENAI_MODEL=gpt-4o
```

## Tips for Best Results

1. **Detailed Rubrics**: More specific criteria = better grading consistency
2. **Answer Keys**: Provide when possible for reference
3. **Test First**: Grade a few submissions manually to validate
4. **Review Outputs**: Always review AI-generated grades
5. **Iterate**: Refine rubrics based on results

## Troubleshooting

### Assignment Not Found
- Verify `config.json` exists in `assignments/{assignment_id}/`
- Run `python main.py --list` to see available assignments

### No Submissions Graded
- Check submissions are in `submissions/{assignment_id}/`
- Verify file formats (.pdf, .docx, .txt)
- Check file permissions

### Poor Grading Quality
- Add more detailed rubric criteria
- Include answer keys
- Provide specific grading instructions
- Try more powerful model (gpt-4o)

### API Errors
- Verify OPENAI_API_KEY is set correctly
- Check API quota and billing
- Review error logs in `output/{assignment_id}/grading.log`

## Examples

### Example 1: CS361 HW5 (Included)

Automata theory assignment with proof-based questions:
```bash
python main.py --assignment cs361_hw5
```

### Example 2: Custom Template

See `assignments/example_assignment/` for a complete example with:
- Multiple question types
- Answer keys
- Custom rubrics
- Detailed documentation

## Development

### Running Tests

```bash
python test_setup.py
```

### Adding New Features

The system is modular:
- `src/agents/` - Add new grading agents
- `src/processors/` - Add document type support
- `src/models/` - Extend data models
- `src/utils/` - Add utilities

## Migration from Version 1.0

If you have the old hardcoded grader:

1. Your existing submissions are in `submissions/cs361_hw5/`
2. Configuration is in `assignments/cs361_hw5/config.json`
3. Run: `python main.py --assignment cs361_hw5`

## Future Enhancements

- Programming assignment grading
- Multiple LLM support (Gemini, Claude)
- Web UI for human-in-the-loop review
- Bias detection and reporting
- LMS integration (Canvas, Blackboard)

## Contributing

Contributions welcome! This is a research project for CS 557 AI at Boise State University.

## License

[Add your license here]

## Citation

If you use this system in your research or teaching, please cite:

```
Grade Lens: AI-Powered Grading Agent for Question-Answer Assignments
CS 557 AI Final Project, Boise State University, Fall 2025
```

## Support

For issues and questions:
- Check documentation in `assignments/example_assignment/README.md`
- Review logs in `output/{assignment_id}/grading.log`
- Examine example configuration in `assignments/cs361_hw5/`

---

**Version:** 2.0.0  
**Last Updated:** November 2025
