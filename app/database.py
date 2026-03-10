"""
MongoDB async connection management using Motor.
Provides database access and index creation on startup.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

# Module-level client and database references
_client: AsyncIOMotorClient = None
_database: AsyncIOMotorDatabase = None


async def connect_to_mongodb():
    """Initialize MongoDB connection and create indexes."""
    global _client, _database
    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    _database = _client[settings.DATABASE_NAME]

    # Create indexes per schema design
    await _create_indexes()
    print(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")


async def close_mongodb_connection():
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        print("🔌 MongoDB connection closed")


async def _create_indexes():
    """Apply all collection indexes defined in the schema design."""
    # Questions: compound index on difficulty + topic
    await _database.questions.create_index(
        [("difficulty", 1), ("topic", 1)],
        name="difficulty_topic_idx"
    )
    # Questions: tag-based filtering
    await _database.questions.create_index(
        [("tags", 1)],
        name="tags_idx"
    )

    # UserSessions: find active session for a student
    await _database.user_sessions.create_index(
        [("student_id", 1), ("status", 1)],
        name="student_status_idx"
    )
    # UserSessions: TTL for abandoned sessions (2 hours)
    await _database.user_sessions.create_index(
        "updated_at",
        name="session_ttl_idx",
        expireAfterSeconds=settings.SESSION_TTL_SECONDS
    )

    # TestResults: lookup by session_id
    await _database.test_results.create_index(
        [("session_id", 1)],
        name="session_id_idx",
        unique=True
    )
    # TestResults: lookup by student_id
    await _database.test_results.create_index(
        [("student_id", 1)],
        name="student_id_idx"
    )


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance. Must be called after connect_to_mongodb()."""
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongodb() first.")
    return _database
