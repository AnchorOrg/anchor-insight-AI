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
API_VERSION = "1.0.0"
API_PREFIX = f"/api/v1"

app = FastAPI(
    title="Anchor Insight AI",
    description="Unified AI-powered focus analysis and scoring service",
    version=API_VERSION,
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

# Include routers with API versioning ensuring no duplicate segment
# focus_router carries internal prefix /monitor; focus_score_router /analyze
app.include_router(focus_router, prefix=API_PREFIX)
app.include_router(focus_score_router, prefix=API_PREFIX)

@app.get("/")
async def root():
    """Root endpoint returning service metadata."""
    return {
        "service": "Anchor Insight AI - Unified Service",
        "status": "running",
        "version": API_VERSION,
        "routes": ["/api/v1/monitor", "/api/v1/analyze"],
    }

@app.get("/health")
async def health_check():
    """Simple liveness probe."""
    return {"status": "healthy", "version": API_VERSION}

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level,
    )