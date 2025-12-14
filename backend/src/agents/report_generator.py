"""
Report Generator - Synthesizes individual question grades into comprehensive final assessment
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from statistics import mean, median

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..models.grading_result import QuestionGrade
from ..models.assignment_config import AssignmentConfig

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates comprehensive assessment reports from individual question grades"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
    ):
        """
        Initialize the report generator

        Args:
            api_key: OpenAI API key
            model: Model name
            temperature: Temperature for generation (slightly higher for creative feedback)
        """
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
        )
        self.model_name = model

    def generate_report(
        self,
        question_grades: List[QuestionGrade],
        assignment_config: AssignmentConfig,
        student_name: str,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive report from individual question grades

        Args:
            question_grades: List of graded questions
            assignment_config: Assignment configuration
            student_name: Name of the student

        Returns:
            Dictionary with report data including:
            - total_score, max_score
            - overall_comment
            - strengths, areas_for_improvement
            - requires_human_review, review_reason
        """
        logger.info(f"Generating report for {student_name}")

        try:
            # Calculate statistics
            stats = self._calculate_statistics(question_grades)

            # Identify strengths and weaknesses
            strengths, weaknesses = self._identify_strengths_and_weaknesses(
                question_grades, assignment_config
            )

            # Generate overall comment using LLM
            overall_comment = self._generate_overall_comment(
                question_grades=question_grades,
                assignment_config=assignment_config,
                stats=stats,
                strengths=strengths,
                weaknesses=weaknesses,
            )

            # Determine if human review is needed
            requires_review, review_reason = self._check_human_review_needed(
                question_grades, stats
            )

            report_data = {
                "total_score": stats["total_score"],
                "max_score": stats["max_score"],
                "overall_comment": overall_comment,
                "strengths": strengths,
                "areas_for_improvement": weaknesses,
                "requires_human_review": requires_review,
                "review_reason": review_reason,
            }

            logger.info(
                f"Report generated: {stats['total_score']}/{stats['max_score']} ({stats['percentage']:.1f}%)"
            )

            return report_data

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)

            # Return basic report on error
            total_score = sum(q.score for q in question_grades)
            max_score = sum(q.max_score for q in question_grades)

            return {
                "total_score": total_score,
                "max_score": max_score,
                "overall_comment": "Report generation encountered an error. Please review individual question feedback.",
                "strengths": None,
                "areas_for_improvement": None,
                "requires_human_review": True,
                "review_reason": f"Report generation error: {str(e)}",
            }

    def _calculate_statistics(
        self, question_grades: List[QuestionGrade]
    ) -> Dict[str, Any]:
        """
        Calculate statistical summary of question grades

        Args:
            question_grades: List of question grades

        Returns:
            Dictionary with statistics
        """
        if not question_grades:
            return {
                "total_score": 0.0,
                "max_score": 0.0,
                "percentage": 0.0,
                "avg_question_percentage": 0.0,
                "median_question_percentage": 0.0,
                "num_perfect": 0,
                "num_zero": 0,
            }

        total_score = sum(q.score for q in question_grades)
        max_score = sum(q.max_score for q in question_grades)
        percentage = (total_score / max_score * 100) if max_score > 0 else 0.0

        # Calculate per-question percentages
        question_percentages = [q.get_percentage() for q in question_grades]

        # Count perfect and zero scores
        num_perfect = sum(1 for q in question_grades if q.score == q.max_score)
        num_zero = sum(1 for q in question_grades if q.score == 0)

        return {
            "total_score": total_score,
            "max_score": max_score,
            "percentage": percentage,
            "avg_question_percentage": (
                mean(question_percentages) if question_percentages else 0.0
            ),
            "median_question_percentage": (
                median(question_percentages) if question_percentages else 0.0
            ),
            "num_questions": len(question_grades),
            "num_perfect": num_perfect,
            "num_zero": num_zero,
        }

    def _identify_strengths_and_weaknesses(
        self,
        question_grades: List[QuestionGrade],
        assignment_config: AssignmentConfig,
    ) -> Tuple[List[str], List[str]]:
        """
        Identify student's strengths and areas for improvement

        Args:
            question_grades: List of question grades
            assignment_config: Assignment configuration

        Returns:
            Tuple of (strengths list, weaknesses list)
        """
        strengths = []
        weaknesses = []

        # Analyze each question
        for q_grade in question_grades:
            percentage = q_grade.get_percentage()

            # Find the question config
            question_config = None
            for q in assignment_config.questions:
                if q.id == q_grade.question_id:
                    question_config = q
                    break

            question_label = (
                question_config.text[:50] if question_config else q_grade.question_id
            )

            # Strong performance (>= 90%)
            if percentage >= 90:
                if q_grade.criteria_met:
                    strengths.append(
                        f"{question_label}: Excellent work - {', '.join(q_grade.criteria_met[:2])}"
                    )
                else:
                    strengths.append(
                        f"{question_label}: Excellent performance ({percentage:.0f}%)"
                    )

            # Good performance (75-89%)
            elif percentage >= 75:
                if q_grade.criteria_met and len(q_grade.criteria_met) > 0:
                    strengths.append(
                        f"{question_label}: Strong understanding demonstrated"
                    )

            # Needs improvement (< 60%)
            elif percentage < 60:
                if q_grade.criteria_missed:
                    weaknesses.append(
                        f"{question_label}: {', '.join(q_grade.criteria_missed[:2])}"
                    )
                else:
                    weaknesses.append(
                        f"{question_label}: Significant improvement needed ({percentage:.0f}%)"
                    )

            # Moderate performance (60-74%)
            elif percentage < 75:
                if q_grade.criteria_missed and len(q_grade.criteria_missed) > 0:
                    weaknesses.append(
                        f"{question_label}: Minor improvements needed - {q_grade.criteria_missed[0]}"
                    )

        # Limit to most relevant items
        strengths = strengths[:5]
        weaknesses = weaknesses[:5]

        return strengths, weaknesses

    def _generate_overall_comment(
        self,
        question_grades: List[QuestionGrade],
        assignment_config: AssignmentConfig,
        stats: Dict[str, Any],
        strengths: List[str],
        weaknesses: List[str],
    ) -> str:
        """
        Generate overall comment using LLM

        Args:
            question_grades: List of question grades
            assignment_config: Assignment configuration
            stats: Statistics dictionary
            strengths: Identified strengths
            weaknesses: Identified weaknesses

        Returns:
            Overall comment string
        """
        try:
            # Build summary of question performance
            question_summary = []
            for q_grade in question_grades:
                question_summary.append(
                    f"- {q_grade.question_id}: {q_grade.score}/{q_grade.max_score} "
                    f"({q_grade.get_percentage():.0f}%) - {q_grade.reasoning[:100]}..."
                )

            question_summary_str = "\n".join(question_summary)

            system_prompt = """You are an experienced educator providing constructive feedback on student assignments.
Generate a concise overall comment (2-4 sentences) that:
1. Acknowledges the student's overall performance
2. Highlights key strengths
3. Points out main areas for improvement
4. Encourages continued learning

Be constructive, specific, and encouraging. Focus on learning outcomes."""

            user_prompt = f"""Assignment: {assignment_config.assignment_name}
Total Score: {stats['total_score']}/{stats['max_score']} ({stats['percentage']:.1f}%)

Question Performance:
{question_summary_str}

Strengths:
{chr(10).join('- ' + s for s in strengths) if strengths else '- None identified'}

Areas for Improvement:
{chr(10).join('- ' + w for w in weaknesses) if weaknesses else '- None identified'}

Generate an overall comment for this student's work."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = self.llm.invoke(messages)
            overall_comment = response.content.strip()

            # Remove quotes if LLM added them
            if overall_comment.startswith('"') and overall_comment.endswith('"'):
                overall_comment = overall_comment[1:-1]

            return overall_comment

        except Exception as e:
            logger.error(f"Error generating overall comment: {str(e)}")

            # Fallback to template-based comment
            percentage = stats["percentage"]

            if percentage >= 90:
                return f"Excellent work! You demonstrated strong understanding across all questions. Score: {stats['total_score']}/{stats['max_score']} ({percentage:.1f}%)"
            elif percentage >= 80:
                return f"Very good work overall. You showed solid understanding with room for minor improvements. Score: {stats['total_score']}/{stats['max_score']} ({percentage:.1f}%)"
            elif percentage >= 70:
                return f"Good effort. You demonstrated understanding of key concepts, but some areas need more attention. Score: {stats['total_score']}/{stats['max_score']} ({percentage:.1f}%)"
            elif percentage >= 60:
                return f"Satisfactory work. Please review the feedback and work on strengthening your understanding. Score: {stats['total_score']}/{stats['max_score']} ({percentage:.1f}%)"
            else:
                return f"This assignment needs significant improvement. Please review the detailed feedback and seek help on challenging topics. Score: {stats['total_score']}/{stats['max_score']} ({percentage:.1f}%)"

    def _check_human_review_needed(
        self,
        question_grades: List[QuestionGrade],
        stats: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if human review is needed

        Args:
            question_grades: List of question grades
            stats: Statistics dictionary

        Returns:
            Tuple of (requires_review flag, reason)
        """
        reasons = []

        # Check for unusual patterns
        if stats["num_zero"] > len(question_grades) / 2:
            reasons.append("More than half of questions received zero points")

        if stats["percentage"] > 95 and stats["num_perfect"] < len(question_grades):
            reasons.append("Near-perfect score with some deductions - verify grading")

        # Check for image processing issues
        image_issues = sum(
            1
            for q in question_grades
            if q.extracted_from_image
            and "error" in (q.image_processing_notes or "").lower()
        )
        if image_issues > 0:
            reasons.append(f"{image_issues} question(s) had image extraction issues")

        # Check for low confidence or unclear grading
        unclear_grading = sum(
            1 for q in question_grades if q.score == 0 and len(q.reasoning) < 50
        )
        if unclear_grading > 0:
            reasons.append(
                f"{unclear_grading} question(s) received zero with minimal explanation"
            )

        if reasons:
            return True, "; ".join(reasons)

        return False, None
