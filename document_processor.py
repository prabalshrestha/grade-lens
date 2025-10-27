import os
import PyPDF2
from docx import Document
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles extraction of text from PDF and DOCX files"""

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {str(e)}")
            return ""

    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {str(e)}")
            return ""

    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Extract text from file based on extension"""
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == ".pdf":
            return DocumentProcessor.extract_text_from_pdf(file_path)
        elif file_extension == ".docx":
            return DocumentProcessor.extract_text_from_docx(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_extension}")
            return ""

    @staticmethod
    def get_all_submissions(submissions_dir: str) -> List[str]:
        """Get all submission file paths"""
        submissions = []
        if os.path.exists(submissions_dir):
            for filename in os.listdir(submissions_dir):
                file_path = os.path.join(submissions_dir, filename)
                if os.path.isfile(file_path) and (
                    filename.endswith(".pdf") or filename.endswith(".docx")
                ):
                    submissions.append(file_path)
        return submissions
