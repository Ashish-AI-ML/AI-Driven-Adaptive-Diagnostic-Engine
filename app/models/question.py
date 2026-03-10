"""
Pydantic models for the Questions collection.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class QuestionDocument(BaseModel):
    """Full question document as stored in MongoDB."""
    id: Optional[str] = Field(None, alias="_id")
    question_text: str
    options: List[str] = Field(..., min_length=4, max_length=4)
    correct_answer: str = Field(..., pattern=r"^[A-D]$")
    difficulty: float = Field(..., ge=0.1, le=1.0)
    discrimination: float = Field(..., ge=0.5, le=3.0)
    guessing: float = Field(..., ge=0.0, le=0.35)
    topic: str
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class QuestionResponse(BaseModel):
    """API response model — never exposes correct_answer."""
    question_id: str
    question_text: str
    options: List[str]
    topic: str
    difficulty_band: str  # 'Easy', 'Medium', 'Hard'
