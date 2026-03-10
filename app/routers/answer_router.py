"""
Answer router — processes submitted answers.
POST /answer/submit
"""

from fastapi import APIRouter, HTTPException

from app.database import get_database
from app.repositories.session_repo import SessionRepository
from app.repositories.question_repo import QuestionRepository
from app.repositories.results_repo import ResultsRepository
from app.engine.adaptive import AdaptiveEngine
from app.schemas.schemas import SubmitAnswerRequest, SubmitAnswerResponse
from app.config import settings

router = APIRouter(prefix="/answer", tags=["Answer"])


@router.post("/submit", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """
    Submit an answer and trigger ability score update.

    Validates:
    - Session exists and is active
    - Question exists
    - Answer hasn't already been submitted for this question (409 Conflict)
    - selected_answer is one of [A, B, C, D]
    """
    db = get_database()
    session_repo = SessionRepository(db)
    question_repo = QuestionRepository(db)
    results_repo = ResultsRepository(db)

    # Validate session
    session = await session_repo.find_by_id(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Session is '{session['status']}'. Cannot submit answers."
        )

    # Validate question
    question = await question_repo.find_by_id(request.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check for duplicate submission (409 Conflict)
    if request.question_id in session.get("answered_ids", []):
        # Find the existing response for this question
        existing = next(
            (r for r in session.get("responses", [])
             if r.get("question_id") == request.question_id),
            None
        )
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Answer already submitted for this question",
                "existing_result": {
                    "correct": existing["correct"] if existing else None,
                    "theta_after": existing["theta_after"] if existing else None,
                }
            }
        )

    # Process answer through adaptive engine
    engine = AdaptiveEngine(question_repo)
    result = engine.process_answer(
        session=session,
        question=question,
        selected_answer=request.selected_answer,
        time_taken_seconds=request.time_taken_seconds,
    )

    # Update session in MongoDB
    await session_repo.update_after_answer(
        session_id=request.session_id,
        new_theta=result["new_theta"],
        target_difficulty=result["new_target_difficulty"],
        question_count=result["new_question_count"],
        answered_id=request.question_id,
        response_record=result["response_record"],
        status=result["session_status"],
    )

    # If test should stop, create the TestResult document
    if result["should_stop"]:
        # Re-fetch updated session for building test result
        updated_session = await session_repo.find_by_id(request.session_id)
        test_result = AdaptiveEngine.build_test_result(updated_session)
        await results_repo.create(test_result)

    questions_remaining = settings.MAX_QUESTIONS - result["new_question_count"]
    if questions_remaining < 0:
        questions_remaining = 0

    return SubmitAnswerResponse(
        correct=result["correct"],
        updated_theta=round(result["new_theta"], 4),
        questions_remaining=questions_remaining,
        session_status=result["session_status"],
    )
