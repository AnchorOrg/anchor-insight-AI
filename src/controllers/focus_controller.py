#!/usr/bin/env python3
"""
controllers/focus_controller.py - API controllers for focus management
"""
from fastapi import HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from ..models.focus_models import (
    AnalysisRequest, AnalysisResponse, MonitoringConfig,
    FocusScoreResponse, HealthStatus, ApiInfo
)
from ..services.focus_service import FocusAnalysisService
from ..config.settings import settings

logger = logging.getLogger(__name__)


class FocusController:
    """Controller for focus-related API endpoints"""
    
    def __init__(self):
        self.focus_service = FocusAnalysisService()
    
    async def initialize(self):
        """Initialize the controller and its services"""
        await self.focus_service.initialize()
    
    async def close(self):
        """Close the controller and its services"""
        await self.focus_service.close()
    
    async def get_api_info(self) -> ApiInfo:
        """Get API information and health check"""
        return ApiInfo(
            service="Focus Management API Gateway",
            version="3.0.0",
            status="operational",
            endpoints={
                "/analyze": "Comprehensive focus analysis with suggestions",
                "/monitor/start": "Start person monitoring",
                "/monitor/stop": "Stop person monitoring",
                "/monitor/status": "Get monitoring status",
                "/focus/score": "Get current focus score only",
                "/time/records": "Get all time records",
                "/time/summary": "Get time statistics summary"
            },
            services={
                "focus_time": settings.focus_time_service_url,
                "focus_score": settings.focus_score_service_url
            }
        )
    
    async def analyze_focus(self, request: AnalysisRequest) -> AnalysisResponse:
        """Comprehensive focus analysis with performance optimization"""
        try:
            return await self.focus_service.comprehensive_analysis(
                capture_screenshot=request.capture_screenshot,
                include_time_records=request.include_time_records,
                use_cache=request.use_cache
            )
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def start_monitor(self, control: MonitoringConfig) -> dict:
        """Start person monitoring"""
        try:
            # Check current status first
            status = await self.focus_service.time_tracking_service.get_monitoring_status()
            if status.get("is_initialized", False):
                return {
                    "status": "already_running",
                    "message": "Monitoring is already active",
                    "current_status": status
                }
            
            # Start monitoring
            result = await self.focus_service.time_tracking_service.start_monitoring(control)
            return result
            
        except Exception as e:
            if "400" in str(e):
                return JSONResponse(status_code=200, content={
                    "status": "already_running",
                    "message": "Monitoring is already active"
                })
            logger.error(f"Failed to start monitoring: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def stop_monitor(self) -> dict:
        """Stop person monitoring"""
        try:
            result = await self.focus_service.time_tracking_service.stop_monitoring()
            
            # Clear cache when monitoring stops
            self.focus_service.cache_service.clear()
            
            return result
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_monitor_status(self) -> dict:
        """Get monitoring status with caching"""
        cache_key = "monitor_status"
        cached = self.focus_service.cache_service.get(cache_key)
        if cached:
            return cached
        
        try:
            status = await self.focus_service.time_tracking_service.get_monitoring_status()
            self.focus_service.cache_service.set(cache_key, status)
            return status
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_focus_score_only(self) -> FocusScoreResponse:
        """Get current focus score only"""
        try:
            return await self.focus_service.get_focus_score_only()
        except Exception as e:
            logger.error(f"Failed to get focus score: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_time_records(self) -> dict:
        """Get all time records"""
        try:
            return await self.focus_service.time_tracking_service.get_all_records()
        except Exception as e:
            logger.error(f"Failed to get records: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_time_summary(self) -> dict:
        """Get time statistics summary"""
        try:
            return await self.focus_service.time_tracking_service.get_time_summary()
        except Exception as e:
            logger.error(f"Failed to get summary: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def health_check(self) -> HealthStatus:
        """Comprehensive health check"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        # Check focus time service
        try:
            await self.focus_service.http_service.get(f"{settings.focus_time_service_url}/health")
            health_status["services"]["focus_time"] = "healthy"
        except Exception as e:
            health_status["services"]["focus_time"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check focus score service
        try:
            await self.focus_service.http_service.get(f"{settings.focus_score_service_url}/health")
            health_status["services"]["focus_score"] = "healthy"
        except Exception as e:
            health_status["services"]["focus_score"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check OpenAI
        try:
            await self.focus_service.openai_service.client.models.list()
            health_status["services"]["openai"] = "healthy"
        except Exception as e:
            health_status["services"]["openai"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        return HealthStatus(**health_status)
