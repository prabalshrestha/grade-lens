"""
Answer Extraction Agent - Extracts student answers from text and images in PDFs
"""

import os
import io
import base64
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image
from pdf2image import convert_from_path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..models.assignment_config import AssignmentConfig, QuestionConfig
from ..processors.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class AnswerExtractionAgent:
    """Agent that extracts student answers from PDFs with text and image support"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        enable_image_processing: bool = True,
    ):
        """
        Initialize the answer extraction agent

        Args:
            api_key: OpenAI API key
            model: Model name (must support vision for image processing)
            temperature: Temperature for generation
            enable_image_processing: Whether to enable image processing
        """
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
        )
        self.doc_processor = DocumentProcessor()
        self.enable_image_processing = enable_image_processing
        self.model_name = model

    def extract_answers(
        self,
        submission_path: str,
        assignment_config: AssignmentConfig,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract student answers from submission PDF

        Args:
            submission_path: Path to submission PDF
            assignment_config: Assignment configuration

        Returns:
            Dictionary mapping question_id to answer data:
            {
                "question_1": {
                    "text": "extracted text answer",
                    "images": ["base64_image1", "base64_image2"],
                    "extracted_from_image": True/False,
                    "extraction_notes": "notes about extraction"
                }
            }
        """
        logger.info(f"Extracting answers from: {os.path.basename(submission_path)}")

        try:
            # Extract text content using existing processor
            text_content = self.doc_processor.extract_text_from_file(submission_path)
            logger.info(f"Extracted {len(text_content)} characters of text")

            # Extract images if enabled and file is PDF
            images = []
            has_images = False

            if self.enable_image_processing and submission_path.lower().endswith(
                ".pdf"
            ):
                images, has_images = self._extract_images_hybrid(submission_path)
                if has_images:
                    logger.info(f"Extracted {len(images)} images from PDF")

            # Map content to questions
            extracted_answers = self._map_content_to_questions(
                text_content=text_content,
                images=images,
                questions=assignment_config.questions,
            )

            logger.info(
                f"Successfully extracted answers for {len(extracted_answers)} questions"
            )
            return extracted_answers

        except Exception as e:
            logger.error(f"Error extracting answers: {str(e)}", exc_info=True)
            # Return empty answers for all questions
            return {
                q.id: {
                    "text": "",
                    "images": [],
                    "extracted_from_image": False,
                    "extraction_notes": f"Error during extraction: {str(e)}",
                }
                for q in assignment_config.questions
            }

    def _extract_images_hybrid(self, pdf_path: str) -> Tuple[List[Image.Image], bool]:
        """
        Hybrid image extraction: try PyMuPDF first, fallback to pdf2image

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (list of PIL Images, has_images flag)
        """
        try:
            # First, try to extract embedded images using PyMuPDF
            images = self._extract_images_pymupdf(pdf_path)

            if images:
                logger.info(f"Extracted {len(images)} embedded images using PyMuPDF")
                return images, True

            # If no embedded images, check if PDF pages might be scanned/image-based
            # Convert pages to images as fallback
            logger.info("No embedded images found, checking if pages are image-based")
            images = self._convert_pages_to_images(pdf_path, max_pages=10)

            if images:
                logger.info(f"Converted {len(images)} PDF pages to images")
                return images, True

            return [], False

        except Exception as e:
            logger.error(f"Error in hybrid image extraction: {str(e)}")
            return [], False

    def _extract_images_pymupdf(self, pdf_path: str) -> List[Image.Image]:
        """
        Extract embedded images from PDF using PyMuPDF

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of PIL Image objects
        """
        images = []

        try:
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)

                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]

                    try:
                        # Extract image
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]

                        # Convert to PIL Image
                        image = Image.open(io.BytesIO(image_bytes))

                        # Only keep images that are reasonably large (likely content, not icons)
                        if image.width > 100 and image.height > 100:
                            images.append(image)
                            logger.debug(
                                f"Extracted image {img_index} from page {page_num + 1}: {image.size}"
                            )

                    except Exception as e:
                        logger.warning(
                            f"Could not extract image {img_index} from page {page_num + 1}: {str(e)}"
                        )
                        continue

            doc.close()

        except Exception as e:
            logger.error(f"Error extracting images with PyMuPDF: {str(e)}")

        return images

    def _convert_pages_to_images(
        self, pdf_path: str, max_pages: Optional[int] = None, dpi: int = 150
    ) -> List[Image.Image]:
        """
        Convert PDF pages to images using pdf2image

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to convert (None = all)
            dpi: DPI for image conversion (higher = better quality but larger)

        Returns:
            List of PIL Image objects
        """
        images = []

        try:
            # Get page count first
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()

            # Limit pages if specified
            last_page = min(page_count, max_pages) if max_pages else page_count

            # Only convert if there are few pages (to avoid excessive API costs)
            if page_count > 20:
                logger.warning(
                    f"PDF has {page_count} pages, skipping page-to-image conversion"
                )
                return []

            logger.info(f"Converting {last_page} pages to images at {dpi} DPI")

            # Convert pages to images
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=1,
                last_page=last_page,
            )

        except Exception as e:
            logger.error(f"Error converting PDF pages to images: {str(e)}")

        return images

    def _map_content_to_questions(
        self,
        text_content: str,
        images: List[Image.Image],
        questions: List[QuestionConfig],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Map extracted content (text and images) to questions

        Args:
            text_content: Extracted text from PDF
            images: List of extracted images
            questions: List of question configurations

        Returns:
            Dictionary mapping question_id to answer data
        """
        extracted_answers = {}

        # If we have images, use vision API to extract text from them
        image_text = ""
        image_data = []

        if images:
            try:
                image_text, image_data = self._extract_text_from_images(images)
                logger.info(
                    f"Extracted {len(image_text)} characters from {len(images)} images"
                )
            except Exception as e:
                logger.error(f"Error extracting text from images: {str(e)}")

        # Combine text and image content
        combined_content = text_content
        if image_text:
            combined_content += f"\n\n--- Content from Images ---\n{image_text}"

        # Use LLM to map content to questions
        try:
            mapping = self._llm_map_to_questions(combined_content, questions)

            # Add image metadata
            for question_id, answer_data in mapping.items():
                answer_data["images"] = image_data if images else []
                answer_data["extracted_from_image"] = bool(images)

                # Add extraction notes
                notes = []
                if images:
                    notes.append(f"Processed {len(images)} images")
                if not answer_data.get("text", "").strip():
                    notes.append("No text answer found")
                answer_data["extraction_notes"] = "; ".join(notes) if notes else None

            extracted_answers = mapping

        except Exception as e:
            logger.error(f"Error mapping content to questions: {str(e)}")
            # Return empty answers
            extracted_answers = {
                q.id: {
                    "text": "",
                    "images": [],
                    "extracted_from_image": False,
                    "extraction_notes": f"Mapping error: {str(e)}",
                }
                for q in questions
            }

        return extracted_answers

    def _extract_text_from_images(
        self, images: List[Image.Image]
    ) -> Tuple[str, List[str]]:
        """
        Extract text from images using OpenAI Vision API

        Args:
            images: List of PIL Image objects

        Returns:
            Tuple of (extracted text, list of base64 encoded images)
        """
        if not images:
            return "", []

        # Limit number of images to process (cost consideration)
        max_images = min(len(images), 10)
        images_to_process = images[:max_images]

        # Convert images to base64
        image_data = []
        for img in images_to_process:
            try:
                # Resize large images to reduce API costs
                if img.width > 2000 or img.height > 2000:
                    img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)

                # Convert to base64
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                image_data.append(img_str)
            except Exception as e:
                logger.warning(f"Could not process image: {str(e)}")
                continue

        if not image_data:
            return "", []

        # Create prompt for vision API
        system_prompt = """You are an expert at extracting text from images of student homework submissions.
Extract ALL visible text, including handwritten answers, diagrams with labels, and any annotations.
Preserve the structure and organization of the content.
If you see question numbers or labels, include them.
Output the extracted text clearly and completely."""

        # Build message with images
        content = [
            {
                "type": "text",
                "text": f"Extract all text from these {len(image_data)} images. Include question numbers, answers, and any written content.",
            }
        ]

        # Add images to content
        for img_b64 in image_data:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_b64}",
                        "detail": "high",  # Use high detail for better text extraction
                    },
                }
            )

        try:
            # Call vision API
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=content),
            ]

            response = self.llm.invoke(messages)
            extracted_text = response.content

            return extracted_text, image_data

        except Exception as e:
            logger.error(f"Error calling vision API: {str(e)}")
            return "", image_data

    def _llm_map_to_questions(
        self,
        content: str,
        questions: List[QuestionConfig],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Use LLM to map extracted content to specific questions

        Args:
            content: Combined text and image content
            questions: List of questions

        Returns:
            Dictionary mapping question_id to answer data
        """
        # Build question list for prompt
        question_list = []
        for q in questions:
            question_list.append(
                f"- {q.id}: {q.text[:200]}..."
            )  # Truncate long questions

        questions_str = "\n".join(question_list)

        system_prompt = """You are an expert at analyzing student submissions and mapping answers to questions.
Given a submission's content and a list of questions, identify which parts of the content answer which questions.

Return a JSON object mapping question IDs to their answers in this format:
{
  "question_1": {
    "text": "The student's answer for question 1...",
    "confidence": "high/medium/low"
  },
  "question_2": {
    "text": "The student's answer for question 2...",
    "confidence": "high/medium/low"
  }
}

If you cannot find an answer for a question, include an empty text field with low confidence.
Extract the complete answer including all reasoning, calculations, and explanations."""

        user_prompt = f"""Questions in this assignment:
{questions_str}

Student submission content:
{content[:10000]}

Map the submission content to the questions above. Return JSON only."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = self.llm.invoke(messages)
            response_text = response.content

            # Parse JSON response
            import json
            import re

            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                mapping_data = json.loads(json_match.group(0))
            else:
                mapping_data = json.loads(response_text)

            # Ensure all questions have entries
            result = {}
            for q in questions:
                if q.id in mapping_data:
                    result[q.id] = mapping_data[q.id]
                else:
                    result[q.id] = {"text": "", "confidence": "low"}

            return result

        except Exception as e:
            logger.error(f"Error in LLM mapping: {str(e)}")
            # Return empty answers for all questions
            return {
                q.id: {
                    "text": (
                        content if len(questions) == 1 else ""
                    ),  # If single question, use all content
                    "confidence": "low",
                }
                for q in questions
            }
