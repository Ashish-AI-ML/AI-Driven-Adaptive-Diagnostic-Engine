"""
Session router — handles session lifecycle.
POST /session/start
"""

from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.repositories.session_repo import SessionRepository
from app.schemas.schemas import StartSessionRequest, StartSessionResponse
from app.config import settings

router = APIRouter(prefix="/session", tags=["Session"])


@router.post("/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """
    Initialize a new test session for a student.
    Idempotent — if student has an active session, return the existing one.
    """
    db = get_database()
    session_repo = SessionRepository(db)

    # Check for existing active session
    existing = await session_repo.find_active_by_student(request.student_id)
    if existing:
        return StartSessionResponse(
            session_id=existing["_id"],
            current_theta=existing["current_theta"],
            status=existing["status"],
            message="Existing active session found"
        )

    # Create new session
    session_data = {
        "student_id": request.student_id,
        "current_theta": settings.INITIAL_THETA,
        "target_difficulty": 0.5,
        "question_count": 0,
        "answered_ids": [],
        "responses": [],
        "status": "active",
    }

    session_id = await session_repo.create(session_data)

    return StartSessionResponse(
        session_id=session_id,
        current_theta=settings.INITIAL_THETA,
        status="active",
        message="Session initialized"
    )
