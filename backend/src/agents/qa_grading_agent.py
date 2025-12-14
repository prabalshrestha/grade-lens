"""
Flexible Q&A Grading Agent using LangChain and OpenAI
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Optional, Dict, Any
import json
import logging
import re

from ..models.assignment_config import AssignmentConfig
from ..models.grading_result import AssignmentGrade, QuestionGrade
from ..utils.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class QAGradingAgent:
    """Flexible grading agent for question-answer assignments"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        grading_mode: str = "full",
    ):
        """
        Initialize the grading agent
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4o-mini)
            temperature: Temperature for generation (lower = more consistent)
            grading_mode: Grading mode - "basic", "standard", or "full" (default)
        """
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
        )
        self.model_name = model
        self.grading_mode = grading_mode

    def grade_submission(
        self,
        assignment_config: AssignmentConfig,
        student_name: str,
        submission_text: str,
        student_id: Optional[str] = None,
        submission_file: Optional[str] = None,
    ) -> Optional[AssignmentGrade]:
        """
        Grade a single submission
        
        Args:
            assignment_config: Assignment configuration
            student_name: Student's name
            submission_text: The submission content
            student_id: Optional student ID
            submission_file: Optional submission filename
            
        Returns:
            AssignmentGrade object or None if grading fails
        """
        try:
            # Build prompts with grading mode
            prompt_builder = PromptBuilder(assignment_config, grading_mode=self.grading_mode)
            system_prompt = prompt_builder.build_system_prompt()
            user_prompt = prompt_builder.build_user_prompt(student_name, submission_text)

            logger.debug(f"Grading submission for {student_name}")

            # Call LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = self.llm.invoke(messages)
            response_text = response.content

            # Parse JSON response
            grading_data = self._parse_llm_response(response_text)

            if not grading_data:
                logger.error(f"Failed to parse LLM response for {student_name}")
                return self._create_error_grade(
                    assignment_config, student_name, student_id, submission_file
                )

            # Convert to AssignmentGrade object
            assignment_grade = self._convert_to_assignment_grade(
                grading_data,
                assignment_config,
                student_name,
                student_id,
                submission_file,
            )

            logger.info(
                f"Successfully graded {student_name}: "
                f"{assignment_grade.total_score}/{assignment_grade.max_score}"
            )

            return assignment_grade

        except Exception as e:
            logger.error(f"Error grading submission for {student_name}: {str(e)}")
            return self._create_error_grade(
                assignment_config, student_name, student_id, submission_file
            )

    def _parse_llm_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse LLM response to extract JSON
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Parsed JSON dictionary or None
        """
        try:
            # Try direct JSON parse first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # Try to find JSON object in the text
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            logger.error("Could not parse JSON from LLM response")
            logger.debug(f"Response text: {response_text[:500]}...")
            return None

    def _convert_to_assignment_grade(
        self,
        grading_data: Dict[str, Any],
        assignment_config: AssignmentConfig,
        student_name: str,
        student_id: Optional[str],
        submission_file: Optional[str],
    ) -> AssignmentGrade:
        """
        Convert parsed grading data to AssignmentGrade object
        
        Args:
            grading_data: Parsed JSON from LLM
            assignment_config: Assignment configuration
            student_name: Student name
            student_id: Student ID
            submission_file: Submission filename
            
        Returns:
            AssignmentGrade object
        """
        # Parse question grades
        question_grades = []
        for question_data in grading_data.get("questions", []):
            question_grade = QuestionGrade(
                question_id=question_data.get("question_id", "unknown"),
                score=float(question_data.get("score", 0)),
                max_score=float(question_data.get("max_score", 0)),
                reasoning=question_data.get("reasoning", "No reasoning provided"),
                feedback=question_data.get("feedback"),
                criteria_met=question_data.get("criteria_met"),
                criteria_missed=question_data.get("criteria_missed"),
                deductions=question_data.get("deductions"),
            )
            question_grades.append(question_grade)

        # Create AssignmentGrade
        assignment_grade = AssignmentGrade(
            student_name=student_name,
            student_id=student_id,
            submission_file=submission_file,
            assignment_id=assignment_config.assignment_id,
            assignment_name=assignment_config.assignment_name,
            total_score=float(grading_data.get("total_score", 0)),
            max_score=float(
                grading_data.get("max_score", assignment_config.total_points)
            ),
            questions=question_grades,
            overall_comment=grading_data.get("overall_comment"),
            strengths=grading_data.get("strengths"),
            areas_for_improvement=grading_data.get("areas_for_improvement"),
            llm_model=self.model_name,
        )

        return assignment_grade

    def _create_error_grade(
        self,
        assignment_config: AssignmentConfig,
        student_name: str,
        student_id: Optional[str],
        submission_file: Optional[str],
    ) -> AssignmentGrade:
        """
        Create a default error grade when grading fails
        
        Args:
            assignment_config: Assignment configuration
            student_name: Student name
            student_id: Student ID
            submission_file: Submission filename
            
        Returns:
            AssignmentGrade object with zero scores
        """
        question_grades = []
        for question in assignment_config.questions:
            question_grade = QuestionGrade(
                question_id=question.id,
                score=0.0,
                max_score=question.points,
                reasoning="Error: Unable to grade this question due to processing failure",
                feedback="Please contact instructor for manual review",
            )
            question_grades.append(question_grade)

        return AssignmentGrade(
            student_name=student_name,
            student_id=student_id,
            submission_file=submission_file,
            assignment_id=assignment_config.assignment_id,
            assignment_name=assignment_config.assignment_name,
            total_score=0.0,
            max_score=assignment_config.total_points or 0.0,
            questions=question_grades,
            overall_comment="Error processing submission - requires manual review",
            requires_human_review=True,
            review_reason="Processing error during automated grading",
            llm_model=self.model_name,
        )

    def grade_empty_submission(
        self,
        assignment_config: AssignmentConfig,
        student_name: str,
        student_id: Optional[str] = None,
        submission_file: Optional[str] = None,
    ) -> AssignmentGrade:
        """
        Create grade for empty or missing submission
        
        Args:
            assignment_config: Assignment configuration
            student_name: Student name
            student_id: Student ID
            submission_file: Submission filename
            
        Returns:
            AssignmentGrade object with zero scores
        """
        question_grades = []
        for question in assignment_config.questions:
            question_grade = QuestionGrade(
                question_id=question.id,
                score=0.0,
                max_score=question.points,
                reasoning="No submission or empty submission",
                feedback="No response provided for this question",
            )
            question_grades.append(question_grade)

        return AssignmentGrade(
            student_name=student_name,
            student_id=student_id,
            submission_file=submission_file,
            assignment_id=assignment_config.assignment_id,
            assignment_name=assignment_config.assignment_name,
            total_score=0.0,
            max_score=assignment_config.total_points or 0.0,
            questions=question_grades,
            overall_comment="No submission provided",
            llm_model=self.model_name,
        )

    @staticmethod
    def extract_student_name(filename: str) -> str:
        """
        Extract student name from filename
        
        Args:
            filename: Submission filename
            
        Returns:
            Extracted student name
        """
        # Remove file extension
        name = filename.rsplit(".", 1)[0]

        # Remove common patterns
        patterns_to_remove = [
            r"_CS\d+_",
            r"_HW\d+_",
            r"_LATE",
            r"_complete",
            r"_\d+$",
            r"\(\d+\)",
            r"-\d+$",
        ]

        for pattern in patterns_to_remove:
            name = re.sub(pattern, "", name, flags=re.IGNORECASE)

        # Split by underscore and take first part (usually the name)
        parts = name.split("_")
        if parts:
            return parts[0].strip()

        return name.strip()

    @staticmethod
    def extract_student_id(filename: str) -> str:
        """
        Extract student ID from filename
        
        Args:
            filename: Submission filename
            
        Returns:
            Extracted student ID or "unknown"
        """
        try:
            # Remove file extension
            name = filename.rsplit(".", 1)[0]

            # Split by underscore
            parts = name.split("_")

            if len(parts) >= 2:
                # Check if 2nd part is 'LATE', then use 3rd part as student ID
                if parts[1] == "LATE" and len(parts) >= 3:
                    return parts[2]
                else:
                    # Try to find a numeric ID
                    for part in parts[1:]:
                        if part.isdigit() and len(part) >= 4:  # Assume IDs are at least 4 digits
                            return part

            return "unknown"

        except Exception as e:
            logger.error(f"Error extracting student ID from {filename}: {str(e)}")
            return "unknown"

