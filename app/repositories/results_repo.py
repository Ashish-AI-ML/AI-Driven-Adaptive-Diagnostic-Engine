"""
Repository for TestResults collection.
Handles creation and retrieval of immutable test result records.
"""

from datetime import datetime
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class ResultsRepository:
    """Data access layer for the TestResults collection."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.test_results

    async def create(self, result_data: dict) -> str:
        """Create a new test result. Returns inserted ID."""
        result_data["completed_at"] = datetime.utcnow()
        result = await self.collection.insert_one(result_data)
        return str(result.inserted_id)

    async def find_by_session_id(self, session_id: str) -> Optional[dict]:
        """Find test results by session ID."""
        result = await self.collection.find_one({"session_id": session_id})
        if result:
            result["_id"] = str(result["_id"])
        return result

    async def find_by_student_id(self, student_id: str) -> list:
        """Find all test results for a student."""
        cursor = self.collection.find({"student_id": student_id})
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def update_study_plan(self, session_id: str, study_plan: dict):
        """Store the LLM-generated study plan in the test result."""
        await self.collection.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "study_plan": study_plan,
                    "plan_generated_at": datetime.utcnow()
                }
            }
        )
