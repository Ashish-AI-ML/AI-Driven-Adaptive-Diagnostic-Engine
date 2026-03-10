"""
Question router — retrieves next adaptive question.
GET /question/next
"""

from fastapi import APIRouter, HTTPException, Query

from app.database import get_database
from app.repositories.session_repo import SessionRepository
from app.repositories.question_repo import QuestionRepository
from app.engine.adaptive import AdaptiveEngine
from app.engine.irt import get_difficulty_band_label
from app.schemas.schemas import NextQuestionResponse

router = APIRouter(prefix="/question", tags=["Question"])


@router.get("/next", response_model=NextQuestionResponse)
async def get_next_question(session_id: str = Query(..., description="Active session ID")):
    """
    Retrieve the next adaptive question for the session.
    Difficulty is adapted based on the student's current ability estimate.
    Never exposes the correct answer.
    """
    db = get_database()
    session_repo = SessionRepository(db)
    question_repo = QuestionRepository(db)

    # Validate session
    session = await session_repo.find_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Session is '{session['status']}'. Cannot retrieve more questions."
        )

    # Select next question using adaptive engine
    engine = AdaptiveEngine(question_repo)
    question = await engine.select_next_question(session)

    if not question:
        raise HTTPException(
            status_code=404,
            detail="No more questions available. Question pool exhausted."
        )

    # Map difficulty to human-readable band
    difficulty_band = get_difficulty_band_label(question.get("difficulty", 0.5))

    return NextQuestionResponse(
        question_id=question["_id"],
        question_text=question["question_text"],
        options=question["options"],
        topic=question["topic"],
        difficulty_band=difficulty_band,
    )
