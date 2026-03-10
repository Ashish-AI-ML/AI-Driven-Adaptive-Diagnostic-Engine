"""
FastAPI Application — main entry point.
Registers routers, startup/shutdown events, CORS middleware, and health endpoint.
"""

from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import connect_to_mongodb, close_mongodb_connection, get_database
from app.routers import session_router, question_router, answer_router, results_router
from app.schemas.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await connect_to_mongodb()
    yield
    await close_mongodb_connection()


app = FastAPI(
    title="AI-Driven Adaptive Diagnostic Engine",
    description=(
        "A 1D Adaptive Testing System powered by IRT 3PL. "
        "Adaptively selects GRE-style questions based on student ability, "
        "estimates latent ability via Item Response Theory, and generates "
        "personalized study plans via LLM."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(session_router.router)
app.include_router(question_router.router)
app.include_router(answer_router.router)
app.include_router(results_router.router)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """System health check for monitoring and load balancers."""
    try:
        db = get_database()
        # Ping MongoDB
        await db.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        database=db_status,
        timestamp=datetime.utcnow(),
    )
