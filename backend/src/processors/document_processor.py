"""
Document processor for extracting text from various file formats
Enhanced version with additional features
"""

import os
import PyPDF2
from docx import Document
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles extraction of text from PDF, DOCX, and TXT files"""

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num} ---\n{page_text}"
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
    def extract_text_from_txt(file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read().strip()
        except Exception as e:
            logger.error(f"Error reading TXT {file_path}: {str(e)}")
            return ""

    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Extract text from file based on extension"""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return ""

        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == ".pdf":
            return DocumentProcessor.extract_text_from_pdf(file_path)
        elif file_extension == ".docx":
            return DocumentProcessor.extract_text_from_docx(file_path)
        elif file_extension == ".txt":
            return DocumentProcessor.extract_text_from_txt(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_extension}")
            return ""

    @staticmethod
    def get_all_submissions(submissions_dir: str, extensions: Optional[List[str]] = None) -> List[str]:
        """
        Get all submission file paths from a directory
        
        Args:
            submissions_dir: Directory containing submissions
            extensions: List of allowed extensions (default: ['.pdf', '.docx', '.txt'])
        
        Returns:
            List of file paths
        """
        if extensions is None:
            extensions = [".pdf", ".docx", ".txt"]

        submissions = []
        if os.path.exists(submissions_dir):
            for filename in os.listdir(submissions_dir):
                file_path = os.path.join(submissions_dir, filename)
                if os.path.isfile(file_path):
                    file_extension = os.path.splitext(filename)[1].lower()
                    if file_extension in extensions:
                        submissions.append(file_path)
        else:
            logger.warning(f"Submissions directory not found: {submissions_dir}")

        return sorted(submissions)

    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """Get file metadata"""
        if not os.path.exists(file_path):
            return {}

        stat_info = os.stat(file_path)
        return {
            "filename": os.path.basename(file_path),
            "size_bytes": stat_info.st_size,
            "modified_time": stat_info.st_mtime,
            "extension": os.path.splitext(file_path)[1].lower(),
        }

