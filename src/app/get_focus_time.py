#!/usr/bin/env python3
"""
Person Monitoring Service using YOLOv11-Pose and FastAPI
Features:
1. Camera-based person detection
2. Focus/Leave time tracking
3. RESTful API endpoints
4. Real-time monitoring with optimized performance
"""

import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.config.settings import app_settings
from src.controllers.focus_controller import focus_router
from src.services.focus_service import session_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# FastAPI app with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Person Monitor API")
    yield
    # Cleanup on shutdown
    active_sessions = session_manager.list_sessions()
    for session_id in active_sessions:
        monitor = session_manager.get_session(session_id)
        if monitor and monitor.is_running:
            monitor.stop()
    session_manager.cleanup_inactive_sessions()
    logger.info("Person Monitor API shutdown complete")


app = FastAPI(
    title="Person Monitor API",
    description="Real-time person detection and time tracking using YOLOv11-Pose",
    version="2.0.0",
    lifespan=lifespan
)

# Include focus router
app.include_router(focus_router)

if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "get_focus_time:app",
        host=app_settings.api_host,
        port=app_settings.api_port,
        reload=app_settings.api_reload,
        log_level=app_settings.log_level
    )