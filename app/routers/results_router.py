"""
Results router — retrieves test results and generates study plans.
GET /results/{session_id}
POST /plan/generate
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.database import get_database
from app.repositories.session_repo import SessionRepository
from app.repositories.results_repo import ResultsRepository
from app.engine.irt import get_theta_descriptor
from app.schemas.schemas import (
    TestResultResponse,
    GeneratePlanRequest,
    StudyPlanResponse,
)
from app.ai.plan_generator import PlanGenerator

router = APIRouter(tags=["Results"])


@router.get("/results/{session_id}", response_model=TestResultResponse)
async def get_results(session_id: str):
    """
    Retrieve final test results after session completion.
    Returns 404 if session not found, 400 if session still active.
    """
    db = get_database()
    session_repo = SessionRepository(db)
    results_repo = ResultsRepository(db)

    # Validate session exists
    session = await session_repo.find_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] == "active":
        raise HTTPException(
            status_code=400,
            detail="Session is still active. Complete the test before requesting results."
        )

    # Get test results
    result = await results_repo.find_by_session_id(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test results not found for this session")

    # Compute percentile descriptor
    percentile_estimate = get_theta_descriptor(result.get("final_theta", 0.0))

    return TestResultResponse(
        session_id=session_id,
        student_id=result.get("student_id", ""),
        final_theta=round(result.get("final_theta", 0.0), 4),
        accuracy_rate=round(result.get("accuracy_rate", 0.0), 4),
        total_questions=result.get("total_questions", 0),
        correct_count=result.get("correct_count", 0),
        topics_attempted=result.get("topics_attempted", []),
        topics_missed=result.get("topics_missed", []),
        difficulty_trajectory=result.get("difficulty_trajectory", []),
        percentile_estimate=percentile_estimate,
        completed_at=result.get("completed_at"),
    )


@router.post("/plan/generate", response_model=StudyPlanResponse)
async def generate_plan(request: GeneratePlanRequest):
    """
    Trigger LLM generation of a personalized study plan.
    Idempotent — if plan already generated, return cached version.
    """
    db = get_database()
    results_repo = ResultsRepository(db)

    # Get test results
    result = await results_repo.find_by_session_id(request.session_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Test results not found. Complete the test first."
        )

    # Check if plan already exists (idempotent)
    if result.get("study_plan"):
        return StudyPlanResponse(
            plan=result["study_plan"],
            generated_at=result.get("plan_generated_at", result.get("completed_at", datetime.utcnow())),
        )

    # Generate plan via AI module
    try:
        generator = PlanGenerator()
        plan = await generator.generate(result)

        # Store plan in TestResults
        await results_repo.update_study_plan(request.session_id, plan)

        return StudyPlanResponse(
            plan=plan,
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Study plan generation failed: {str(e)}. Test results are unaffected.",
            headers={"Retry-After": "30"},
        )
