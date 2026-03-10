"""
Pydantic models for the UserSession collection.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ResponseRecord(BaseModel):
    """Individual response within a session."""
    question_id: str
    selected_answer: str
    correct_answer: str
    correct: bool
    theta_before: float
    theta_after: float
    time_taken_seconds: Optional[int] = None
    difficulty: float
    topic: str


class UserSessionDocument(BaseModel):
    """Full session document as stored in MongoDB."""
    id: Optional[str] = Field(None, alias="_id")
    student_id: str
    current_theta: float = 0.0
    target_difficulty: float = 0.5
    question_count: int = 0
    answered_ids: List[str] = []
    responses: List[ResponseRecord] = []
    status: SessionStatus = SessionStatus.ACTIVE
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        use_enum_values = True
