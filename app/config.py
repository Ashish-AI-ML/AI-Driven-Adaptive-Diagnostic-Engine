"""
Application configuration using Pydantic Settings.
Loads values from .env file and provides typed access to all config values.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Central configuration for the Adaptive Diagnostic Engine."""

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "adaptive_diagnostic_engine"

    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"

    # Algorithm Constants
    INITIAL_THETA: float = 0.0
    MAX_QUESTIONS: int = 10
    SEM_THRESHOLD: float = 0.3

    # IRT Bounds
    THETA_MIN: float = -3.0
    THETA_MAX: float = 3.0
    DIFFICULTY_MIN: float = 0.1
    DIFFICULTY_MAX: float = 1.0

    # Difficulty Band Search
    INITIAL_BAND_WIDTH: float = 0.1
    MAX_BAND_EXPANSIONS: int = 3
    BAND_EXPANSION_STEP: float = 0.1

    # Session TTL (seconds) — 2 hours
    SESSION_TTL_SECONDS: int = 7200

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
