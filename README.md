# Grade Lens - AI-Powered Grading System

A web-based AI grading system with React frontend and FastAPI backend.

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API key

### Installation

```bash
# 1. Install backend dependencies
cd backend
pip install -r requirements.txt

# 2. Create .env file in backend directory
echo "OPENAI_API_KEY=your_api_key_here" > .env

# 3. Install frontend dependencies
cd ../frontend
npm install
```

### Running the Application

**Start both servers:**
```bash
cd backend
./start-web.sh
```

Or start separately:

**Backend (Terminal 1):**
```bash
cd backend
python main.py
# Runs on http://localhost:8000
```

**Frontend (Terminal 2):**
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

### Access
- **Web UI:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs

## Features

- 🤖 AI-powered config generation from PDFs
- 📝 Create and edit assignments with custom rubrics
- 📤 Upload student submissions (PDF, DOCX, TXT)
- ⚙️ Three grading modes (Full, Standard, Basic)
- 📊 View detailed results with statistics
- 💾 Export to CSV or JSON

## Project Structure

```
grade-lens/
├── backend/          # FastAPI server + core grading system
│   ├── src/         # Core grading agents and processors
│   ├── main.py      # API server
│   ├── cli.py       # CLI interface
│   └── README.md    # Backend documentation
├── frontend/         # React web interface
│   ├── src/         # React components and pages
│   └── README.md    # Frontend documentation
├── assignments/      # Assignment configurations
├── submissions/      # Student submissions
└── output/          # Grading results
```

## Documentation

- **Backend:** See `backend/README.md` for API and CLI documentation
- **Frontend:** See `frontend/README.md` for UI development guide

## Usage

1. **Create Assignment**
   - Upload question and answer key PDFs
   - AI generates configuration
   - Review and edit rubrics
   - Save

2. **Upload Submissions**
   - Upload student files
   - View submission list

3. **Grade**
   - Select grading mode
   - Start grading
   - View results

4. **Export**
   - Download CSV or JSON

## Support

For issues and questions:
- Check backend/frontend README files
- Review API docs at http://localhost:8000/docs
- Check logs in `output/{assignment_id}/grading.log`

---

**CS 557 AI Final Project**  
**Boise State University, Fall 2025**
