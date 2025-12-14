"""
Data models for assignment configuration using Pydantic
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
import json


class RubricConfig(BaseModel):
    """Grading rubric configuration"""

    # Criteria for grading (e.g., ["correct_setup", "valid_proof", "clear_explanation"])
    criteria: Optional[List[str]] = Field(
        default=None, description="List of grading criteria"
    )

    # Partial credit rules
    no_submission: float = Field(default=0.0, description="Points for no submission")
    attempted: Optional[float] = Field(
        default=None, description="Points for attempting the question"
    )
    mostly_correct: Optional[float] = Field(
        default=None, description="Points for mostly correct answer"
    )
    correct: Optional[float] = Field(
        default=None, description="Points for fully correct answer"
    )

    # Additional grading instructions
    instructions: Optional[str] = Field(
        default=None, description="Additional grading instructions"
    )

    # Custom scoring rules (flexible for different grading schemes)
    custom_scoring: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom scoring rules"
    )

    class Config:
        extra = "allow"  # Allow additional fields for flexibility


class QuestionConfig(BaseModel):
    """Configuration for a single question"""

    id: str = Field(..., description="Unique identifier for the question")
    text: str = Field(..., description="Question text/prompt")
    points: float = Field(..., gt=0, description="Maximum points for this question")

    # Optional answer key
    answer_key: Optional[str] = Field(
        default=None, description="Model answer or answer key"
    )

    # Question-specific rubric (overrides general rubric)
    rubric: Optional[RubricConfig] = Field(
        default=None, description="Question-specific rubric"
    )

    # Additional metadata
    question_type: Optional[str] = Field(
        default="essay", description="Type of question (essay, short_answer, etc.)"
    )
    tags: Optional[List[str]] = Field(default=None, description="Question tags")

    class Config:
        extra = "allow"


class AssignmentConfig(BaseModel):
    """Complete assignment configuration"""

    # Basic metadata
    assignment_id: str = Field(..., description="Unique assignment identifier")
    assignment_name: str = Field(..., description="Human-readable assignment name")
    course_code: Optional[str] = Field(default=None, description="Course code")
    term: Optional[str] = Field(default=None, description="Academic term")

    # Questions
    questions: List[QuestionConfig] = Field(
        ..., min_length=1, description="List of questions in the assignment"
    )

    # General rubric (applies to all questions unless overridden)
    general_rubric: Optional[RubricConfig] = Field(
        default=None, description="General rubric for all questions"
    )

    # Answer key (for entire assignment, separate from per-question answer keys)
    answer_key_text: Optional[str] = Field(
        default=None, description="Complete answer key text (loaded from PDF)"
    )

    # Additional configuration
    total_points: Optional[float] = Field(
        default=None, description="Total points (auto-calculated if not provided)"
    )
    grading_instructions: Optional[str] = Field(
        default=None, description="General grading instructions"
    )
    allow_partial_credit: bool = Field(
        default=True, description="Whether to allow partial credit"
    )

    # Metadata
    created_by: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)
    version: str = Field(default="1.0")

    @field_validator("total_points", mode="before")
    @classmethod
    def calculate_total_points(cls, v, info):
        """Auto-calculate total points if not provided"""
        if v is None and "questions" in info.data:
            return sum(q.points for q in info.data["questions"])
        return v

    def get_question_rubric(self, question_id: str) -> Optional[RubricConfig]:
        """Get rubric for a specific question (question-specific or general)"""
        for question in self.questions:
            if question.id == question_id:
                return question.rubric or self.general_rubric
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssignmentConfig":
        """Create from dictionary"""
        return cls(**data)

    @classmethod
    def from_json_file(cls, file_path: str) -> "AssignmentConfig":
        """Load configuration from JSON file"""
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_json_file(self, file_path: str):
        """Save configuration to JSON file"""
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    class Config:
        extra = "allow"

