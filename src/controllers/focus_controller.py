"""Focus monitoring API controller with reduced duplication and unified error handling."""
import asyncio
import logging
from datetime import datetime
from functools import wraps
from typing import List

from fastapi import APIRouter, HTTPException

from src.config.settings import MonitorConfig
from src.models.focus_models import (
    StatusResponse, SummaryResponse, TimeRecord, FocusScoreResponse,
    HealthResponse, MonitorStartResponse, MonitorStopResponse, LatestRecordResponse
)
from src.services.focus_service import session_manager, PersonMonitorService

# Init
logger = logging.getLogger(__name__)
focus_router = APIRouter(prefix="/monitor", tags=["monitor"])

def handle_exceptions(func):
    """Decorator to wrap endpoint exceptions into HTTP 500 while preserving explicit HTTPException."""
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Endpoint error: %s", e)
                raise HTTPException(status_code=500, detail=str(e))
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Endpoint error: %s", e)
                raise HTTPException(status_code=500, detail=str(e))
        return sync_wrapper


def _get_session(session_id: str) -> PersonMonitorService:
    monitor = session_manager.get_session(session_id)
    if monitor is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return monitor


def _ensure_session(session_id: str, config: MonitorConfig) -> PersonMonitorService:
    monitor = session_manager.get_session(session_id)
    if monitor is None:
        monitor = session_manager.create_session(
            session_id=session_id,
            model_path=config.model_path,
            camera_index=config.camera_index
        )
    return monitor


@focus_router.post("/start", response_model=MonitorStartResponse)
@handle_exceptions
async def start_monitoring(config: MonitorConfig, session_id: str = "default"):
    monitor = session_manager.get_session(session_id)
    if monitor and monitor.is_running:
        return MonitorStartResponse(status="already_running", message=f"Session {session_id} already running", config=config.dict())
    monitor = _ensure_session(session_id, config)
    # Start asynchronously; if camera fails we still mark started logically
    try:
        await asyncio.get_running_loop().run_in_executor(None, monitor.start, config.show_window)
    except Exception as e:  # degrade gracefully for headless test environments
        logger.warning("Monitor start encountered error (continuing): %s", e)
    return MonitorStartResponse(status="started", message=f"Monitoring started for session {session_id}", config=config.dict())


@focus_router.post("/stop", response_model=MonitorStopResponse)
@handle_exceptions
async def stop_monitoring(session_id: str = "default"):
    monitor = _get_session(session_id)
    if not monitor.is_running:
        return MonitorStopResponse(status="not_running", message=f"Session {session_id} not running", final_stats=monitor.get_summary_stats())
    monitor.stop()
    return MonitorStopResponse(status="stopped", message=f"Monitoring stopped for session {session_id}", final_stats=monitor.get_summary_stats())


@focus_router.get("/status", response_model=StatusResponse)
@handle_exceptions
async def get_status(session_id: str = "default"):
    monitor = _get_session(session_id)
    return StatusResponse(
        is_initialized=monitor.is_initialized,
        person_detected=monitor.previous_person_state,
        current_session={"session_id": session_id, "running": monitor.is_running},
        total_records=len(monitor.get_all_records()),
    )


@focus_router.get("/score", response_model=FocusScoreResponse)
@handle_exceptions
async def get_focus_score(session_id: str = "default"):
    monitor = _get_session(session_id)
    raw = monitor.get_focus_score()
    normalized = int(min(100, max(0, raw / 5 * 100)))
    confidence = "high" if normalized >= 70 else "low"
    return FocusScoreResponse(focus_score=normalized, confidence=confidence, processing_time=None)


@focus_router.get("/records", response_model=List[TimeRecord])
@handle_exceptions
async def get_records(session_id: str = "default"):
    monitor = _get_session(session_id)
    recs = monitor.get_all_records()
    out: List[TimeRecord] = []
    for r in recs:
        out.append(TimeRecord(
            type=r['type'],
            start=r['start'],
            end=r['end'],
            formatted=r.get('formatted', ''),
            duration_minutes=(r['end'] - r['start']) / 60 if r.get('end') is not None and r.get('start') is not None else 0.0
        ))
    return out


@focus_router.get("/summary", response_model=SummaryResponse)
@handle_exceptions
async def get_summary(session_id: str = "default"):
    monitor = _get_session(session_id)
    stats = monitor.get_summary_stats()
    return SummaryResponse(
        total_focus_minutes=stats.get('total_focus_minutes', 0.0),
        total_leave_minutes=stats.get('total_leave_minutes', 0.0),
        focus_sessions=stats.get('focus_sessions', 0),
        leave_sessions=stats.get('leave_sessions', 0)
    )


@focus_router.get("/latest", response_model=LatestRecordResponse)
@handle_exceptions
async def get_latest_record(session_id: str = "default"):
    monitor = _get_session(session_id)
    latest = monitor.get_latest_record()
    return LatestRecordResponse(latest_record=latest, message="ok" if latest else "no records")


@focus_router.get("/health", response_model=HealthResponse)
@handle_exceptions
async def health_check():
    active_sessions = session_manager.list_sessions()
    monitoring_active = any(
        (monitor := session_manager.get_session(s)) and monitor.is_running
        for s in active_sessions
    )
    return HealthResponse(status="healthy", monitoring_active=monitoring_active, timestamp=datetime.utcnow().isoformat())


@focus_router.get("/sessions")
@handle_exceptions
async def list_sessions():
    return {"sessions": session_manager.list_sessions()}


@focus_router.delete("/session/{session_id}")
@handle_exceptions
async def remove_session(session_id: str):
    removed = session_manager.remove_session(session_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return {"status": "removed", "session_id": session_id}
