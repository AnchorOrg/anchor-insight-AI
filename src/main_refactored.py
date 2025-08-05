#!/usr/bin/env python3
"""
main_refactored.py - Focus Management API Gateway with Layered Architecture
Implements Controller-Service pattern following clean architecture principles
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

from src.controllers.focus_controller import FocusController
from src.models.focus_models import (
    AnalysisRequest, MonitoringConfig
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global controller instance
focus_controller: FocusController = None


# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global focus_controller
    
    # Startup
    logger.info("Starting Focus Management API Gateway with Layered Architecture")
    focus_controller = FocusController()
    await focus_controller.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Focus Management API Gateway")
    if focus_controller:
        await focus_controller.close()


# Create FastAPI app
app = FastAPI(
    title="Focus Management API Gateway",
    version="3.0.0",
    description="Unified API for focus analysis and time tracking with layered architecture",
    lifespan=lifespan
)


# API Routes using Controller pattern
@app.get("/")
async def root():
    """API information and health check"""
    return await focus_controller.get_api_info()


@app.post("/analyze")
async def analyze_focus(request: AnalysisRequest = AnalysisRequest()):
    """Comprehensive focus analysis with suggestions"""
    return await focus_controller.analyze_focus(request)


@app.post("/monitor/start")
async def start_monitor(control: MonitoringConfig = MonitoringConfig()):
    """Start person monitoring"""
    return await focus_controller.start_monitor(control)


@app.post("/monitor/stop")
async def stop_monitor():
    """Stop person monitoring"""
    return await focus_controller.stop_monitor()


@app.get("/monitor/status")
async def get_monitor_status():
    """Get monitoring status"""
    return await focus_controller.get_monitor_status()


@app.get("/focus/score")
async def get_focus_score_only():
    """Get current focus score only"""
    return await focus_controller.get_focus_score_only()


@app.get("/time/records")
async def get_time_records():
    """Get all time records"""
    return await focus_controller.get_time_records()


@app.get("/time/summary")
async def get_time_summary():
    """Get time statistics summary"""
    return await focus_controller.get_time_summary()


@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = await focus_controller.health_check()
    status_code = 200 if health_status.status == "healthy" else 503
    return JSONResponse(status_code=status_code, content=health_status.model_dump())


if __name__ == "__main__":
    print("Starting Focus Management API Gateway v3.0 with Layered Architecture...")
    print("Architecture: Controller -> Service -> External APIs")
    print("\nLayers:")
    print("  - Controllers: Handle HTTP requests and responses")
    print("  - Services: Implement business logic")
    print("  - Models: Define data structures")
    print("  - Config: Manage application settings")
    print("\nAPI Documentation available at http://localhost:8080/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
