# Quick Start Guide - Image Processing Grading

## Installation

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Verify image processing libraries
python -c "import fitz; from pdf2image import convert_from_path; from PIL import Image; print('✓ All libraries installed')"
```

## Usage

### 1. Grade Assignment (Automatic Image Processing)

```bash
python main.py --assignment cs361_hw7
```

That's it! The system automatically:

- Detects images in PDFs
- Extracts text from images using Vision API
- Grades each question individually
- Generates comprehensive report

### 2. Check if PDF Has Images

```bash
python -c "
from src.processors.document_processor import DocumentProcessor
pdf_path = 'submissions/cs361_hw7/student_submission.pdf'
has_images = DocumentProcessor.has_images(pdf_path)
print(f'Has images: {has_images}')
"
```

### 3. Test Image Processing

```bash
# Run test suite
python test_image_grading.py

# Test specific submission
python main.py --assignment test_assignment
```

### 4. Disable Image Processing (Faster)

```bash
python main.py --assignment cs361_hw7 --disable-images
```

## Architecture at a Glance

```
PDF → Extract Answers → Grade Questions → Generate Report → Final Grade
      (text + images)   (individually)     (AI summary)
```

## Key Files

- `src/agents/answer_extraction_agent.py` - Extracts from images
- `src/agents/qa_grading_agent.py` - Grades questions (enhanced)
- `src/agents/report_generator.py` - Creates comprehensive reports
- `src/processors/document_processor.py` - Handles PDFs (enhanced)
- `cli.py` - Main workflow (3-stage pipeline)

## Common Tasks

### Add New Assignment

```bash
python main.py --generate-config my_assignment \
  --name "My Assignment" \
  --questions-pdf questions.pdf \
  --answer-key-pdf answers.pdf
```

### View Results

```bash
# CSV format
cat output/cs361_hw7/grading_results_latest.csv

# JSON format (detailed)
cat output/cs361_hw7/grading_results_detailed_*.json

# Logs
tail -f output/cs361_hw7/grading.log
```

### Debug Issues

```bash
# Verbose logging
python main.py --assignment cs361_hw7 --verbose

# Check specific PDF
python -c "
from src.processors.document_processor import DocumentProcessor
metadata = DocumentProcessor.get_pdf_metadata('path/to/file.pdf')
print(metadata)
"
```

## API Usage

```python
from src.agents import AnswerExtractionAgent, QAGradingAgent, ReportGenerator
from src.processors import InputProcessor

# Initialize
config = InputProcessor().load_assignment("cs361_hw7")
extractor = AnswerExtractionAgent(api_key, model="gpt-4o-mini")
grader = QAGradingAgent(api_key, model="gpt-4o-mini")
reporter = ReportGenerator(api_key, model="gpt-4o-mini")

# Process
answers = extractor.extract_answers("submission.pdf", config)
grade = grader.grade_submission_with_extraction(config, "Student", answers)
report = reporter.generate_report(grade.questions, config, "Student")

# Results
print(f"Score: {grade.total_score}/{grade.max_score}")
print(f"Comment: {report['overall_comment']}")
```

## Configuration

### Enable/Disable Image Processing

```python
workflow = GradingWorkflow(
    assignment_id="cs361_hw7",
    enable_image_processing=True  # or False
)
```

### Grading Modes

```bash
# Basic: Only rubric scores
python main.py --assignment cs361_hw7 --grading-mode basic

# Standard: Rubric + criteria + instructions
python main.py --assignment cs361_hw7 --grading-mode standard

# Full: Everything + answer key (default)
python main.py --assignment cs361_hw7 --grading-mode full
```

## Costs

Using gpt-4o-mini:

- Text grading: ~$0.001/submission
- Image processing: ~$0.003/image
- Report generation: ~$0.001/submission

Typical submission (5 images): ~$0.017

## Troubleshooting

### Images Not Processing

```bash
# Check dependencies
pip list | grep -E "pymupdf|pdf2image|Pillow"

# Verify PDF has images
python -c "from src.processors.document_processor import DocumentProcessor; print(DocumentProcessor.has_images('file.pdf'))"
```

### Vision API Errors

```bash
# Check API key
python -c "from config import OPENAI_API_KEY; print('OK' if OPENAI_API_KEY else 'NOT SET')"

# Test API directly
python -c "from langchain_openai import ChatOpenAI; ChatOpenAI(api_key='your-key', model='gpt-4o-mini').invoke('test')"
```

### Low Quality OCR

- Use higher DPI: Edit `answer_extraction_agent.py`, set `dpi=200`
- Switch to gpt-4o: Edit initialization, use `model="gpt-4o"`
- Ensure clear images: Rescan with better quality

## Documentation

- Full guide: `IMAGE_PROCESSING_README.md`
- Implementation: `IMPLEMENTATION_SUMMARY.md`
- This quick start: `QUICK_START.md`

## Support

1. Check logs: `output/<assignment_id>/grading.log`
2. Run tests: `python test_image_grading.py`
3. Enable verbose: `python main.py --verbose`
