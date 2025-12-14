"""
FastAPI backend for Grade Lens web interface
"""

import os
import sys
import json
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import OPENAI_API_KEY, OPENAI_MODEL, SUBMISSIONS_BASE_DIR, OUTPUT_BASE_DIR, ASSIGNMENTS_BASE_DIR
from src.processors.document_processor import DocumentProcessor
from src.processors.input_processor import InputProcessor
from src.agents.qa_grading_agent import QAGradingAgent
from src.agents.config_generator_agent import ConfigGeneratorAgent
from src.utils.output_manager import OutputManager
from src.models.assignment_config import AssignmentConfig
from cli import GradingWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Grade Lens API",
    description="AI-Powered Assignment Grading System",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
doc_processor = DocumentProcessor()
input_processor = InputProcessor(ASSIGNMENTS_BASE_DIR)

# ============================================================================
# Models
# ============================================================================

class GenerateConfigRequest(BaseModel):
    assignment_id: str
    assignment_name: str
    course_code: Optional[str] = None
    term: Optional[str] = None

class UpdateConfigRequest(BaseModel):
    config: dict

class GradeAssignmentRequest(BaseModel):
    assignment_id: str
    grading_mode: str = "full"

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Grade Lens API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "openai_configured": bool(OPENAI_API_KEY),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/assignments")
async def list_assignments():
    """List all available assignments"""
    try:
        assignments = input_processor.list_available_assignments()
        
        assignments_data = []
        for assignment_id in assignments:
            config = input_processor.load_assignment(assignment_id)
            if config:
                # Check for results
                output_dir = os.path.join(OUTPUT_BASE_DIR, assignment_id)
                has_results = os.path.exists(output_dir) and any(
                    f.endswith('.csv') for f in os.listdir(output_dir)
                )
                
                # Count submissions
                submissions_dir = os.path.join(SUBMISSIONS_BASE_DIR, assignment_id)
                num_submissions = 0
                if os.path.exists(submissions_dir):
                    num_submissions = len(doc_processor.get_all_submissions(submissions_dir))
                
                assignments_data.append({
                    "id": assignment_id,
                    "name": config.assignment_name,
                    "course_code": config.course_code,
                    "term": config.term,
                    "num_questions": len(config.questions),
                    "total_points": config.total_points,
                    "num_submissions": num_submissions,
                    "has_results": has_results,
                })
        
        return {"assignments": assignments_data}
    
    except Exception as e:
        logger.error(f"Error listing assignments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assignments/{assignment_id}")
async def get_assignment(assignment_id: str):
    """Get assignment details"""
    try:
        config = input_processor.load_assignment(assignment_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Convert to dict
        config_dict = {
            "assignment_id": config.assignment_id,
            "assignment_name": config.assignment_name,
            "course_code": config.course_code,
            "term": config.term,
            "total_points": config.total_points,
            "allow_partial_credit": config.allow_partial_credit,
            "grading_instructions": config.grading_instructions,
            "questions": [
                {
                    "id": q.id,
                    "text": q.text,
                    "points": q.points,
                    "question_type": q.question_type,
                    "answer_key": q.answer_key,
                    "rubric": q.rubric,
                }
                for q in config.questions
            ],
        }
        
        return config_dict
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assignments/upload")
async def upload_assignment_files(
    questions_pdf: UploadFile = File(...),
    answer_key_pdf: Optional[UploadFile] = File(None),
):
    """Upload assignment PDF files"""
    try:
        # Create temp directory
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        # Save questions PDF
        questions_path = temp_dir / questions_pdf.filename
        with open(questions_path, "wb") as f:
            content = await questions_pdf.read()
            f.write(content)
        
        # Save answer key PDF if provided
        answer_key_path = None
        if answer_key_pdf:
            answer_key_path = temp_dir / answer_key_pdf.filename
            with open(answer_key_path, "wb") as f:
                content = await answer_key_pdf.read()
                f.write(content)
        
        return {
            "message": "Files uploaded successfully",
            "questions_pdf": str(questions_path),
            "answer_key_pdf": str(answer_key_path) if answer_key_path else None,
        }
    
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assignments/generate-config")
async def generate_assignment_config(
    assignment_id: str = Form(...),
    assignment_name: str = Form(...),
    course_code: Optional[str] = Form(None),
    term: Optional[str] = Form(None),
    questions_pdf_path: str = Form(...),
    answer_key_pdf_path: Optional[str] = Form(None),
):
    """Generate assignment configuration from uploaded PDFs"""
    try:
        logger.info(f"Generating config for: {assignment_name}")
        
        # Check if files exist
        if not os.path.exists(questions_pdf_path):
            raise HTTPException(status_code=404, detail="Questions PDF not found")
        
        if answer_key_pdf_path and not os.path.exists(answer_key_pdf_path):
            raise HTTPException(status_code=404, detail="Answer key PDF not found")
        
        # Initialize config generator
        generator = ConfigGeneratorAgent(OPENAI_API_KEY, model=OPENAI_MODEL)
        
        # Generate configuration
        config = generator.generate_config(
            assignment_id=assignment_id,
            assignment_name=assignment_name,
            questions_pdf_path=questions_pdf_path,
            answer_key_pdf_path=answer_key_pdf_path,
            course_code=course_code,
            term=term,
        )
        
        # Validate configuration
        is_valid, issues = generator.validate_config(config)
        
        return {
            "config": config,
            "is_valid": is_valid,
            "validation_issues": issues,
        }
    
    except Exception as e:
        logger.error(f"Error generating config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assignments/{assignment_id}/config")
async def save_assignment_config(assignment_id: str, request: UpdateConfigRequest):
    """Save or update assignment configuration"""
    try:
        # Create assignment directory
        assignment_dir = os.path.join(ASSIGNMENTS_BASE_DIR, assignment_id)
        os.makedirs(assignment_dir, exist_ok=True)
        
        # Create submissions directory
        submissions_dir = os.path.join(SUBMISSIONS_BASE_DIR, assignment_id)
        os.makedirs(submissions_dir, exist_ok=True)
        
        # Save configuration
        config_path = os.path.join(assignment_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(request.config, f, indent=2)
        
        # Create README
        readme_path = os.path.join(assignment_dir, "README.md")
        with open(readme_path, "w") as f:
            f.write(f"# {request.config.get('assignment_name', 'Assignment')}\n\n")
            f.write(f"**Course:** {request.config.get('course_code', 'N/A')}  \n")
            f.write(f"**Term:** {request.config.get('term', 'N/A')}  \n")
            f.write(f"**Total Points:** {request.config.get('total_points', 0)}  \n\n")
            f.write(f"## Questions\n\n")
            f.write(f"This assignment has {len(request.config.get('questions', []))} questions.\n")
        
        return {
            "message": "Configuration saved successfully",
            "assignment_id": assignment_id,
            "config_path": config_path,
        }
    
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assignments/{assignment_id}/submissions")
async def upload_submissions(
    assignment_id: str,
    files: List[UploadFile] = File(...),
):
    """Upload student submissions"""
    try:
        # Create submissions directory
        submissions_dir = os.path.join(SUBMISSIONS_BASE_DIR, assignment_id)
        os.makedirs(submissions_dir, exist_ok=True)
        
        uploaded_files = []
        
        for file in files:
            # Check file extension
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ['.pdf', '.docx', '.txt']:
                continue
            
            # Save file
            file_path = os.path.join(submissions_dir, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            uploaded_files.append(file.filename)
        
        return {
            "message": f"Uploaded {len(uploaded_files)} submissions",
            "files": uploaded_files,
        }
    
    except Exception as e:
        logger.error(f"Error uploading submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assignments/{assignment_id}/submissions")
async def list_submissions(assignment_id: str):
    """List all submissions for an assignment"""
    try:
        submissions_dir = os.path.join(SUBMISSIONS_BASE_DIR, assignment_id)
        
        if not os.path.exists(submissions_dir):
            return {"submissions": []}
        
        submission_files = doc_processor.get_all_submissions(submissions_dir)
        
        submissions = []
        for file_path in submission_files:
            filename = os.path.basename(file_path)
            student_name = QAGradingAgent.extract_student_name(filename)
            student_id = QAGradingAgent.extract_student_id(filename)
            
            submissions.append({
                "filename": filename,
                "student_name": student_name,
                "student_id": student_id,
                "file_path": file_path,
            })
        
        return {"submissions": submissions}
    
    except Exception as e:
        logger.error(f"Error listing submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assignments/{assignment_id}/grade")
async def grade_assignment(
    assignment_id: str,
    background_tasks: BackgroundTasks,
    grading_mode: str = "full",
):
    """Start grading an assignment"""
    try:
        # Check if assignment exists
        config = input_processor.load_assignment(assignment_id)
        if not config:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Check if submissions exist
        submissions_dir = os.path.join(SUBMISSIONS_BASE_DIR, assignment_id)
        if not os.path.exists(submissions_dir):
            raise HTTPException(status_code=404, detail="No submissions found")
        
        submission_files = doc_processor.get_all_submissions(submissions_dir)
        if not submission_files:
            raise HTTPException(status_code=404, detail="No submissions found")
        
        # Start grading in background
        background_tasks.add_task(
            run_grading_workflow,
            assignment_id,
            grading_mode
        )
        
        return {
            "message": "Grading started",
            "assignment_id": assignment_id,
            "num_submissions": len(submission_files),
            "grading_mode": grading_mode,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting grading: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assignments/{assignment_id}/results")
async def get_results(assignment_id: str, grading_mode: str = "full"):
    """Get grading results for an assignment"""
    try:
        # Determine output directory based on grading mode
        if grading_mode != "full":
            output_dir = os.path.join(OUTPUT_BASE_DIR, f"{assignment_id}_{grading_mode}")
        else:
            output_dir = os.path.join(OUTPUT_BASE_DIR, assignment_id)
        
        if not os.path.exists(output_dir):
            raise HTTPException(status_code=404, detail="No results found")
        
        # Find latest detailed JSON
        json_files = [f for f in os.listdir(output_dir) if f.startswith("grading_results_detailed_") and f.endswith(".json")]
        
        if not json_files:
            raise HTTPException(status_code=404, detail="No detailed results found")
        
        # Get the latest file
        latest_json = sorted(json_files)[-1]
        json_path = os.path.join(output_dir, latest_json)
        
        with open(json_path, "r") as f:
            results = json.load(f)
        
        # Load summary if exists
        summary_files = [f for f in os.listdir(output_dir) if f.startswith("grading_summary_") and f.endswith(".json")]
        summary = None
        if summary_files:
            latest_summary = sorted(summary_files)[-1]
            summary_path = os.path.join(output_dir, latest_summary)
            with open(summary_path, "r") as f:
                summary = json.load(f)
        
        return {
            "results": results,
            "summary": summary,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assignments/{assignment_id}/results/download")
async def download_results(assignment_id: str, format: str = "csv", grading_mode: str = "full"):
    """Download results in CSV or JSON format"""
    try:
        # Determine output directory
        if grading_mode != "full":
            output_dir = os.path.join(OUTPUT_BASE_DIR, f"{assignment_id}_{grading_mode}")
        else:
            output_dir = os.path.join(OUTPUT_BASE_DIR, assignment_id)
        
        if not os.path.exists(output_dir):
            raise HTTPException(status_code=404, detail="No results found")
        
        if format == "csv":
            # Find latest CSV
            csv_files = [f for f in os.listdir(output_dir) if f.endswith(".csv")]
            if not csv_files:
                raise HTTPException(status_code=404, detail="No CSV results found")
            
            latest_csv = sorted(csv_files)[-1]
            file_path = os.path.join(output_dir, latest_csv)
            
            return FileResponse(
                file_path,
                media_type="text/csv",
                filename=latest_csv,
            )
        
        elif format == "json":
            # Find latest detailed JSON
            json_files = [f for f in os.listdir(output_dir) if f.startswith("grading_results_detailed_") and f.endswith(".json")]
            if not json_files:
                raise HTTPException(status_code=404, detail="No JSON results found")
            
            latest_json = sorted(json_files)[-1]
            file_path = os.path.join(output_dir, latest_json)
            
            return FileResponse(
                file_path,
                media_type="application/json",
                filename=latest_json,
            )
        
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'csv' or 'json'")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/assignments/{assignment_id}")
async def delete_assignment(assignment_id: str):
    """Delete an assignment and all associated data"""
    try:
        # Delete assignment directory
        assignment_dir = os.path.join(ASSIGNMENTS_BASE_DIR, assignment_id)
        if os.path.exists(assignment_dir):
            shutil.rmtree(assignment_dir)
        
        # Delete submissions directory
        submissions_dir = os.path.join(SUBMISSIONS_BASE_DIR, assignment_id)
        if os.path.exists(submissions_dir):
            shutil.rmtree(submissions_dir)
        
        # Delete output directory
        output_dir = os.path.join(OUTPUT_BASE_DIR, assignment_id)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        
        return {"message": "Assignment deleted successfully"}
    
    except Exception as e:
        logger.error(f"Error deleting assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Helper Functions
# ============================================================================

def run_grading_workflow(assignment_id: str, grading_mode: str = "full"):
    """Run grading workflow in background"""
    try:
        logger.info(f"Starting grading workflow for: {assignment_id}")
        
        workflow = GradingWorkflow(
            assignment_id=assignment_id,
            grading_mode=grading_mode,
        )
        
        success = workflow.run()
        
        if success:
            logger.info(f"Grading completed successfully for: {assignment_id}")
        else:
            logger.error(f"Grading failed for: {assignment_id}")
    
    except Exception as e:
        logger.error(f"Error in grading workflow: {str(e)}", exc_info=True)

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

