"""
Document processor for extracting text from various file formats
Enhanced version with image extraction support
"""

import os
import io
import PyPDF2
from docx import Document
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Try to import optional image processing libraries
try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not available. Image extraction from PDFs will be limited.")

try:
    from pdf2image import convert_from_path

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logger.warning("pdf2image not available. PDF page conversion will be disabled.")


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
    def get_all_submissions(
        submissions_dir: str, extensions: Optional[List[str]] = None
    ) -> List[str]:
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
        info = {
            "filename": os.path.basename(file_path),
            "size_bytes": stat_info.st_size,
            "modified_time": stat_info.st_mtime,
            "extension": os.path.splitext(file_path)[1].lower(),
        }

        # Add PDF-specific metadata if applicable
        if info["extension"] == ".pdf":
            pdf_metadata = DocumentProcessor.get_pdf_metadata(file_path)
            info.update(pdf_metadata)

        return info

    @staticmethod
    def has_images(file_path: str) -> bool:
        """
        Check if a PDF file contains images

        Args:
            file_path: Path to PDF file

        Returns:
            True if PDF contains images, False otherwise
        """
        if not file_path.lower().endswith(".pdf"):
            return False

        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)

                if len(image_list) > 0:
                    doc.close()
                    return True

            doc.close()
            return False

        except Exception as e:
            logger.error(f"Error checking for images in {file_path}: {str(e)}")
            return False

    @staticmethod
    def extract_images_from_pdf(file_path: str) -> List[Tuple[int, bytes]]:
        """
        Extract embedded images from PDF file

        Args:
            file_path: Path to PDF file

        Returns:
            List of tuples (page_number, image_bytes)
        """
        images = []

        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)

                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]

                    try:
                        # Extract image
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]

                        # Only keep reasonably sized images
                        if len(image_bytes) > 1000:  # At least 1KB
                            images.append((page_num + 1, image_bytes))
                            logger.debug(f"Extracted image from page {page_num + 1}")

                    except Exception as e:
                        logger.warning(
                            f"Could not extract image {img_index} from page {page_num + 1}: {str(e)}"
                        )
                        continue

            doc.close()
            logger.info(f"Extracted {len(images)} images from {file_path}")

        except ImportError:
            logger.error("PyMuPDF (fitz) not installed. Cannot extract images.")
        except Exception as e:
            logger.error(f"Error extracting images from {file_path}: {str(e)}")

        return images

    @staticmethod
    def get_pdf_metadata(file_path: str) -> dict:
        """
        Get metadata about a PDF file including page count and image count

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with metadata
        """
        metadata = {
            "page_count": 0,
            "image_count": 0,
            "has_images": False,
            "file_size_bytes": 0,
        }

        if not os.path.exists(file_path):
            return metadata

        try:
            # Get file size
            metadata["file_size_bytes"] = os.path.getsize(file_path)

            # Get PDF info using PyMuPDF for better image detection
            try:
                import fitz

                doc = fitz.open(file_path)
                metadata["page_count"] = len(doc)

                # Count images
                image_count = 0
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    image_list = page.get_images(full=True)
                    image_count += len(image_list)

                metadata["image_count"] = image_count
                metadata["has_images"] = image_count > 0

                doc.close()

            except ImportError:
                # Fallback to PyPDF2 if PyMuPDF not available
                with open(file_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    metadata["page_count"] = len(pdf_reader.pages)
                    # PyPDF2 doesn't easily detect images
                    metadata["has_images"] = None  # Unknown

        except Exception as e:
            logger.error(f"Error getting PDF metadata for {file_path}: {str(e)}")

        return metadata

    @staticmethod
    def has_images(file_path: str) -> bool:
        """
        Check if a PDF file contains images

        Args:
            file_path: Path to PDF file

        Returns:
            True if PDF contains images, False otherwise
        """
        if not PYMUPDF_AVAILABLE:
            logger.debug("PyMuPDF not available, assuming PDF may have images")
            return True  # Assume yes to trigger fallback processing

        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                if image_list:
                    doc.close()
                    return True
            doc.close()
            return False
        except Exception as e:
            logger.error(f"Error checking for images in {file_path}: {str(e)}")
            return True  # Assume yes on error

    @staticmethod
    def extract_images_from_pdf(file_path: str) -> List[Tuple[int, Image.Image]]:
        """
        Extract embedded images from PDF file using PyMuPDF

        Args:
            file_path: Path to PDF file

        Returns:
            List of tuples (page_number, PIL.Image)
        """
        images = []

        if not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not available. Cannot extract embedded images.")
            return images

        try:
            doc = fitz.open(file_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()

                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]

                        # Convert to PIL Image
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        images.append((page_num + 1, pil_image))

                        logger.debug(
                            f"Extracted image {img_index + 1} from page {page_num + 1}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to extract image {img_index} from page {page_num + 1}: {str(e)}"
                        )

            doc.close()
            logger.info(f"Extracted {len(images)} images from {file_path}")

        except Exception as e:
            logger.error(f"Error extracting images from {file_path}: {str(e)}")

        return images

    @staticmethod
    def convert_pdf_pages_to_images(
        file_path: str, dpi: int = 200
    ) -> List[Tuple[int, Image.Image]]:
        """
        Convert PDF pages to images using pdf2image
        Used as fallback when no embedded images are found

        Args:
            file_path: Path to PDF file
            dpi: Resolution for conversion (default: 200)

        Returns:
            List of tuples (page_number, PIL.Image)
        """
        images = []

        if not PDF2IMAGE_AVAILABLE:
            logger.warning(
                "pdf2image not available. Cannot convert PDF pages to images."
            )
            return images

        try:
            # Convert PDF to images
            pil_images = convert_from_path(file_path, dpi=dpi)

            for page_num, pil_image in enumerate(pil_images, 1):
                images.append((page_num, pil_image))

            logger.info(f"Converted {len(images)} pages from {file_path} to images")

        except Exception as e:
            logger.error(f"Error converting PDF pages to images: {str(e)}")

        return images

    @staticmethod
    def get_pdf_metadata(file_path: str) -> Dict[str, Any]:
        """
        Get PDF metadata including page count and image count

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with metadata
        """
        metadata = {
            "page_count": 0,
            "image_count": 0,
            "has_images": False,
            "file_size": 0,
        }

        if not os.path.exists(file_path):
            return metadata

        metadata["file_size"] = os.path.getsize(file_path)

        try:
            if PYMUPDF_AVAILABLE:
                doc = fitz.open(file_path)
                metadata["page_count"] = len(doc)

                image_count = 0
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    image_count += len(page.get_images())

                metadata["image_count"] = image_count
                metadata["has_images"] = image_count > 0
                doc.close()
            else:
                # Fallback to PyPDF2 for basic metadata
                with open(file_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    metadata["page_count"] = len(pdf_reader.pages)
                    metadata["has_images"] = True  # Assume yes without PyMuPDF

        except Exception as e:
            logger.error(f"Error getting PDF metadata: {str(e)}")

        return metadata
