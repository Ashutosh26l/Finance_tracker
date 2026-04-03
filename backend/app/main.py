"""
Finance Tracker API — Main Application Entry Point

ML-powered personal finance tracker with auto-categorization,
spending predictions, and anomaly detection.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, close_mongo_connection
from app.routes import transactions, categories, analytics
from app.ml.categorizer import categorizer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("🚀 Starting Finance Tracker API...")
    await connect_to_mongo()

    # Initialize ML models
    print("🧠 Loading ML models...")
    categorizer.load_model()
    print("✅ All systems ready!")

    yield

    # Shutdown
    await close_mongo_connection()
    print("👋 Finance Tracker API shut down")


app = FastAPI(
    title="Finance Tracker API",
    description="ML-powered personal finance tracker with auto-categorization, spending predictions, and anomaly detection.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(analytics.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": "Finance Tracker API",
        "version": "1.0.0",
        "status": "healthy",
        "ml_models": {
            "categorizer": categorizer.is_trained,
            "categorizer_accuracy": f"{categorizer.accuracy:.2%}" if categorizer.is_trained else "not trained",
        }
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
