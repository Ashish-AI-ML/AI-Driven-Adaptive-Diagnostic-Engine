"""
Adaptive Engine — orchestrates question selection, answer processing, and stopping.
Pure business logic. Has zero knowledge of HTTP or database internals.
Uses injected repository for data access.
"""

from typing import Optional
from app.engine.irt import (
    update_theta,
    theta_to_difficulty,
    difficulty_to_theta,
    compute_sem,
    get_difficulty_band_label,
)
from app.config import settings
from app.repositories.question_repo import QuestionRepository


class AdaptiveEngine:
    """
    The mathematical core of the adaptive testing system.
    Computes ability estimates and determines the next question.
    """

    def __init__(self, question_repo: QuestionRepository):
        self.question_repo = question_repo

    async def select_next_question(self, session: dict) -> Optional[dict]:
        """
        Select the next question based on the current session state.

        Strategy:
        1. Use target_difficulty from session (derived from theta).
        2. Query questions within the difficulty band, excluding answered IDs.
        3. QuestionRepository handles fallback widening internally.

        Args:
            session: Current session document from MongoDB.

        Returns:
            Question document, or None if no questions available.
        """
        target_difficulty = session.get("target_difficulty", 0.5)
        answered_ids = session.get("answered_ids", [])

        question = await self.question_repo.find_by_difficulty_band(
            target_difficulty=target_difficulty,
            excluded_ids=answered_ids,
        )

        return question

    def process_answer(
        self,
        session: dict,
        question: dict,
        selected_answer: str,
        time_taken_seconds: Optional[int] = None
    ) -> dict:
        """
        Process a student's answer: evaluate correctness, update theta, compute
        new target difficulty, and build response record.

        Args:
            session: Current session document.
            question: The question that was answered.
            selected_answer: The student's selected answer ('A', 'B', 'C', or 'D').
            time_taken_seconds: Optional time taken to answer (for analytics).

        Returns:
            Dictionary with:
                - correct (bool)
                - new_theta (float)
                - new_target_difficulty (float)
                - new_question_count (int)
                - response_record (dict)
                - should_stop (bool)
                - session_status (str)
        """
        # Evaluate correctness
        correct = selected_answer.upper() == question["correct_answer"].upper()

        # Current state
        current_theta = session.get("current_theta", settings.INITIAL_THETA)
        question_count = session.get("question_count", 0)

        # IRT parameters — map difficulty from [0.1, 1.0] to theta scale for b
        a = question.get("discrimination", 1.0)
        b = difficulty_to_theta(question.get("difficulty", 0.5))
        c = question.get("guessing", 0.25)

        # Update theta using IRT MLE step
        new_theta = update_theta(current_theta, a, b, c, correct)

        # Compute new target difficulty
        new_target_difficulty = theta_to_difficulty(new_theta)

        # Increment question count
        new_question_count = question_count + 1

        # Build response record
        response_record = {
            "question_id": question["_id"],
            "selected_answer": selected_answer,
            "correct_answer": question["correct_answer"],
            "correct": correct,
            "theta_before": current_theta,
            "theta_after": new_theta,
            "time_taken_seconds": time_taken_seconds,
            "difficulty": question.get("difficulty", 0.5),
            "discrimination": a,
            "guessing": c,
            "topic": question.get("topic", "Unknown"),
        }

        # Check stopping criterion
        all_responses = session.get("responses", []) + [response_record]
        should_stop = self._should_stop(new_question_count, all_responses)

        session_status = "completed" if should_stop else "active"

        return {
            "correct": correct,
            "new_theta": new_theta,
            "new_target_difficulty": new_target_difficulty,
            "new_question_count": new_question_count,
            "response_record": response_record,
            "should_stop": should_stop,
            "session_status": session_status,
        }

    def _should_stop(self, question_count: int, responses: list) -> bool:
        """
        Check if the test should end.

        Stopping criteria:
        1. Maximum questions reached (10)
        2. SEM falls below threshold (0.3), indicating sufficient confidence

        Args:
            question_count: Number of questions answered so far.
            responses: All response records including the current one.

        Returns:
            True if the test should stop.
        """
        # Criterion 1: Maximum questions
        if question_count >= settings.MAX_QUESTIONS:
            return True

        # Criterion 2: SEM threshold (only check after minimum 5 questions)
        if question_count >= 5:
            sem = compute_sem(responses)
            if sem < settings.SEM_THRESHOLD:
                return True

        return False

    @staticmethod
    def build_test_result(session: dict) -> dict:
        """
        Build a TestResult document from a completed session.

        Args:
            session: Completed session document.

        Returns:
            Dictionary ready to be inserted into test_results collection.
        """
        responses = session.get("responses", [])

        # Aggregate topics
        topics_attempted = list(set(r.get("topic", "") for r in responses))
        topics_missed = list(set(
            r.get("topic", "") for r in responses if not r.get("correct", False)
        ))

        # Difficulty trajectory
        difficulty_trajectory = [r.get("difficulty", 0.5) for r in responses]

        # Accuracy
        correct_count = sum(1 for r in responses if r.get("correct", False))
        total = len(responses)
        accuracy_rate = correct_count / total if total > 0 else 0.0

        return {
            "session_id": session.get("_id", ""),
            "student_id": session.get("student_id", ""),
            "final_theta": session.get("current_theta", 0.0),
            "topics_attempted": topics_attempted,
            "topics_missed": topics_missed,
            "difficulty_trajectory": difficulty_trajectory,
            "accuracy_rate": round(accuracy_rate, 4),
            "total_questions": total,
            "correct_count": correct_count,
        }
