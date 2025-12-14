"""
Dynamic prompt builder for grading based on assignment configuration
"""

import json
import logging
from typing import Optional
from ..models.assignment_config import AssignmentConfig, QuestionConfig, RubricConfig

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds dynamic prompts for LLM grading based on assignment configuration"""

    def __init__(self, assignment_config: AssignmentConfig, grading_mode: str = "full"):
        """
        Initialize PromptBuilder with grading mode support

        Args:
            assignment_config: Assignment configuration
            grading_mode: Grading mode controlling what information to include
                - "basic": Only basic rubric (no criteria, no instructions, no answer key)
                - "standard": Rubric with criteria and instructions (no answer key)
                - "full": Everything including answer key (default)
        """
        self.config = assignment_config
        self.grading_mode = grading_mode

        # Validate grading mode
        valid_modes = ["basic", "standard", "full"]
        if self.grading_mode not in valid_modes:
            logger.warning(
                f"Invalid grading mode '{self.grading_mode}', defaulting to 'full'"
            )
            self.grading_mode = "full"

    def build_system_prompt(self) -> str:
        """
        Build the system prompt for the grading agent

        Returns:
            Complete system prompt string
        """
        prompt_parts = []

        # Role definition
        prompt_parts.append(
            "You are an expert grading assistant. Your task is to grade student submissions "
            "fairly, consistently, and with detailed explanations."
        )

        # Assignment context
        prompt_parts.append(f"\n\nASSIGNMENT: {self.config.assignment_name}")
        if self.config.course_code:
            prompt_parts.append(f"Course: {self.config.course_code}")
        if self.config.term:
            prompt_parts.append(f"Term: {self.config.term}")
        prompt_parts.append(f"Total Points: {self.config.total_points}")

        # General grading instructions
        if self.config.grading_instructions:
            prompt_parts.append(
                f"\n\nGENERAL INSTRUCTIONS:\n{self.config.grading_instructions}"
            )

        # Questions section
        prompt_parts.append("\n\nQUESTIONS:")
        for i, question in enumerate(self.config.questions, 1):
            prompt_parts.append(f"\n{'-' * 80}")
            prompt_parts.append(
                f"Question {i} (ID: {question.id}) - {question.points} points"
            )
            prompt_parts.append(f"{'-' * 80}")
            prompt_parts.append(f"\n{question.text}")

            # Add answer key if available (only in full mode)
            if self.grading_mode == "full" and question.answer_key:
                prompt_parts.append(
                    f"\n[MODEL ANSWER/ANSWER KEY]:\n{question.answer_key}"
                )

            # Add question-specific rubric
            rubric = question.rubric or self.config.general_rubric
            if rubric:
                prompt_parts.append("\n[GRADING RUBRIC]:")
                prompt_parts.append(self._format_rubric(rubric, question.points))

        # General rubric if exists and not already shown per-question
        if self.config.general_rubric and not any(
            q.rubric for q in self.config.questions
        ):
            prompt_parts.append(f"\n\n{'-' * 80}")
            prompt_parts.append("GENERAL GRADING RUBRIC (applies to all questions):")
            prompt_parts.append(f"{'-' * 80}")
            prompt_parts.append(self._format_rubric(self.config.general_rubric))

        # Complete answer key if provided (only in full mode)
        if self.grading_mode == "full" and self.config.answer_key_text:
            prompt_parts.append(f"\n\n{'-' * 80}")
            prompt_parts.append("COMPLETE ANSWER KEY DOCUMENT:")
            prompt_parts.append(f"{'-' * 80}")
            prompt_parts.append(self.config.answer_key_text)
            prompt_parts.append(f"\n{'-' * 80}")
            prompt_parts.append(
                "Use this answer key as reference when grading student submissions."
            )

        # Output format instructions
        prompt_parts.append("\n\n" + self._get_output_format_instructions())

        # Grading guidelines
        prompt_parts.append("\n\n" + self._get_grading_guidelines())

        return "\n".join(prompt_parts)

    def build_user_prompt(self, student_name: str, submission_text: str) -> str:
        """
        Build the user prompt with student submission

        Args:
            student_name: Name of the student
            submission_text: The student's submission text

        Returns:
            User prompt string
        """
        prompt_parts = []

        prompt_parts.append(f"Student: {student_name}")
        prompt_parts.append("\n" + "=" * 80)
        prompt_parts.append("STUDENT SUBMISSION:")
        prompt_parts.append("=" * 80)
        prompt_parts.append(f"\n{submission_text}")
        prompt_parts.append("\n" + "=" * 80)

        prompt_parts.append(
            "\nPlease grade this submission based on the assignment questions and rubric provided. "
            "Return ONLY the JSON response with scores and detailed reasoning for each question."
        )

        return "\n".join(prompt_parts)

    def _format_rubric(
        self, rubric: RubricConfig, question_points: Optional[float] = None
    ) -> str:
        """Format rubric for display in prompt (respects grading_mode)"""
        parts = []

        # Criteria (only in standard and full modes)
        if self.grading_mode in ["standard", "full"] and rubric.criteria:
            parts.append("Grading Criteria:")
            for criterion in rubric.criteria:
                parts.append(f"  - {criterion}")

        # Scoring guidelines (always included)
        parts.append("\nScoring Guidelines:")

        if rubric.correct is not None:
            parts.append(f"  - Full Credit (Correct): {rubric.correct} points")
        elif question_points:
            parts.append(f"  - Full Credit (Correct): {question_points} points")

        if rubric.mostly_correct is not None:
            parts.append(
                f"  - Mostly Correct (minor errors): {rubric.mostly_correct} points"
            )

        if rubric.attempted is not None:
            parts.append(
                f"  - Attempted (partial understanding): {rubric.attempted} points"
            )

        parts.append(f"  - No Submission/No Attempt: {rubric.no_submission} points")

        # Additional instructions (only in standard and full modes)
        if self.grading_mode in ["standard", "full"] and rubric.instructions:
            parts.append(f"\nAdditional Instructions:\n{rubric.instructions}")

        # Custom scoring (always included if present)
        if rubric.custom_scoring:
            parts.append("\nCustom Scoring Rules:")
            for key, value in rubric.custom_scoring.items():
                parts.append(f"  - {key}: {value}")

        return "\n".join(parts)

    def _get_output_format_instructions(self) -> str:
        """Get output format instructions for the LLM"""
        example_questions = []
        for question in self.config.questions:
            example_questions.append(
                {
                    "question_id": question.id,
                    "score": 0.0,
                    "max_score": question.points,
                    "reasoning": "Detailed explanation of why this score was given...",
                    "feedback": "Constructive feedback for the student...",
                }
            )

        example_output = {
            "total_score": 0.0,
            "max_score": self.config.total_points,
            "overall_comment": "Overall assessment of the submission...",
            "questions": example_questions,
        }

        return f"""OUTPUT FORMAT:

You MUST return your grading in the following JSON format:

{json.dumps(example_output, indent=2)}

IMPORTANT:
- Return ONLY valid JSON, no additional text before or after
- Include all fields shown in the example
- Provide detailed reasoning for each question's score
- Ensure scores don't exceed max_score for each question
- Total score should equal the sum of individual question scores
- Give constructive feedback that helps students improve
"""

    def _get_grading_guidelines(self) -> str:
        """Get general grading guidelines"""
        guidelines = """GRADING GUIDELINES:

1. READ CAREFULLY: Review the entire submission before assigning grades

2. BE FAIR: Apply the rubric consistently and objectively

3. BE THOROUGH: Provide detailed reasoning for each score
   - Explain what the student did well
   - Identify specific errors or missing elements
   - Reference rubric criteria in your reasoning

4. BE CONSTRUCTIVE: Give feedback that helps students learn
   - Point out strengths to reinforce good practices
   - Suggest specific improvements for areas of weakness
   - Maintain a respectful and encouraging tone

5. BE ACCURATE: Ensure all scores are within valid ranges
   - Individual scores ≤ max_score for that question
   - Total score = sum of individual question scores

6. HANDLE EDGE CASES:
   - Empty/no response: Give 0 points with appropriate reasoning
   - Partial attempts: Award partial credit based on rubric
   - Unclear responses: Make best judgment and explain uncertainty
"""

        if self.config.allow_partial_credit:
            guidelines += "\n7. PARTIAL CREDIT: This assignment allows partial credit. Award points proportionally based on the rubric."
        else:
            guidelines += "\n7. NO PARTIAL CREDIT: This assignment does not allow partial credit. Only award full points or zero."

        return guidelines

    def get_json_schema(self) -> dict:
        """
        Get JSON schema for the expected output format
        This can be used for structured output with OpenAI
        """
        question_properties = {}
        required_questions = []

        for question in self.config.questions:
            question_properties[question.id] = {
                "type": "object",
                "properties": {
                    "question_id": {"type": "string"},
                    "score": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": question.points,
                    },
                    "max_score": {"type": "number"},
                    "reasoning": {"type": "string"},
                    "feedback": {"type": "string"},
                },
                "required": ["question_id", "score", "max_score", "reasoning"],
            }
            required_questions.append(question.id)

        schema = {
            "type": "object",
            "properties": {
                "total_score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": self.config.total_points,
                },
                "max_score": {"type": "number"},
                "overall_comment": {"type": "string"},
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question_id": {"type": "string"},
                            "score": {"type": "number"},
                            "max_score": {"type": "number"},
                            "reasoning": {"type": "string"},
                            "feedback": {"type": "string"},
                        },
                        "required": ["question_id", "score", "max_score", "reasoning"],
                    },
                },
            },
            "required": ["total_score", "max_score", "overall_comment", "questions"],
        }

        return schema

    def build_extraction_prompt(
        self, submission_text: str, image_text: Optional[str] = None
    ) -> str:
        """
        Build prompt for answer extraction from text and images

        Args:
            submission_text: Text extracted from submission
            image_text: Text extracted from images (if any)

        Returns:
            Prompt for extraction agent
        """
        prompt_parts = []

        prompt_parts.append(
            "You are an expert at extracting and organizing student answers from submission documents. "
            "Your task is to identify which parts of the submission correspond to which questions."
        )

        prompt_parts.append(f"\n\nASSIGNMENT: {self.config.assignment_name}")
        prompt_parts.append(f"Total Questions: {len(self.config.questions)}")

        prompt_parts.append("\n\nQUESTIONS TO MATCH:")
        for i, question in enumerate(self.config.questions, 1):
            prompt_parts.append(f"\n{i}. Question ID: {question.id}")
            prompt_parts.append(f"   Text: {question.text[:200]}...")  # First 200 chars

        prompt_parts.append("\n\n" + "=" * 80)
        prompt_parts.append("SUBMISSION CONTENT (TEXT):")
        prompt_parts.append("=" * 80)
        prompt_parts.append(f"\n{submission_text}")

        if image_text:
            prompt_parts.append("\n\n" + "=" * 80)
            prompt_parts.append("SUBMISSION CONTENT (FROM IMAGES):")
            prompt_parts.append("=" * 80)
            prompt_parts.append(f"\n{image_text}")

        prompt_parts.append("\n\n" + "=" * 80)
        prompt_parts.append("TASK:")
        prompt_parts.append("=" * 80)
        prompt_parts.append(
            "\nFor each question, extract the student's answer from the submission content above. "
            "Return a JSON object mapping question IDs to answer content."
        )

        example_output = {
            question.id: {
                "answer_text": "The student's answer content here...",
                "found_in": "text_extraction",  # or "image_extraction" or "both"
                "confidence": "high",  # or "medium" or "low"
            }
            for question in self.config.questions
        }

        prompt_parts.append(
            f"\n\nEXPECTED OUTPUT FORMAT:\n{json.dumps(example_output, indent=2)}"
        )

        prompt_parts.append(
            "\n\nIMPORTANT:\n"
            "- Match answers to questions based on question numbers, headers, or content\n"
            "- If an answer spans multiple sections, combine them\n"
            "- If no answer is found for a question, set answer_text to 'No answer provided'\n"
            "- Include ALL content that appears to be part of the answer\n"
            "- Return ONLY valid JSON, no additional text"
        )

        return "\n".join(prompt_parts)

    def build_single_question_prompt(
        self,
        question: QuestionConfig,
        student_answer: str,
        context: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Build prompts for grading a single question

        Args:
            question: Question configuration
            student_answer: Student's answer to this question
            context: Optional additional context from other answers

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # System prompt
        system_parts = []

        system_parts.append(
            "You are an expert grading assistant. Your task is to grade a single question "
            "from a student assignment fairly and thoroughly."
        )

        system_parts.append(f"\n\nASSIGNMENT: {self.config.assignment_name}")
        if self.config.course_code:
            system_parts.append(f"Course: {self.config.course_code}")

        system_parts.append("\n\n" + "=" * 80)
        system_parts.append(f"QUESTION (ID: {question.id}) - {question.points} points")
        system_parts.append("=" * 80)
        system_parts.append(f"\n{question.text}")

        # Add answer key (only in full mode)
        if self.grading_mode == "full" and question.answer_key:
            system_parts.append(
                f"\n\n[MODEL ANSWER/ANSWER KEY]:\n{question.answer_key}"
            )

        # Add rubric
        rubric = question.rubric or self.config.general_rubric
        if rubric:
            system_parts.append("\n\n[GRADING RUBRIC]:")
            system_parts.append(self._format_rubric(rubric, question.points))

        # Output format
        example_output = {
            "question_id": question.id,
            "score": 0.0,
            "max_score": question.points,
            "reasoning": "Detailed explanation of the grade...",
            "feedback": "Constructive feedback for the student...",
            "criteria_met": ["criterion 1", "criterion 2"],
            "criteria_missed": ["criterion 3"],
        }

        system_parts.append(
            f"\n\nOUTPUT FORMAT:\n{json.dumps(example_output, indent=2)}"
        )

        system_parts.append(
            "\n\nGRADING GUIDELINES:\n"
            "- Evaluate based on correctness, completeness, and clarity\n"
            "- Reference specific rubric criteria in your reasoning\n"
            "- Provide constructive feedback\n"
            "- Return ONLY valid JSON"
        )

        system_prompt = "\n".join(system_parts)

        # User prompt
        user_parts = []

        user_parts.append("=" * 80)
        user_parts.append("STUDENT'S ANSWER:")
        user_parts.append("=" * 80)
        user_parts.append(f"\n{student_answer}")
        user_parts.append("\n" + "=" * 80)

        if context:
            user_parts.append("\n[Additional Context from Submission]:")
            user_parts.append(context[:500] + "..." if len(context) > 500 else context)
            user_parts.append("")

        user_parts.append(
            "\nPlease grade this answer based on the question and rubric provided. "
            "Return ONLY the JSON response."
        )

        user_prompt = "\n".join(user_parts)

        return system_prompt, user_prompt

    def build_image_extraction_prompt(
        self, question_context: Optional[str] = None
    ) -> str:
        """
        Build prompt for extracting text from images using Vision API

        Args:
            question_context: Optional context about what questions to look for

        Returns:
            Prompt for vision model
        """
        prompt_parts = []

        prompt_parts.append(
            "You are analyzing an image from a student assignment submission. "
            "Your task is to extract ALL text content from this image, including:\n"
            "- Handwritten answers\n"
            "- Typed text\n"
            "- Mathematical notation\n"
            "- Diagrams with labels\n"
            "- Any other written content"
        )

        if question_context:
            prompt_parts.append(
                f"\n\nContext: This submission is for an assignment with the following questions:"
            )
            prompt_parts.append(question_context)

        prompt_parts.append(
            "\n\nPlease transcribe ALL visible text from the image. "
            "Maintain the structure and organization as much as possible. "
            "If text is unclear or ambiguous, include your best interpretation and note the uncertainty."
        )

        return "\n".join(prompt_parts)
