"""
API integration tests using FastAPI TestClient.
Tests the full session flow: start → questions → answers → results.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from bson import ObjectId


# Mock MongoDB before importing the app
mock_db = MagicMock()


def mock_get_database():
    return mock_db


# Patch the database module
with patch("app.database.get_database", mock_get_database):
    with patch("app.database.connect_to_mongodb", new_callable=AsyncMock):
        with patch("app.database.close_mongodb_connection", new_callable=AsyncMock):
            from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check(self):
        """Health endpoint should return 200."""
        mock_db.command = AsyncMock(return_value={"ok": 1})
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "timestamp" in data


class TestSessionEndpoint:
    """Tests for POST /session/start."""

    def test_start_session(self):
        """Should create a new session."""
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )
        mock_db.user_sessions = mock_collection

        response = client.post("/session/start", json={
            "student_id": "test_student_001"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["current_theta"] == 0.0
        assert "session_id" in data

    def test_start_session_returns_existing(self):
        """Should return existing active session (idempotent)."""
        existing_session = {
            "_id": ObjectId(),
            "student_id": "test_student_001",
            "current_theta": 0.5,
            "status": "active",
        }
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=existing_session)
        mock_db.user_sessions = mock_collection

        response = client.post("/session/start", json={
            "student_id": "test_student_001"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["message"] == "Existing active session found"


class TestAnswerValidation:
    """Tests for POST /answer/submit validation."""

    def test_invalid_answer_choice(self):
        """Should reject answer outside A-D."""
        response = client.post("/answer/submit", json={
            "session_id": str(ObjectId()),
            "question_id": str(ObjectId()),
            "selected_answer": "E",
        })
        assert response.status_code == 422  # Pydantic validation


class TestResultsEndpoint:
    """Tests for GET /results/{session_id}."""

    def test_session_not_found(self):
        """Should return 404 for non-existent session."""
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_db.user_sessions = mock_collection

        response = client.get(f"/results/{str(ObjectId())}")
        assert response.status_code == 404

    def test_active_session_returns_400(self):
        """Should return 400 if session is still active."""
        active_session = {
            "_id": ObjectId(),
            "status": "active",
        }
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=active_session)
        mock_db.user_sessions = mock_collection

        response = client.get(f"/results/{str(ObjectId())}")
        assert response.status_code == 400
