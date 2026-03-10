"""
Repository for UserSessions collection.
Handles session lifecycle: create, read, update, complete.
"""

from datetime import datetime
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class SessionRepository:
    """Data access layer for the UserSessions collection."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.user_sessions

    async def create(self, session_data: dict) -> str:
        """Create a new session. Returns the inserted ID as string."""
        session_data["started_at"] = datetime.utcnow()
        session_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(session_data)
        return str(result.inserted_id)

    async def find_by_id(self, session_id: str) -> Optional[dict]:
        """Find a session by its ObjectId."""
        if not ObjectId.is_valid(session_id):
            return None
        session = await self.collection.find_one({"_id": ObjectId(session_id)})
        if session:
            session["_id"] = str(session["_id"])
        return session

    async def find_active_by_student(self, student_id: str) -> Optional[dict]:
        """Find the active session for a student (idempotent start)."""
        session = await self.collection.find_one({
            "student_id": student_id,
            "status": "active"
        })
        if session:
            session["_id"] = str(session["_id"])
        return session

    async def update_after_answer(
        self,
        session_id: str,
        new_theta: float,
        target_difficulty: float,
        question_count: int,
        answered_id: str,
        response_record: dict,
        status: str = "active"
    ):
        """Atomic update after an answer is submitted."""
        await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "current_theta": new_theta,
                    "target_difficulty": target_difficulty,
                    "question_count": question_count,
                    "status": status,
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "answered_ids": answered_id,
                    "responses": response_record
                }
            }
        )

    async def mark_completed(self, session_id: str):
        """Mark a session as completed."""
        await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"status": "completed", "updated_at": datetime.utcnow()}}
        )
