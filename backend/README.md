# Grade Lens Backend

FastAPI-based backend for AI-powered assignment grading system.

## Overview

The backend provides:
- **REST API** for web interface
- **CLI** for command-line grading
- **AI Grading Engine** using OpenAI GPT models
- **Config Generator** from PDF files

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

## Configuration

Edit `.env` file:

```env
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
OPENAI_MODEL=gpt-4o-mini
ASSIGNMENTS_BASE_DIR=../assignments
SUBMISSIONS_BASE_DIR=../submissions
OUTPUT_BASE_DIR=../output
LOG_LEVEL=INFO
LLM_TEMPERATURE=0.1
```

## Running

### Web API Server

```bash
python main.py
# Runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

### CLI Interface

```bash
# List assignments
python cli.py --list

# Grade an assignment
python cli.py --assignment cs361_hw5

# Create new assignment template
python cli.py --create my_assignment --questions 5

# Generate config from PDF
python cli.py --generate-config hw6 \
  --name "Homework 6" \
  --questions-pdf questions.pdf \
  --answer-key-pdf answers.pdf
```

### Start Both Servers

```bash
./start-web.sh
```

This starts:
- Backend API on http://localhost:8000
- Frontend on http://localhost:5173

## API Endpoints

### Assignments

- `GET /api/assignments` - List all assignments
- `GET /api/assignments/{id}` - Get assignment details
- `POST /api/assignments/upload` - Upload PDFs
- `POST /api/assignments/generate-config` - Generate config from PDFs
- `POST /api/assignments/{id}/config` - Save/update config
- `DELETE /api/assignments/{id}` - Delete assignment

### Submissions

- `GET /api/assignments/{id}/submissions` - List submissions
- `POST /api/assignments/{id}/submissions` - Upload submissions

### Grading

- `POST /api/assignments/{id}/grade` - Start grading
- `GET /api/assignments/{id}/results` - Get results
- `GET /api/assignments/{id}/results/download` - Download CSV/JSON

### Health

- `GET /health` - Health check
- `GET /` - API info

## Project Structure

```
backend/
├── src/
│   ├── agents/
│   │   ├── qa_grading_agent.py      # Main grading agent
│   │   └── config_generator_agent.py # PDF to config generator
│   ├── models/
│   │   ├── assignment_config.py     # Assignment data model
│   │   └── grading_result.py        # Grading result model
│   ├── processors/
│   │   ├── document_processor.py    # PDF/DOCX processing
│   │   └── input_processor.py       # Config loading
│   └── utils/
│       ├── output_manager.py        # Result saving
│       └── prompt_builder.py        # LLM prompt generation
├── main.py                          # FastAPI server
├── cli.py                           # Command-line interface
├── config.py                        # Configuration
├── requirements.txt                 # Dependencies
├── .env                            # Environment variables
├── start-web.sh                    # Startup script
└── temp_uploads/                   # Temporary file storage
```

## Grading Modes

Three grading modes for experimental comparison:

### Full Mode (Default)
Uses everything:
- Answer keys
- Rubrics with 4 score levels
- Grading criteria
- Instructions

### Standard Mode
Uses:
- Rubrics
- Criteria
- Instructions
- **No answer keys**

### Basic Mode
Uses only:
- Basic rubric (4 score levels)
- **No criteria, instructions, or answer keys**

Example:
```bash
python cli.py --assignment hw7 --grading-mode standard
```

## Assignment Configuration

Assignments are stored in `../assignments/{id}/config.json`:

```json
{
  "assignment_id": "hw1",
  "assignment_name": "Homework 1",
  "course_code": "CS361",
  "term": "Fall 2025",
  "total_points": 50,
  "grading_instructions": "General instructions...",
  "questions": [
    {
      "id": "question_1",
      "text": "Question text...",
      "points": 10,
      "question_type": "essay",
      "answer_key": "Model answer...",
      "rubric": {
        "no_submission": 0,
        "attempted": 5,
        "mostly_correct": 9,
        "correct": 10,
        "criteria": [
          "Uses proper terminology",
          "Shows step-by-step work"
        ],
        "instructions": "Specific grading instructions..."
      }
    }
  ]
}
```

## Output

Results are saved in `../output/{assignment_id}/`:

- `grading_results_{timestamp}.csv` - Spreadsheet format
- `grading_results_detailed_{timestamp}.json` - Complete data
- `grading_summary_{timestamp}.json` - Statistics
- `grading.log` - Processing log

## Development

### Run with Auto-Reload

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests

```bash
python test_system.py
```

### Add New Features

The system is modular:

- `src/agents/` - Add new grading agents
- `src/processors/` - Add document type support
- `src/models/` - Extend data models
- `src/utils/` - Add utilities

## Troubleshooting

### Module Not Found

```bash
# Make sure dependencies are installed
pip install -r requirements.txt
```

### API Key Error

```bash
# Check .env file exists and has valid key
cat .env
```

### Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Path Issues

The `config.py` automatically resolves paths relative to project root. Your `assignments/`, `submissions/`, and `output/` directories stay at the project root level.

## Dependencies

Key packages:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `langchain` - LLM integration
- `langchain-openai` - OpenAI support
- `pypdf2` - PDF processing
- `python-docx` - DOCX processing
- `pandas` - Data handling
- `python-dotenv` - Environment variables

## Performance Tips

1. **Use Basic Mode** for faster grading (no answer key processing)
2. **Batch Processing** - Upload all submissions at once
3. **Monitor Logs** - Check `../output/{id}/grading.log` for progress
4. **API Rate Limits** - Be aware of OpenAI rate limits

## Security Notes

- API keys are stored in `.env` (not in git)
- CORS is configured for localhost only
- File uploads are validated by type and size
- Sandbox prevents access to system files

## Support

For issues:
1. Check API docs: http://localhost:8000/docs
2. Review logs: `../output/{assignment_id}/grading.log`
3. Check configuration: `../assignments/{assignment_id}/config.json`

## License

CS 557 AI Final Project, Boise State University

---

**API Documentation:** http://localhost:8000/docs  
**Main README:** ../README.md
