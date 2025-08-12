"""
Focus monitoring API controller
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.config.settings import MonitorConfig
from src.models.focus_models import (
    StatusResponse, SummaryResponse, TimeRecord, FocusScoreResponse,
    HealthResponse, MonitorStartResponse, MonitorStopResponse, LatestRecordResponse
)
from src.services.focus_service import session_manager

logger = logging.getLogger(__name__)

# Create router for focus endpoints
focus_router = APIRouter(prefix="/monitor", tags=["focus"])


def get_or_create_session(session_id: str = "default", config: Optional[MonitorConfig] = None):
    """Get existing session or create new one if needed"""
    monitor = session_manager.get_session(session_id)
    if monitor is None and config is not None:
        monitor = session_manager.create_session(
            session_id=session_id,
            model_path=config.model_path,
            camera_index=config.camera_index
        )
    return monitor


@focus_router.post("/start", response_model=MonitorStartResponse)
async def start_monitoring(config: MonitorConfig, session_id: str = "default"):
    """Start person monitoring for a specific session"""
    try:
        # Check if session already exists and is running
        existing_monitor = session_manager.get_session(session_id)
        if existing_monitor and existing_monitor.is_running:
            return JSONResponse(
                status_code=400,
                content={"error": f"Monitoring is already running for session {session_id}"}
            )
        
        # Create or get monitor
        monitor = get_or_create_session(session_id, config)
        if monitor is None:
            raise HTTPException(status_code=500, detail="Failed to create monitor session")
        
        # Start monitoring in background
        await asyncio.get_event_loop().run_in_executor(
            None, monitor.start, config.show_window
        )
        
        return MonitorStartResponse(
            status="started",
            message=f"Monitoring started successfully for session {session_id}",
            config=config.dict()
        )
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@focus_router.post("/stop", response_model=MonitorStopResponse)
async def stop_monitoring(session_id: str = "default"):
    """Stop person monitoring for a specific session"""
    try:
        monitor = session_manager.get_session(session_id)
        if monitor is None:
            return JSONResponse(
                status_code=400,
                content={"error": f"No monitoring session found for {session_id}"}
            )
        
        if not monitor.is_running:
            return JSONResponse(
                status_code=400,
                content={"error": f"Monitoring is not running for session {session_id}"}
            )
        
        # Get final stats before stopping
        final_stats = monitor.get_summary_stats()
        
        # Stop monitoring
        await asyncio.get_event_loop().run_in_executor(
            None, monitor.stop
        )
        
        # Remove session
        session_manager.remove_session(session_id)
        
        return MonitorStopResponse(
            status="stopped",
            message=f"Monitoring stopped successfully for session {session_id}",
            final_stats=final_stats
        )
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@focus_router.get("/status", response_model=StatusResponse)
async def get_status(session_id: str = "default"):
    """Get current monitoring status for a specific session"""
    try:
        monitor = session_manager.get_session(session_id)
        if monitor is None:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        status = monitor.get_current_status()
        return StatusResponse(**status)
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@focus_router.get("/score", response_model=FocusScoreResponse)
async def get_focus_score(session_id: str = "default"):
    """Get current focus score for a specific session"""
    try:
        monitor = session_manager.get_session(session_id)
        if monitor is None:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        raw_score = monitor.get_focus_score()
        status = monitor.get_current_status()
        
        # Calculate session duration
        session_duration = 0.0
        if status.get('current_session'):
            session_duration = status['current_session'].get(
                'duration_minutes', 0.0
            )

        return FocusScoreResponse(
            score=raw_score * 20,  # Convert 0-5 scale to 0-100
            timestamp=datetime.now().isoformat(),
            session_duration_minutes=session_duration,
        )
    except Exception as e:
        logger.error(f"Failed to get focus score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@focus_router.get("/records", response_model=List[TimeRecord])
async def get_records(session_id: str = "default"):
    """Get all time records for a specific session"""
    try:
        monitor = session_manager.get_session(session_id)
        if monitor is None:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        records = monitor.get_all_records()
        
        # Convert to response model
        return [
            TimeRecord(
                type=record['type'],
                start=record['start'],
                end=record['end'],
                formatted=record['formatted'],
                duration_minutes=(record['end'] - record['start']) / 60
            )
            for record in records
        ]
    except Exception as e:
        logger.error(f"Failed to get records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@focus_router.get("/summary", response_model=SummaryResponse)
async def get_summary(session_id: str = "default"):
    """Get time tracking summary for a specific session"""
    try:
        monitor = session_manager.get_session(session_id)
        if monitor is None:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        summary = monitor.get_summary_stats()
        return SummaryResponse(**summary)
    except Exception as e:
        logger.error(f"Failed to get summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@focus_router.get("/latest", response_model=LatestRecordResponse)
async def get_latest_record(session_id: str = "default"):
    """Get latest time record for a specific session"""
    try:
        monitor = session_manager.get_session(session_id)
        if monitor is None:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        record = monitor.get_latest_record()
        
        if record is None:
            return LatestRecordResponse(message="No new records available")
        
        return LatestRecordResponse(latest_record=record)
    except Exception as e:
        logger.error(f"Failed to get latest record: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@focus_router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check if any sessions are active
        active_sessions = session_manager.list_sessions()
        monitoring_active = any(
            session_manager.get_session(sid).is_running 
            for sid in active_sessions 
            if session_manager.get_session(sid)
        )
        
        return HealthResponse(
            status="healthy",
            monitoring_active=monitoring_active,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content=HealthResponse(
                status="unhealthy",
                monitoring_active=False,
                timestamp=datetime.now().isoformat()
            ).dict()
        )


@focus_router.get("/sessions")
async def list_sessions():
    """List all active monitoring sessions"""
    try:
        sessions = session_manager.list_sessions()
        session_info = []
        
        for session_id in sessions:
            monitor = session_manager.get_session(session_id)
            if monitor:
                status = monitor.get_current_status()
                session_info.append({
                    "session_id": session_id,
                    "is_running": monitor.is_running,
                    "is_initialized": status.get('is_initialized', False),
                    "total_records": status.get('total_records', 0)
                })
        
        return {"sessions": session_info, "total_sessions": len(sessions)}
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@focus_router.delete("/session/{session_id}")
async def remove_session(session_id: str):
    """Remove a specific session"""
    try:
        success = session_manager.remove_session(session_id)
        if success:
            return {"message": f"Session {session_id} removed successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        logger.error(f"Failed to remove session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
