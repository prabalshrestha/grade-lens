from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from typing import Dict, List, Tuple
import json
import logging
from config import GRADING_CRITERIA, OPENAI_MODEL

logger = logging.getLogger(__name__)


class GradingAgent:
    """LangChain agent for grading submissions using OpenAI"""

    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=api_key,
            temperature=0.1,  # Low temperature for consistent grading
        )

        self.system_prompt = """You are an expert computer science grader. Your task is to grade student submissions for CS361 HW5 based on the following criteria:

ASSIGNMENT QUESTIONS:
Question 1 (15 points): Use the pumping lemma to prove the following language is not regular: 
L1 = {w over {a,b,c} | w has twice the number of a's as b's.}

Question 2 (15 points): Prove the language L2 defined below is either regular or not regular. 
L2 = {w over {a,b} | w has the same number of a's and b's, and |w| <=2}

GRADING CRITERIA (per question):
1. No submission for a question: 0 points
2. Student attempted the question: 7.5 points (half marks - 50% of 15 points)
3. Student completely solved the question correctly: 15 points (full marks)
4. Student got most of the solution right but complete solution is not correct: 14 points (deduct 1 point)

For each question in the submission, analyze:
- Whether the student attempted the question
- If attempted, whether the solution is correct
- If mostly correct but not complete, identify what's missing
- For Question 1: Check if they properly used pumping lemma with correct setup, contradiction, and conclusion
- For Question 2: Check if they correctly determined regularity and provided proper proof

Return your grading in the following JSON format:
{
    "question_1": {
        "score": 7.5,
        "reasoning": "Student attempted the pumping lemma proof but made errors in the contradiction step"
    },
    "question_2": {
        "score": 15,
        "reasoning": "Complete and correct solution showing L2 is regular with proper justification"
    }
}

Be fair but strict in your grading. If a student shows understanding but has minor errors, consider giving partial credit."""

    def grade_submission(
        self, student_name: str, submission_text: str, questions: List[str]
    ) -> Dict:
        """Grade a single submission"""
        try:
            # Create the grading prompt
            human_prompt = f"""
Student: {student_name}
Submission Content:
{submission_text}

Please grade this submission based on the questions and criteria provided.
Return only the JSON response with scores and reasoning for each question.
"""

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=human_prompt),
            ]

            response = self.llm.invoke(messages)
            grading_result = json.loads(response.content)

            return grading_result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {student_name}: {str(e)}")
            return self._create_default_grading(questions)
        except Exception as e:
            logger.error(f"Error grading submission for {student_name}: {str(e)}")
            return self._create_default_grading(questions)

    def _create_default_grading(self, questions: List[str]) -> Dict:
        """Create default grading when parsing fails"""
        default_grading = {}
        for question in questions:
            default_grading[question] = {
                "score": 0,
                "reasoning": "Error in grading - default score assigned",
            }
        return default_grading

    def calculate_total_score(self, grading_result: Dict) -> float:
        """Calculate total score from grading result"""
        total = 0.0
        for question, result in grading_result.items():
            if isinstance(result, dict) and "score" in result:
                total += result["score"]
        return total

    def extract_student_name(self, filename: str) -> str:
        """Extract student name from filename"""
        # Remove file extension
        name = filename.split(".")[0]
        # Remove common prefixes and suffixes
        name = name.replace("_CS361_HW5_FA25", "")
        name = name.replace("_LATE", "")
        name = name.replace("_complete", "")
        name = name.replace("_1", "")
        name = name.replace("_2", "")
        name = name.replace("(1)", "")
        name = name.replace("-1", "")
        name = name.replace("-2", "")

        # Split by underscore and take the first part (usually the name)
        parts = name.split("_")
        if len(parts) > 0:
            return parts[0]
        return name
