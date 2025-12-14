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
            logger.warning(f"Invalid grading mode '{self.grading_mode}', defaulting to 'full'")
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
            prompt_parts.append(f"\n\nGENERAL INSTRUCTIONS:\n{self.config.grading_instructions}")

        # Questions section
        prompt_parts.append("\n\nQUESTIONS:")
        for i, question in enumerate(self.config.questions, 1):
            prompt_parts.append(f"\n{'-' * 80}")
            prompt_parts.append(f"Question {i} (ID: {question.id}) - {question.points} points")
            prompt_parts.append(f"{'-' * 80}")
            prompt_parts.append(f"\n{question.text}")

            # Add answer key if available (only in full mode)
            if self.grading_mode == "full" and question.answer_key:
                prompt_parts.append(f"\n[MODEL ANSWER/ANSWER KEY]:\n{question.answer_key}")

            # Add question-specific rubric
            rubric = question.rubric or self.config.general_rubric
            if rubric:
                prompt_parts.append("\n[GRADING RUBRIC]:")
                prompt_parts.append(self._format_rubric(rubric, question.points))

        # General rubric if exists and not already shown per-question
        if self.config.general_rubric and not any(q.rubric for q in self.config.questions):
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
            prompt_parts.append("Use this answer key as reference when grading student submissions.")

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

    def _format_rubric(self, rubric: RubricConfig, question_points: Optional[float] = None) -> str:
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
            parts.append(f"  - Mostly Correct (minor errors): {rubric.mostly_correct} points")

        if rubric.attempted is not None:
            parts.append(f"  - Attempted (partial understanding): {rubric.attempted} points")

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
            example_questions.append({
                "question_id": question.id,
                "score": 0.0,
                "max_score": question.points,
                "reasoning": "Detailed explanation of why this score was given...",
                "feedback": "Constructive feedback for the student...",
            })

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
                    "score": {"type": "number", "minimum": 0, "maximum": question.points},
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

