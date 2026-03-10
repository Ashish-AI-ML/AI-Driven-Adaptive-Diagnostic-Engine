"""
Tests for the Adaptive Engine — question selection, answer processing, stopping.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.engine.adaptive import AdaptiveEngine
from app.engine.irt import theta_to_difficulty
from app.config import settings


class MockQuestionRepo:
    """Mock question repository for testing without MongoDB."""

    def __init__(self, questions=None):
        self.questions = questions or []
        self.last_query_params = {}

    async def find_by_difficulty_band(self, target_difficulty, excluded_ids, topic=None):
        """Return the first question not in excluded_ids."""
        self.last_query_params = {
            "target_difficulty": target_difficulty,
            "excluded_ids": excluded_ids,
            "topic": topic,
        }
        for q in self.questions:
            if q["_id"] not in excluded_ids:
                return q
        return None


# Sample questions for testing
SAMPLE_QUESTIONS = [
    {
        "_id": "q1",
        "question_text": "Test question 1",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "A",
        "difficulty": 0.3,
        "discrimination": 1.0,
        "guessing": 0.25,
        "topic": "Algebra",
    },
    {
        "_id": "q2",
        "question_text": "Test question 2",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "B",
        "difficulty": 0.5,
        "discrimination": 1.5,
        "guessing": 0.20,
        "topic": "Vocabulary",
    },
    {
        "_id": "q3",
        "question_text": "Test question 3",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "C",
        "difficulty": 0.8,
        "discrimination": 2.0,
        "guessing": 0.15,
        "topic": "Reading Comprehension",
    },
]


class TestAdaptiveEngine:
    """Tests for the AdaptiveEngine class."""

    @pytest.mark.asyncio
    async def test_select_next_question(self):
        """Engine should select a question from the repo."""
        repo = MockQuestionRepo(SAMPLE_QUESTIONS)
        engine = AdaptiveEngine(repo)

        session = {
            "target_difficulty": 0.5,
            "answered_ids": [],
        }
        question = await engine.select_next_question(session)
        assert question is not None
        assert question["_id"] in ["q1", "q2", "q3"]

    @pytest.mark.asyncio
    async def test_excludes_answered_questions(self):
        """Engine should not return already-answered questions."""
        repo = MockQuestionRepo(SAMPLE_QUESTIONS)
        engine = AdaptiveEngine(repo)

        session = {
            "target_difficulty": 0.5,
            "answered_ids": ["q1"],
        }
        question = await engine.select_next_question(session)
        assert question is not None
        assert question["_id"] != "q1"

    @pytest.mark.asyncio
    async def test_no_questions_available(self):
        """Engine should return None when all questions are answered."""
        repo = MockQuestionRepo(SAMPLE_QUESTIONS)
        engine = AdaptiveEngine(repo)

        session = {
            "target_difficulty": 0.5,
            "answered_ids": ["q1", "q2", "q3"],
        }
        question = await engine.select_next_question(session)
        assert question is None

    def test_process_correct_answer(self):
        """Correct answer should increase theta."""
        repo = MockQuestionRepo()
        engine = AdaptiveEngine(repo)

        session = {
            "_id": "session1",
            "current_theta": 0.0,
            "question_count": 0,
            "responses": [],
        }
        result = engine.process_answer(session, SAMPLE_QUESTIONS[1], "B")
        assert result["correct"] is True
        assert result["new_theta"] > 0.0
        assert result["new_question_count"] == 1

    def test_process_incorrect_answer(self):
        """Incorrect answer should decrease theta."""
        repo = MockQuestionRepo()
        engine = AdaptiveEngine(repo)

        session = {
            "_id": "session1",
            "current_theta": 0.0,
            "question_count": 0,
            "responses": [],
        }
        result = engine.process_answer(session, SAMPLE_QUESTIONS[1], "A")  # Wrong
        assert result["correct"] is False
        assert result["new_theta"] < 0.0

    def test_stopping_at_max_questions(self):
        """Engine should stop after MAX_QUESTIONS."""
        repo = MockQuestionRepo()
        engine = AdaptiveEngine(repo)

        session = {
            "_id": "session1",
            "current_theta": 0.0,
            "question_count": settings.MAX_QUESTIONS - 1,
            "responses": [
                {"theta_after": 0.0, "discrimination": 1.0, "difficulty": 0.5, "guessing": 0.25}
            ] * (settings.MAX_QUESTIONS - 1),
        }
        result = engine.process_answer(session, SAMPLE_QUESTIONS[0], "A")
        assert result["should_stop"] is True
        assert result["session_status"] == "completed"

    def test_not_stopping_before_max(self):
        """Engine should NOT stop before reaching MAX_QUESTIONS (if SEM is high)."""
        repo = MockQuestionRepo()
        engine = AdaptiveEngine(repo)

        session = {
            "_id": "session1",
            "current_theta": 0.0,
            "question_count": 2,  # Only 2 questions in
            "responses": [
                {"theta_after": 0.0, "discrimination": 1.0, "difficulty": 0.5, "guessing": 0.25},
                {"theta_after": 0.1, "discrimination": 1.0, "difficulty": 0.5, "guessing": 0.25},
            ],
        }
        result = engine.process_answer(session, SAMPLE_QUESTIONS[0], "A")
        assert result["should_stop"] is False
        assert result["session_status"] == "active"


class TestBuildTestResult:
    """Tests for building test result documents from completed sessions."""

    def test_build_result(self):
        """Should correctly aggregate topics and compute accuracy."""
        session = {
            "_id": "session1",
            "student_id": "student_1",
            "current_theta": 1.5,
            "responses": [
                {"topic": "Algebra", "correct": True, "difficulty": 0.3},
                {"topic": "Vocabulary", "correct": False, "difficulty": 0.5},
                {"topic": "Algebra", "correct": True, "difficulty": 0.6},
            ],
        }

        result = AdaptiveEngine.build_test_result(session)

        assert result["final_theta"] == 1.5
        assert result["total_questions"] == 3
        assert result["correct_count"] == 2
        assert abs(result["accuracy_rate"] - 0.6667) < 0.01
        assert "Algebra" in result["topics_attempted"]
        assert "Vocabulary" in result["topics_attempted"]
        assert "Vocabulary" in result["topics_missed"]
        assert "Algebra" not in result["topics_missed"]
