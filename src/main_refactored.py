"""
Unified FastAPI Service - Anchor Insight AI
===========================================

A single FastAPI service that integrates focus analysis and scoring capabilities
without microservice HTTP calls, using modular architecture with dependency injection.

Architecture:
- Single FastAPI application with unified routing
- Modular controllers and services maintained
- Direct service calls instead of HTTP requests
- Centralized configuration and dependency injection
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings
from src.controllers.focus_controller import focus_router
from src.controllers.focus_score_controller import focus_score_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifespan events.
    
    Handles startup and shutdown events for the unified service.
    """
    # Startup
    settings = get_settings()
    logger.info("Starting Anchor Insight AI unified service")
    logger.info(f"Environment: {settings.environment}")
    logger.info("OpenAI API configured")  # Don't log the actual key for security
    
    yield
    
    # Shutdown
    logger.info("Shutting down Anchor Insight AI unified service")


# Create unified FastAPI application
app = FastAPI(
    title="Anchor Insight AI",
    description="Unified AI-powered focus analysis and scoring service",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API versioning
app.include_router(focus_router, prefix="/api/v1")
app.include_router(focus_score_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "Anchor Insight AI - Unified Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "src.main_refactored:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
