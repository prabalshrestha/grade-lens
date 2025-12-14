"""
Configuration Generator Agent - Automatically creates assignment configs from PDFs
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Optional, Dict, Any
import json
import logging
import re

from ..processors.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class ConfigGeneratorAgent:
    """Agent that generates assignment configurations from question and answer PDFs"""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize the config generator agent
        
        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-4o recommended for better extraction)
        """
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=0.1,
        )
        self.doc_processor = DocumentProcessor()

    def generate_config(
        self,
        assignment_id: str,
        assignment_name: str,
        questions_pdf_path: str,
        answer_key_pdf_path: Optional[str] = None,
        course_code: Optional[str] = None,
        term: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate assignment configuration from PDF files
        
        Args:
            assignment_id: Unique identifier for the assignment
            assignment_name: Human-readable name
            questions_pdf_path: Path to PDF with questions
            answer_key_pdf_path: Optional path to answer key PDF
            course_code: Course code (e.g., "CS361")
            term: Academic term (e.g., "Fall 2025")
            
        Returns:
            Dictionary with assignment configuration
        """
        logger.info(f"Generating config for: {assignment_name}")

        # Extract text from questions PDF
        questions_text = self.doc_processor.extract_text_from_file(questions_pdf_path)
        if not questions_text:
            raise ValueError(f"Could not extract text from: {questions_pdf_path}")

        logger.info(f"Extracted {len(questions_text)} characters from questions PDF")

        # Extract text from answer key if provided
        answer_key_text = None
        if answer_key_pdf_path:
            answer_key_text = self.doc_processor.extract_text_from_file(answer_key_pdf_path)
            logger.info(f"Extracted {len(answer_key_text)} characters from answer key PDF")

        # Generate config using LLM
        config = self._generate_config_with_llm(
            assignment_id=assignment_id,
            assignment_name=assignment_name,
            questions_text=questions_text,
            answer_key_text=answer_key_text,
            course_code=course_code,
            term=term,
        )

        return config

    def _generate_config_with_llm(
        self,
        assignment_id: str,
        assignment_name: str,
        questions_text: str,
        answer_key_text: Optional[str],
        course_code: Optional[str],
        term: Optional[str],
    ) -> Dict[str, Any]:
        """Use LLM to extract and structure assignment configuration"""

        system_prompt = """You are an expert at analyzing academic assignments and creating structured configurations.

Your task is to analyze the provided assignment questions and create a JSON configuration that includes:

1. Extract all questions from the document
2. Identify the point value for each question
3. Create appropriate question IDs (e.g., "question_1", "question_2")
4. Determine question types (essay, short_answer, proof, problem_solving, etc.)
5. If answer key is provided, match answers to questions
6. Create reasonable grading rubrics based on question complexity

For the rubric, use this structure:
- no_submission: 0.0
- attempted: 50% of points (shows partial understanding)
- mostly_correct: 90-95% of points (minor errors)
- correct: 100% of points

Also suggest grading criteria based on the question type.

Return ONLY valid JSON in this exact format:

{
  "questions": [
    {
      "id": "question_1",
      "text": "Full question text...",
      "points": 10.0,
      "answer_key": "Model answer if provided, otherwise null",
      "question_type": "essay|short_answer|proof|problem_solving|coding",
      "rubric": {
        "no_submission": 0.0,
        "attempted": 5.0,
        "mostly_correct": 9.0,
        "correct": 10.0,
        "criteria": [
          "criterion_1",
          "criterion_2"
        ],
        "instructions": "Specific grading instructions for this question"
      }
    }
  ],
  "total_points": 30.0,
  "grading_instructions": "General instructions for grading this assignment"
}

Be thorough and extract ALL questions. Preserve the original question text exactly."""

        user_prompt_parts = [
            f"Assignment: {assignment_name}",
            "\n" + "=" * 80,
            "QUESTIONS DOCUMENT:",
            "=" * 80,
            questions_text,
        ]

        if answer_key_text:
            user_prompt_parts.extend([
                "\n" + "=" * 80,
                "ANSWER KEY:",
                "=" * 80,
                answer_key_text,
            ])

        user_prompt_parts.append(
            "\n" + "=" * 80 +
            "\nAnalyze the above and generate the configuration JSON."
        )

        user_prompt = "\n".join(user_prompt_parts)

        logger.info("Calling LLM to generate configuration...")

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = self.llm.invoke(messages)
        response_text = response.content

        # Parse JSON from response
        extracted_config = self._parse_json_from_response(response_text)

        if not extracted_config:
            raise ValueError("Failed to generate valid configuration from LLM")

        # Build complete config
        complete_config = {
            "assignment_id": assignment_id,
            "assignment_name": assignment_name,
            "course_code": course_code or "UNKNOWN",
            "term": term or "Unknown Term",
            "questions": extracted_config.get("questions", []),
            "total_points": extracted_config.get("total_points"),
            "grading_instructions": extracted_config.get("grading_instructions", 
                "Grade fairly and consistently. Provide detailed feedback."),
            "allow_partial_credit": True,
            "created_by": "ConfigGeneratorAgent",
            "version": "1.0",
        }

        # Calculate total points if not provided
        if not complete_config["total_points"]:
            complete_config["total_points"] = sum(
                q.get("points", 0) for q in complete_config["questions"]
            )

        logger.info(
            f"Generated config with {len(complete_config['questions'])} questions, "
            f"{complete_config['total_points']} total points"
        )

        return complete_config

    def _parse_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from LLM response"""
        try:
            # Try direct parse first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract from markdown code block
            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```",
                response_text,
                re.DOTALL
            )
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # Try to find JSON object in text
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            logger.error("Could not parse JSON from LLM response")
            logger.debug(f"Response: {response_text[:500]}...")
            return None

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate generated configuration
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []

        # Check required fields
        required_fields = ["assignment_id", "assignment_name", "questions"]
        for field in required_fields:
            if field not in config:
                issues.append(f"Missing required field: {field}")

        # Check questions
        if "questions" in config:
            if len(config["questions"]) == 0:
                issues.append("No questions found in configuration")

            for i, question in enumerate(config["questions"], 1):
                # Check required question fields
                if "id" not in question:
                    issues.append(f"Question {i}: Missing 'id' field")
                if "text" not in question:
                    issues.append(f"Question {i}: Missing 'text' field")
                if "points" not in question:
                    issues.append(f"Question {i}: Missing 'points' field")
                elif question["points"] <= 0:
                    issues.append(f"Question {i}: Invalid points value")

        is_valid = len(issues) == 0
        return is_valid, issues

    def save_config(
        self,
        config: Dict[str, Any],
        output_path: str,
        pretty: bool = True
    ):
        """
        Save configuration to JSON file
        
        Args:
            config: Configuration dictionary
            output_path: Path to save JSON file
            pretty: Whether to format JSON nicely
        """
        indent = 2 if pretty else None

        with open(output_path, "w") as f:
            json.dump(config, f, indent=indent)

        logger.info(f"Saved configuration to: {output_path}")

    def preview_config(self, config: Dict[str, Any]) -> str:
        """
        Generate a human-readable preview of the configuration
        
        Returns:
            Formatted preview string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("ASSIGNMENT CONFIGURATION PREVIEW")
        lines.append("=" * 80)
        lines.append(f"Assignment ID: {config.get('assignment_id')}")
        lines.append(f"Name: {config.get('assignment_name')}")
        lines.append(f"Course: {config.get('course_code', 'N/A')}")
        lines.append(f"Term: {config.get('term', 'N/A')}")
        lines.append(f"Total Points: {config.get('total_points')}")
        lines.append(f"Number of Questions: {len(config.get('questions', []))}")
        lines.append("")

        for i, question in enumerate(config.get("questions", []), 1):
            lines.append(f"\nQuestion {i}: {question.get('id')}")
            lines.append(f"  Points: {question.get('points')}")
            lines.append(f"  Type: {question.get('question_type', 'unknown')}")
            
            # Show first 100 chars of question
            q_text = question.get('text', '')
            if len(q_text) > 100:
                q_text = q_text[:100] + "..."
            lines.append(f"  Text: {q_text}")
            
            # Show if answer key provided
            if question.get('answer_key'):
                lines.append(f"  Answer Key: ✓ Provided")
            else:
                lines.append(f"  Answer Key: ✗ Not provided")

            # Show rubric
            rubric = question.get('rubric', {})
            if rubric:
                lines.append(f"  Rubric:")
                lines.append(f"    - No submission: {rubric.get('no_submission', 0)}")
                lines.append(f"    - Attempted: {rubric.get('attempted', 0)}")
                lines.append(f"    - Mostly correct: {rubric.get('mostly_correct', 0)}")
                lines.append(f"    - Correct: {rubric.get('correct', 0)}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)

