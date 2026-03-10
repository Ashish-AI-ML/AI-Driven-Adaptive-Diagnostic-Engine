"""
Repository for Questions collection.
Handles CRUD and difficulty-band queries with fallback widening.
"""

from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.config import settings


class QuestionRepository:
    """Data access layer for the Questions collection."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.questions

    async def find_by_difficulty_band(
        self,
        target_difficulty: float,
        excluded_ids: List[str],
        topic: Optional[str] = None
    ) -> Optional[dict]:
        """
        Find a question near the target difficulty, excluding already-answered IDs.
        Implements fallback widening: ±0.1 → ±0.2 → ±0.3.
        """
        excluded_object_ids = [ObjectId(qid) for qid in excluded_ids if ObjectId.is_valid(qid)]
        band_width = settings.INITIAL_BAND_WIDTH

        for _ in range(settings.MAX_BAND_EXPANSIONS + 1):
            query = {
                "difficulty": {
                    "$gte": max(settings.DIFFICULTY_MIN, target_difficulty - band_width),
                    "$lte": min(settings.DIFFICULTY_MAX, target_difficulty + band_width),
                },
                "_id": {"$nin": excluded_object_ids}
            }
            if topic:
                query["topic"] = topic

            question = await self.collection.find_one(query)
            if question:
                question["_id"] = str(question["_id"])
                return question

            band_width += settings.BAND_EXPANSION_STEP

        # Final fallback: any unanswered question
        fallback_query = {"_id": {"$nin": excluded_object_ids}}
        question = await self.collection.find_one(fallback_query)
        if question:
            question["_id"] = str(question["_id"])
        return question

    async def find_by_id(self, question_id: str) -> Optional[dict]:
        """Find a question by its ObjectId."""
        if not ObjectId.is_valid(question_id):
            return None
        question = await self.collection.find_one({"_id": ObjectId(question_id)})
        if question:
            question["_id"] = str(question["_id"])
        return question

    async def count(self) -> int:
        """Return total number of questions."""
        return await self.collection.count_documents({})

    async def insert_many(self, questions: List[dict]) -> List[str]:
        """Insert multiple questions. Returns list of inserted IDs."""
        result = await self.collection.insert_many(questions)
        return [str(oid) for oid in result.inserted_ids]
