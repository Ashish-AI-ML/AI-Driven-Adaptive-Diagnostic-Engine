"""
Pydantic models for the TestResults collection.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class StudyPlanStep(BaseModel):
    """A single step in the personalized study plan."""
    focus: str
    action: str
    resource_type: str


class StudyPlan(BaseModel):
    """LLM-generated 3-step study plan."""
    step_1: StudyPlanStep
    step_2: StudyPlanStep
    step_3: StudyPlanStep


class TestResultDocument(BaseModel):
    """Immutable test result document created on session completion."""
    id: Optional[str] = Field(None, alias="_id")
    session_id: str
    student_id: str
    final_theta: float
    topics_attempted: List[str] = []
    topics_missed: List[str] = []
    difficulty_trajectory: List[float] = []
    accuracy_rate: float = 0.0
    total_questions: int = 0
    correct_count: int = 0
    study_plan: Optional[StudyPlan] = None
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
