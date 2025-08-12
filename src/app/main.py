#!/usr/bin/env python3
"""
main.py - Anchor Insight AI Unified Service
Unified FastAPI service providing focus analysis and time tracking
Following the technical specifications in spec.md
"""
import asyncio
import base64
import time
import io
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

import pyautogui
from PIL import Image
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import logging

# Import existing modular components
from src.controllers.focus_controller import focus_router
from src.controllers.focus_score_controller import focus_score_router
from src.config.settings import app_settings, focus_score_settings
from src.constants.focus_constants import API_TITLE, API_DESCRIPTION, API_VERSION  
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use existing configuration
settings = app_settings
focus_settings = focus_score_settings

# Simple in-memory cache
class SimpleCache:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple[Any, float]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        self.cache[key] = (value, time.time())
    
    def clear(self):
        self.cache.clear()

# Initialize cache
cache = SimpleCache(60)  # 60 seconds TTL

# Request and Response Models
class AnalysisRequest(BaseModel):
    capture_screenshot: bool = Field(True, description="Whether to capture screenshot")
    include_time_records: bool = Field(True, description="Whether to include detailed time records")
    use_cache: bool = Field(True, description="Whether to use cached results")

class AnalysisResponse(BaseModel):
    focus_score: Optional[int] = None
    total_focus_minutes: Optional[float] = None
    total_leave_minutes: Optional[float] = None
    focus_sessions: Optional[int] = None
    leave_sessions: Optional[int] = None
    latest_time_record: Optional[str] = None
    all_time_records: Optional[List[str]] = None
    suggestion: Optional[str] = None
    processing_time_ms: Optional[float] = None
    cached: bool = False
    error: Optional[str] = None

class MonitorControl(BaseModel):
    show_window: bool = Field(False, description="Whether to show monitoring window")

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Anchor Insight AI Unified Service")
    yield
    logger.info("Anchor Insight AI Unified Service shutdown complete")
    cache.clear()

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION, 
    version=API_VERSION,
    lifespan=lifespan
)

# Include existing routers with proper prefixes
app.include_router(focus_router, prefix="/api/v1/monitor", tags=["Monitor"])
app.include_router(focus_score_router, prefix="/api/v1/focus", tags=["Focus Score"])

# Helper functions
async def capture_screenshot() -> str:
    """Capture screenshot and return base64 encoded string"""
    def _capture():
        screenshot = pyautogui.screenshot()
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return base64.b64encode(img_byte_arr.read()).decode('utf-8')
    
    # Run in thread pool to avoid blocking
    return await asyncio.to_thread(_capture)

@app.get("/health")
async def health_check():
    """Service health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Anchor Insight AI Unified Service",
        "version": API_VERSION,
        "architecture": "unified_fastapi_service"
    }

# Root endpoint for API information
@app.get("/")
async def root():
    """API information and health check"""
    return {
        "service": "Anchor Insight AI Unified Service", 
        "version": API_VERSION,
        "status": "operational",
        "architecture": "unified_fastapi_service",
        "endpoints": {
            "/api/v1/monitor/*": "Person monitoring and time tracking",
            "/api/v1/focus/*": "Focus score analysis",
            "/health": "Service health check"
        },
        "description": "Unified FastAPI service providing focus analysis and time tracking"
    }

if __name__ == "__main__":
    print("Starting Anchor Insight AI Unified Service...")
    print(f"Service: {API_TITLE} v{API_VERSION}")
    print("Architecture: Unified FastAPI service with modular components")
    print("API Documentation available at http://localhost:8080/docs")
    print("\nService endpoints:")
    print("  - /api/v1/monitor/* - Person monitoring and time tracking")  
    print("  - /api/v1/focus/* - Focus score analysis")
    print("  - /health - Service health check")
    print("\nConfiguration:")
    print("  - Environment variables loaded from .env file")
    print("  - All services running in single process")
    print("  - Modular architecture maintained")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")