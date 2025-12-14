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
            prompt_builder = PromptBuilder(
                assignment_config, grading_mode=self.grading_mode
            )
            system_prompt = prompt_builder.build_system_prompt()
            user_prompt = prompt_builder.build_user_prompt(
                student_name, submission_text
            )

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

    def grade_single_question(
        self,
        question_config,
        answer_data: Dict[str, Any],
        assignment_config: AssignmentConfig,
        context: Optional[Dict[str, Any]] = None,
    ) -> QuestionGrade:
        """
        Grade a single question individually

        Args:
            question_config: QuestionConfig object for this question
            answer_data: Dictionary with answer text and metadata
            assignment_config: Full assignment configuration for context
            context: Optional additional context from other answers

        Returns:
            QuestionGrade object
        """
        try:
            # Extract answer text
            answer_text = answer_data.get("text", "")
            extracted_from_image = answer_data.get("extracted_from_image", False)
            extraction_notes = answer_data.get("extraction_notes", "")

            if not answer_text or answer_text.strip() == "No answer provided":
                # No answer provided
                return QuestionGrade(
                    question_id=question_config.id,
                    score=0.0,
                    max_score=question_config.points,
                    reasoning="No answer provided for this question",
                    feedback="Please ensure you answer all questions in future submissions",
                    extracted_from_image=extracted_from_image,
                    image_processing_notes=(
                        extraction_notes if extraction_notes else None
                    ),
                )

            # Build prompts for single question
            prompt_builder = PromptBuilder(
                assignment_config, grading_mode=self.grading_mode
            )

            # Build context string if provided
            context_str = None
            if context:
                context_parts = []
                for q_id, q_data in context.items():
                    if q_id != question_config.id:
                        text = q_data.get("text", "")[:200]
                        if text:
                            context_parts.append(f"{q_id}: {text}...")
                if context_parts:
                    context_str = "\n".join(
                        context_parts[:3]
                    )  # Limit to 3 other questions

            system_prompt, user_prompt = prompt_builder.build_single_question_prompt(
                question_config, answer_text, context_str
            )

            logger.debug(f"Grading question: {question_config.id}")

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
                logger.error(
                    f"Failed to parse response for question {question_config.id}"
                )
                return self._create_error_question_grade(
                    question_config, extracted_from_image, extraction_notes
                )

            # Create QuestionGrade object
            question_grade = QuestionGrade(
                question_id=grading_data.get("question_id", question_config.id),
                score=float(grading_data.get("score", 0)),
                max_score=float(grading_data.get("max_score", question_config.points)),
                reasoning=grading_data.get("reasoning", "No reasoning provided"),
                feedback=grading_data.get("feedback"),
                criteria_met=grading_data.get("criteria_met"),
                criteria_missed=grading_data.get("criteria_missed"),
                deductions=grading_data.get("deductions"),
                extracted_from_image=extracted_from_image,
                image_processing_notes=extraction_notes if extraction_notes else None,
            )

            logger.debug(
                f"Question {question_config.id}: {question_grade.score}/{question_grade.max_score}"
            )

            return question_grade

        except Exception as e:
            logger.error(f"Error grading question {question_config.id}: {str(e)}")
            return self._create_error_question_grade(
                question_config,
                answer_data.get("extracted_from_image", False),
                answer_data.get("extraction_notes", ""),
            )

    def grade_submission_with_extraction(
        self,
        assignment_config: AssignmentConfig,
        student_name: str,
        extracted_answers: Dict[str, Dict[str, Any]],
        student_id: Optional[str] = None,
        submission_file: Optional[str] = None,
    ) -> Optional[AssignmentGrade]:
        """
        Grade submission using pre-extracted answers (new multi-stage approach)

        Args:
            assignment_config: Assignment configuration
            student_name: Student's name
            extracted_answers: Dictionary of extracted answers by question ID
            student_id: Optional student ID
            submission_file: Optional submission filename

        Returns:
            AssignmentGrade object or None if grading fails
        """
        try:
            logger.info(f"Grading {student_name} with extracted answers")

            # Grade each question individually
            question_grades = []
            for question in assignment_config.questions:
                answer_data = extracted_answers.get(
                    question.id,
                    {
                        "text": "",
                        "extracted_from_image": False,
                        "extraction_notes": "Answer not found in extraction",
                    },
                )

                question_grade = self.grade_single_question(
                    question, answer_data, assignment_config, context=extracted_answers
                )
                question_grades.append(question_grade)

            # Calculate total score
            total_score = sum(q.score for q in question_grades)
            max_score = sum(q.max_score for q in question_grades)

            # Create AssignmentGrade (report will be added by ReportGenerator)
            assignment_grade = AssignmentGrade(
                student_name=student_name,
                student_id=student_id,
                submission_file=submission_file,
                assignment_id=assignment_config.assignment_id,
                assignment_name=assignment_config.assignment_name,
                total_score=total_score,
                max_score=max_score,
                questions=question_grades,
                overall_comment="",  # Will be filled by ReportGenerator
                llm_model=self.model_name,
            )

            logger.info(
                f"Successfully graded {student_name}: {total_score}/{max_score}"
            )

            return assignment_grade

        except Exception as e:
            logger.error(f"Error grading submission for {student_name}: {str(e)}")
            return self._create_error_grade(
                assignment_config, student_name, student_id, submission_file
            )

    def _create_error_question_grade(
        self,
        question_config,
        extracted_from_image: bool = False,
        extraction_notes: str = "",
    ) -> QuestionGrade:
        """
        Create an error grade for a single question

        Args:
            question_config: Question configuration
            extracted_from_image: Whether answer was from image
            extraction_notes: Notes about extraction

        Returns:
            QuestionGrade with error information
        """
        return QuestionGrade(
            question_id=question_config.id,
            score=0.0,
            max_score=question_config.points,
            reasoning="Error: Unable to grade this question due to processing failure",
            feedback="Please contact instructor for manual review",
            extracted_from_image=extracted_from_image,
            image_processing_notes=extraction_notes if extraction_notes else None,
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
            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL
            )
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

    def grade_single_question(
        self,
        question: "QuestionConfig",
        answer_data: Dict[str, Any],
        assignment_config: "AssignmentConfig",
        context: Optional[str] = None,
    ) -> Optional[QuestionGrade]:
        """
        Grade a single question individually

        Args:
            question: Question configuration
            answer_data: Dictionary with answer text, images, etc.
            assignment_config: Full assignment configuration for context
            context: Optional additional context from submission

        Returns:
            QuestionGrade object or None if grading fails
        """
        try:
            # Extract answer text
            answer_text = answer_data.get("text", "")
            extracted_from_image = answer_data.get("extracted_from_image", False)
            extraction_notes = answer_data.get("extraction_notes")

            if not answer_text or answer_text.strip() == "":
                logger.warning(f"No answer text for question {question.id}")
                answer_text = "No answer provided"

            # Build prompts using PromptBuilder
            prompt_builder = PromptBuilder(
                assignment_config, grading_mode=self.grading_mode
            )
            system_prompt, user_prompt = prompt_builder.build_single_question_prompt(
                question=question,
                student_answer=answer_text,
                context=context,
            )

            logger.debug(f"Grading question {question.id}")

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
                logger.error(f"Failed to parse LLM response for question {question.id}")
                return self._create_error_question_grade(
                    question, extracted_from_image, extraction_notes
                )

            # Convert to QuestionGrade object
            question_grade = QuestionGrade(
                question_id=grading_data.get("question_id", question.id),
                score=float(grading_data.get("score", 0)),
                max_score=float(grading_data.get("max_score", question.points)),
                reasoning=grading_data.get("reasoning", "No reasoning provided"),
                feedback=grading_data.get("feedback"),
                criteria_met=grading_data.get("criteria_met"),
                criteria_missed=grading_data.get("criteria_missed"),
                deductions=grading_data.get("deductions"),
                extracted_from_image=extracted_from_image,
                image_processing_notes=extraction_notes,
            )

            logger.info(
                f"Question {question.id}: {question_grade.score}/{question_grade.max_score}"
            )

            return question_grade

        except Exception as e:
            logger.error(f"Error grading question {question.id}: {str(e)}")
            return self._create_error_question_grade(
                question, extracted_from_image, extraction_notes
            )

    def _create_error_question_grade(
        self,
        question: "QuestionConfig",
        extracted_from_image: bool = False,
        extraction_notes: Optional[str] = None,
    ) -> QuestionGrade:
        """
        Create error grade for a single question

        Args:
            question: Question configuration
            extracted_from_image: Whether answer was from image
            extraction_notes: Notes about extraction

        Returns:
            QuestionGrade with error information
        """
        return QuestionGrade(
            question_id=question.id,
            score=0.0,
            max_score=question.points,
            reasoning="Error: Unable to grade this question due to processing failure",
            feedback="Please contact instructor for manual review",
            extracted_from_image=extracted_from_image,
            image_processing_notes=extraction_notes,
        )

    def grade_submission_with_extraction(
        self,
        assignment_config: "AssignmentConfig",
        student_name: str,
        extracted_answers: Dict[str, Dict[str, Any]],
        student_id: Optional[str] = None,
        submission_file: Optional[str] = None,
    ) -> Optional[AssignmentGrade]:
        """
        Grade a submission using pre-extracted answers (new multi-stage pipeline)

        Args:
            assignment_config: Assignment configuration
            student_name: Student's name
            extracted_answers: Dictionary mapping question_id to answer data
            student_id: Optional student ID
            submission_file: Optional submission filename

        Returns:
            AssignmentGrade object or None if grading fails
        """
        try:
            logger.debug(
                f"Grading submission for {student_name} with extracted answers"
            )

            # Grade each question individually
            question_grades = []

            for question in assignment_config.questions:
                answer_data = extracted_answers.get(
                    question.id,
                    {
                        "text": "",
                        "extracted_from_image": False,
                        "extraction_notes": "Question not found in extraction",
                    },
                )

                # Get context from other answers (optional)
                context = None
                if len(assignment_config.questions) > 1:
                    other_answers = [
                        f"{q_id}: {data.get('text', '')[:100]}..."
                        for q_id, data in extracted_answers.items()
                        if q_id != question.id
                    ]
                    context = "\n".join(other_answers[:3])  # Limit context

                # Grade the question
                question_grade = self.grade_single_question(
                    question=question,
                    answer_data=answer_data,
                    assignment_config=assignment_config,
                    context=context,
                )

                if question_grade:
                    question_grades.append(question_grade)
                else:
                    # Create error grade if grading failed
                    question_grades.append(
                        self._create_error_question_grade(
                            question,
                            answer_data.get("extracted_from_image", False),
                            answer_data.get("extraction_notes"),
                        )
                    )

            # Calculate total score
            total_score = sum(q.score for q in question_grades)
            max_score = sum(q.max_score for q in question_grades)

            # Create AssignmentGrade (report generation will be done separately)
            assignment_grade = AssignmentGrade(
                student_name=student_name,
                student_id=student_id,
                submission_file=submission_file,
                assignment_id=assignment_config.assignment_id,
                assignment_name=assignment_config.assignment_name,
                total_score=total_score,
                max_score=max_score,
                questions=question_grades,
                overall_comment=None,  # Will be set by report generator
                llm_model=self.model_name,
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
                        if (
                            part.isdigit() and len(part) >= 4
                        ):  # Assume IDs are at least 4 digits
                            return part

            return "unknown"

        except Exception as e:
            logger.error(f"Error extracting student ID from {filename}: {str(e)}")
            return "unknown"
