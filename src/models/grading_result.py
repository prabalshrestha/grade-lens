"""
Data models for grading results using Pydantic
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


class QuestionGrade(BaseModel):
    """Grading result for a single question"""

    question_id: str = Field(..., description="Question identifier")
    score: float = Field(..., ge=0, description="Points earned")
    max_score: float = Field(..., gt=0, description="Maximum possible points")
    reasoning: str = Field(..., description="Detailed reasoning for the grade")
    feedback: Optional[str] = Field(
        default=None, description="Constructive feedback for the student"
    )

    # Additional metadata
    criteria_met: Optional[List[str]] = Field(
        default=None, description="List of rubric criteria met"
    )
    criteria_missed: Optional[List[str]] = Field(
        default=None, description="List of rubric criteria missed"
    )
    deductions: Optional[Dict[str, float]] = Field(
        default=None, description="Specific deductions with reasons"
    )

    @field_validator("score")
    @classmethod
    def validate_score(cls, v, info):
        """Ensure score doesn't exceed max_score"""
        if "max_score" in info.data and v > info.data["max_score"]:
            raise ValueError(f"Score {v} cannot exceed max_score {info.data['max_score']}")
        return v

    def get_percentage(self) -> float:
        """Calculate percentage score"""
        return (self.score / self.max_score * 100) if self.max_score > 0 else 0.0

    class Config:
        extra = "allow"


class AssignmentGrade(BaseModel):
    """Complete grading result for an assignment"""

    # Student information
    student_name: str = Field(..., description="Student name")
    student_id: Optional[str] = Field(default=None, description="Student ID")
    submission_file: Optional[str] = Field(
        default=None, description="Original submission filename"
    )

    # Assignment information
    assignment_id: str = Field(..., description="Assignment identifier")
    assignment_name: Optional[str] = Field(default=None)

    # Scores
    total_score: float = Field(..., ge=0, description="Total points earned")
    max_score: float = Field(..., gt=0, description="Maximum possible points")

    # Question-level grades
    questions: List[QuestionGrade] = Field(
        ..., min_length=1, description="Grades for individual questions"
    )

    # Overall feedback
    overall_comment: Optional[str] = Field(
        default=None, description="Overall comment on the submission"
    )
    strengths: Optional[List[str]] = Field(
        default=None, description="Identified strengths"
    )
    areas_for_improvement: Optional[List[str]] = Field(
        default=None, description="Areas needing improvement"
    )

    # Metadata
    graded_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp of grading",
    )
    graded_by: str = Field(default="AI", description="Grader identifier")
    llm_model: Optional[str] = Field(default=None, description="LLM model used")

    # Flags
    requires_human_review: bool = Field(
        default=False, description="Flag for human review needed"
    )
    review_reason: Optional[str] = Field(
        default=None, description="Reason for human review"
    )

    @field_validator("total_score")
    @classmethod
    def validate_total_score(cls, v, info):
        """Ensure total score doesn't exceed max_score"""
        if "max_score" in info.data and v > info.data["max_score"]:
            raise ValueError(
                f"Total score {v} cannot exceed max_score {info.data['max_score']}"
            )
        return v

    @field_validator("questions")
    @classmethod
    def validate_questions_sum(cls, v, info):
        """Check if question scores sum matches total_score"""
        if "total_score" in info.data:
            question_sum = sum(q.score for q in v)
            total = info.data["total_score"]
            # Allow small floating point differences
            if abs(question_sum - total) > 0.01:
                # This is just a warning, not an error
                import logging
                logging.warning(
                    f"Question scores sum ({question_sum}) doesn't match total_score ({total})"
                )
        return v

    def get_percentage(self) -> float:
        """Calculate overall percentage score"""
        return (self.total_score / self.max_score * 100) if self.max_score > 0 else 0.0

    def get_letter_grade(self, scale: Optional[Dict[str, float]] = None) -> str:
        """Calculate letter grade based on percentage"""
        if scale is None:
            # Default grading scale
            scale = {
                "A": 90.0,
                "B": 80.0,
                "C": 70.0,
                "D": 60.0,
                "F": 0.0,
            }

        percentage = self.get_percentage()
        for grade, threshold in sorted(scale.items(), key=lambda x: x[1], reverse=True):
            if percentage >= threshold:
                return grade
        return "F"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump()

    def to_flat_dict(self) -> Dict[str, Any]:
        """Convert to flattened dictionary for CSV export"""
        flat = {
            "student_name": self.student_name,
            "student_id": self.student_id,
            "submission_file": self.submission_file,
            "assignment_id": self.assignment_id,
            "assignment_name": self.assignment_name,
            "total_score": self.total_score,
            "max_score": self.max_score,
            "percentage": round(self.get_percentage(), 2),
            "letter_grade": self.get_letter_grade(),
            "overall_comment": self.overall_comment,
            "graded_at": self.graded_at,
            "graded_by": self.graded_by,
            "llm_model": self.llm_model,
            "requires_human_review": self.requires_human_review,
            "review_reason": self.review_reason,
        }

        # Add question-level data
        for question in self.questions:
            prefix = question.question_id
            flat[f"{prefix}_score"] = question.score
            flat[f"{prefix}_max_score"] = question.max_score
            flat[f"{prefix}_percentage"] = round(question.get_percentage(), 2)
            flat[f"{prefix}_reasoning"] = question.reasoning
            flat[f"{prefix}_feedback"] = question.feedback

        return flat

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssignmentGrade":
        """Create from dictionary"""
        return cls(**data)

    @classmethod
    def from_json_file(cls, file_path: str) -> "AssignmentGrade":
        """Load from JSON file"""
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_json_file(self, file_path: str):
        """Save to JSON file"""
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    class Config:
        extra = "allow"

