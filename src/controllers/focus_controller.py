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
        """Focus monitoring API controller implementation."""
        import asyncio
        import logging
        from datetime import datetime
        from typing import Dict, Any, List, Optional

        from fastapi import APIRouter, HTTPException

        from src.config.settings import MonitorConfig
        from src.models.focus_models import (
            StatusResponse, SummaryResponse, TimeRecord, FocusScoreResponse,
            HealthResponse, MonitorStartResponse, MonitorStopResponse, LatestRecordResponse
        )
        from src.services.focus_service import session_manager, PersonMonitorService

        logger = logging.getLogger(__name__)

        focus_router = APIRouter(prefix="/monitor", tags=["monitor"])


        def _get_session_or_404(session_id: str) -> PersonMonitorService:
            monitor = session_manager.get_session(session_id)
            if monitor is None:
                raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
            return monitor


        def _create_or_get_session(session_id: str, config: MonitorConfig) -> PersonMonitorService:
            monitor = session_manager.get_session(session_id)
            if monitor is None:
                monitor = session_manager.create_session(
                    session_id=session_id,
                    model_path=config.model_path,
                    camera_index=config.camera_index
                )
            return monitor


        @focus_router.post("/start", response_model=MonitorStartResponse)
        async def start_monitoring(config: MonitorConfig, session_id: str = "default"):
            try:
                monitor = _create_or_get_session(session_id, config)
                if monitor.is_running:
                    return MonitorStartResponse(status="already_running", message=f"Session {session_id} already running", config=config.dict())
                await asyncio.get_event_loop().run_in_executor(None, monitor.start, config.show_window)
                return MonitorStartResponse(status="started", message=f"Monitoring started for session {session_id}", config=config.dict())
            except Exception as e:
                logger.exception("Failed to start monitoring")
                raise HTTPException(status_code=500, detail=str(e))


        @focus_router.post("/stop", response_model=MonitorStopResponse)
        async def stop_monitoring(session_id: str = "default"):
            try:
                monitor = _get_session_or_404(session_id)
                if not monitor.is_running:
                    return MonitorStopResponse(status="not_running", message=f"Session {session_id} not running", final_stats=monitor.get_summary_stats())
                monitor.stop()
                return MonitorStopResponse(status="stopped", message=f"Monitoring stopped for session {session_id}", final_stats=monitor.get_summary_stats())
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Failed to stop monitoring")
                raise HTTPException(status_code=500, detail=str(e))


        @focus_router.get("/status", response_model=StatusResponse)
        async def get_status(session_id: str = "default"):
            try:
                monitor = _get_session_or_404(session_id)
                status = monitor.get_current_status()
                return StatusResponse(
                    is_initialized=monitor.is_initialized,
                    person_detected=status.get("person_detected"),
                    current_session={"session_id": session_id, "running": monitor.is_running},
                    total_records=len(monitor.get_all_records()),
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Failed to get status")
                raise HTTPException(status_code=500, detail=str(e))


        @focus_router.get("/score", response_model=FocusScoreResponse)
        async def get_focus_score(session_id: str = "default"):
            try:
                monitor = _get_session_or_404(session_id)
                # Original monitor score scale 0-5; convert to 0-100 for unified response
                raw_score = monitor.get_focus_score()
                normalized = max(0.0, min(raw_score / 5 * 100, 100))
                confidence = "high" if normalized >= 70 else "low"
                return FocusScoreResponse(focus_score=int(normalized), confidence=confidence, processing_time=None)
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Failed to get focus score")
                raise HTTPException(status_code=500, detail=str(e))


        @focus_router.get("/records", response_model=List[TimeRecord])
        async def get_records(session_id: str = "default"):
            try:
                monitor = _get_session_or_404(session_id)
                records = monitor.get_all_records()
                return [
                    TimeRecord(
                        type=r["type"],
                        start=r["start"],
                        end=r["end"],
                        formatted=r.get("formatted", ""),
                        duration_minutes=(r["end"] - r["start"]) / 60 if r.get("end") and r.get("start") else 0.0,
                    ) for r in records
                ]
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Failed to get records")
                raise HTTPException(status_code=500, detail=str(e))


        @focus_router.get("/summary", response_model=SummaryResponse)
        async def get_summary(session_id: str = "default"):
            try:
                monitor = _get_session_or_404(session_id)
                stats = monitor.get_summary_stats()
                return SummaryResponse(
                    total_focus_minutes=stats.get("total_focus_minutes", 0.0),
                    total_leave_minutes=stats.get("total_leave_minutes", 0.0),
                    focus_sessions=stats.get("focus_sessions", 0),
                    leave_sessions=stats.get("leave_sessions", 0),
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Failed to get summary")
                raise HTTPException(status_code=500, detail=str(e))


        @focus_router.get("/latest", response_model=LatestRecordResponse)
        async def get_latest_record(session_id: str = "default"):
            try:
                monitor = _get_session_or_404(session_id)
                latest = monitor.get_latest_record()
                return LatestRecordResponse(latest_record=latest, message="ok" if latest else "no records")
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Failed to get latest record")
                raise HTTPException(status_code=500, detail=str(e))


        @focus_router.get("/health", response_model=HealthResponse)
        async def health_check():
            try:
                # Basic aggregated monitoring health
                active_sessions = session_manager.list_sessions()
                monitoring_active = any(
                    (session_manager.get_session(s) and session_manager.get_session(s).is_running)
                    for s in active_sessions
                )
                return HealthResponse(
                    status="ok",
                    monitoring_active=monitoring_active,
                    timestamp=datetime.utcnow().isoformat()
                )
            except Exception as e:
                logger.exception("Health check failed")
                raise HTTPException(status_code=500, detail=str(e))


        @focus_router.get("/sessions")
        async def list_sessions():
            try:
                return {"sessions": session_manager.list_sessions()}
            except Exception as e:
                logger.exception("Failed to list sessions")
                raise HTTPException(status_code=500, detail=str(e))


        @focus_router.delete("/session/{session_id}")
        async def remove_session(session_id: str):
            try:
                success = session_manager.remove_session(session_id)
                if not success:
                    raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
                return {"status": "removed", "session_id": session_id}
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Failed to remove session")
                raise HTTPException(status_code=500, detail=str(e))
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
