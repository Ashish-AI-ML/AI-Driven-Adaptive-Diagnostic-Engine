"""
Request/Response schemas for all API endpoints.
Separated from database models for clean API contracts.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ─── Session Schemas ───────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    student_id: str
    subject: Optional[str] = None


class StartSessionResponse(BaseModel):
    session_id: str
    current_theta: float
    status: str
    message: str


# ─── Question Schemas ──────────────────────────────────────────────

class NextQuestionResponse(BaseModel):
    question_id: str
    question_text: str
    options: List[str]
    topic: str
    difficulty_band: str  # 'Easy', 'Medium', 'Hard'


# ─── Answer Schemas ────────────────────────────────────────────────

class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    selected_answer: str = Field(..., pattern=r"^[A-D]$")
    time_taken_seconds: Optional[int] = None


class SubmitAnswerResponse(BaseModel):
    correct: bool
    updated_theta: float
    questions_remaining: int
    session_status: str


# ─── Results Schemas ───────────────────────────────────────────────

class TestResultResponse(BaseModel):
    session_id: str
    student_id: str
    final_theta: float
    accuracy_rate: float
    total_questions: int
    correct_count: int
    topics_attempted: List[str]
    topics_missed: List[str]
    difficulty_trajectory: List[float]
    percentile_estimate: str
    completed_at: Optional[datetime] = None


# ─── Plan Schemas ──────────────────────────────────────────────────

class GeneratePlanRequest(BaseModel):
    session_id: str


class StudyPlanStepSchema(BaseModel):
    focus: str
    action: str
    resource_type: str


class StudyPlanResponse(BaseModel):
    plan: dict
    generated_at: datetime


# ─── Health Schemas ────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime


# ─── Error Schema ──────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
