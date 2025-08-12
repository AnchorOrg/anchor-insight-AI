"""
Data models for focus monitoring
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class StatusResponse(BaseModel):
    """Response model for monitoring status"""
    is_initialized: bool
    person_detected: Optional[bool]
    current_session: Optional[Dict[str, Any]]
    total_records: int


class SummaryResponse(BaseModel):
    """Response model for time tracking summary"""
    total_focus_minutes: float
    total_leave_minutes: float
    focus_sessions: int
    leave_sessions: int


class TimeRecord(BaseModel):
    """Model for individual time record"""
    type: str
    start: float
    end: float
    formatted: str
    duration_minutes: float


class FocusScoreResponse(BaseModel):
    """Response model for focus score"""
    focus_score: int = Field(..., ge=0, le=100, description="Focus score (0-100)")
    confidence: Optional[str] = Field(None, description="Confidence level of the analysis")
    processing_time: Optional[float] = Field(
        None, 
        description="Total processing time in seconds from request initiation to response completion. Includes image encoding, OpenAI API call latency, response parsing, and network overhead. Used for performance monitoring, API optimization, and user experience analysis."
    )


# URL analysis model removed based on TODO requirements
# The UrlRequest class has been removed to simplify the API
# and focus on file upload analysis only.


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    monitoring_active: bool
    timestamp: str


class MonitorStartResponse(BaseModel):
    """Response model for starting monitoring"""
    status: str
    message: str
    config: Dict[str, Any]


class MonitorStopResponse(BaseModel):
    """Response model for stopping monitoring"""
    status: str
    message: str
    final_stats: Dict[str, Any]


class LatestRecordResponse(BaseModel):
    """Response model for latest record"""
    latest_record: Optional[str] = None
    message: Optional[str] = None
