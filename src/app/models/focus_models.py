#!/usr/bin/env python3
"""
models/focus_models.py - Data models for focus management system
"""
# TODO: i think pydantic is needed.
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# TODO: rmove all contens of the below. since they are merely for reference purpose.
# the below are merley for reference purpose. Please let me know whether @Wang want to have the perosnal purchase on the copilot license or with a team guaranteed one. 
class FocusScoreRequest(BaseModel):
    """Request model for focus score analysis"""
    image_base64: str = Field(..., description="Base64 encoded image")
    

class FocusScoreResponse(BaseModel):
    """Response model for focus score analysis"""
    focus_score: int = Field(..., description="Focus score from 0 to 100")
    timestamp: str = Field(..., description="Analysis timestamp")
    confidence: Optional[float] = Field(None, description="Confidence level")


class MonitoringConfig(BaseModel):
    """Configuration for person monitoring"""
    show_window: bool = Field(False, description="Whether to show monitoring window")
    camera_index: int = Field(0, description="Camera index to use")
    model_path: Optional[str] = Field(None, description="Path to YOLO model")


class MonitoringStatus(BaseModel):
    """Status of person monitoring"""
    is_initialized: bool = Field(..., description="Whether monitoring is initialized")
    is_running: bool = Field(..., description="Whether monitoring is currently running")
    camera_active: bool = Field(..., description="Whether camera is active")
    person_detected: bool = Field(..., description="Whether person is currently detected")
    current_state: str = Field(..., description="Current monitoring state")


class TimeRecord(BaseModel):
    """Individual time record"""
    timestamp: datetime = Field(..., description="Record timestamp")
    state: str = Field(..., description="State (focus/leave)")
    duration: Optional[float] = Field(None, description="Duration in minutes")
    formatted: str = Field(..., description="Formatted time record string")


class TimeSummary(BaseModel):
    """Summary of time records"""
    total_focus_minutes: float = Field(..., description="Total focus time in minutes")
    total_leave_minutes: float = Field(..., description="Total leave time in minutes")
    focus_sessions: int = Field(..., description="Number of focus sessions")
    leave_sessions: int = Field(..., description="Number of leave sessions")
    latest_record: Optional[str] = Field(None, description="Latest time record")


class AnalysisRequest(BaseModel):
    """Request model for comprehensive analysis"""
    capture_screenshot: bool = Field(True, description="Whether to capture screenshot")
    include_time_records: bool = Field(True, description="Whether to include detailed time records")
    use_cache: bool = Field(True, description="Whether to use cached results")


class AnalysisResponse(BaseModel):
    """Response model for comprehensive analysis"""
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


class HealthStatus(BaseModel):
    """Health status model"""
    status: str = Field(..., description="Overall status")
    timestamp: str = Field(..., description="Check timestamp")
    services: dict = Field(..., description="Individual service statuses")


class ApiInfo(BaseModel):
    """API information model"""
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    status: str = Field(..., description="Service status")
    endpoints: dict = Field(..., description="Available endpoints")
    services: dict = Field(..., description="Connected services")
