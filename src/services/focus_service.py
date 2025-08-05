#!/usr/bin/env python3
"""
services/focus_service.py - Business logic for focus analysis
"""
import asyncio
import base64
import time
import io
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

import httpx
import pyautogui
from PIL import Image
import openai

from ..config.settings import settings
from ..models.focus_models import (
    FocusScoreResponse, TimeSummary, AnalysisResponse, 
    TimeRecord, MonitoringStatus, MonitoringConfig
)

logger = logging.getLogger(__name__)


class HttpService:
    """HTTP client service for external API calls"""
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self):
        """Initialize HTTP client"""
        if not self.client:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.http_timeout),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
            )
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def get(self, url: str) -> dict:
        """Make GET request"""
        if not self.client:
            await self.initialize()
        
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()
    
    async def post(self, url: str, json_data: dict = None, files: dict = None) -> dict:
        """Make POST request"""
        if not self.client:
            await self.initialize()
        
        if files:
            response = await self.client.post(url, files=files)
        else:
            response = await self.client.post(url, json=json_data)
        
        response.raise_for_status()
        return response.json()


class CacheService:
    """Simple in-memory cache service"""
    
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple[Any, float]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set cached value"""
        self.cache[key] = (value, time.time())
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()


class ScreenshotService:
    """Service for capturing screenshots"""
    
    @staticmethod
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


class FocusScoreService:
    """Service for focus score analysis"""
    
    def __init__(self, http_service: HttpService):
        self.http_service = http_service
    
    async def analyze_focus_score(self, image_base64: str) -> int:
        """Analyze focus score from image"""
        url = f"{settings.focus_score_service_url}/analyze/upload"
        
        # Convert base64 to file-like object for upload
        image_bytes = base64.b64decode(image_base64)
        files = {"file": ("screenshot.png", image_bytes, "image/png")}
        
        result = await self.http_service.post(url, files=files)
        return result.get("focus_score", -1)


class TimeTrackingService:
    """Service for time tracking operations"""
    
    def __init__(self, http_service: HttpService):
        self.http_service = http_service
    
    async def start_monitoring(self, config: MonitoringConfig) -> dict:
        """Start person monitoring"""
        url = f"{settings.focus_time_service_url}/monitor/start"
        config_dict = {
            "show_window": config.show_window,
            "model_path": config.model_path,
            "camera_index": config.camera_index
        }
        return await self.http_service.post(url, json_data=config_dict)
    
    async def stop_monitoring(self) -> dict:
        """Stop person monitoring"""
        url = f"{settings.focus_time_service_url}/monitor/stop"
        return await self.http_service.post(url)
    
    async def get_monitoring_status(self) -> dict:
        """Get monitoring status"""
        url = f"{settings.focus_time_service_url}/monitor/status"
        return await self.http_service.get(url)
    
    async def get_time_summary(self) -> dict:
        """Get time summary"""
        url = f"{settings.focus_time_service_url}/monitor/summary"
        return await self.http_service.get(url)
    
    async def get_latest_record(self) -> dict:
        """Get latest time record"""
        url = f"{settings.focus_time_service_url}/monitor/latest"
        return await self.http_service.get(url)
    
    async def get_all_records(self) -> dict:
        """Get all time records"""
        url = f"{settings.focus_time_service_url}/monitor/records"
        return await self.http_service.get(url)


class OpenAIService:
    """Service for OpenAI operations"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def generate_management_suggestion(
        self,
        focus_score: int,
        focus_minutes: float,
        leave_minutes: float,
        time_records: List[str]
    ) -> str:
        """Generate management suggestions using OpenAI"""
        # Prepare prompt with recent records
        recent_records = "\n".join(time_records[-10:]) if time_records else "No time records available"
        
        prompt = f"""As a productivity and time management expert, analyze the following user data and provide specific, actionable recommendations:

Focus Score: {focus_score}/100
Total Focus Time: {focus_minutes:.1f} minutes
Total Leave Time: {leave_minutes:.1f} minutes

Recent Time Records:
{recent_records}

Based on this data, provide:
1. An assessment of the current productivity pattern
2. Specific recommendations for improving focus and time management
3. Suggested work-rest balance adjustments
4. Practical tips for maintaining concentration

Keep the response concise and actionable."""

        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional productivity coach specializing in data-driven time management and focus optimization."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating suggestion: {e}")
            return f"Unable to generate suggestions at this time. Error: {str(e)}"


class FocusAnalysisService:
    """Main service for comprehensive focus analysis"""
    
    def __init__(self):
        self.http_service = HttpService()
        self.cache_service = CacheService(settings.cache_ttl_seconds)
        self.screenshot_service = ScreenshotService()
        self.focus_score_service = FocusScoreService(self.http_service)
        self.time_tracking_service = TimeTrackingService(self.http_service)
        self.openai_service = OpenAIService()
    
    async def initialize(self):
        """Initialize all services"""
        await self.http_service.initialize()
    
    async def close(self):
        """Close all services"""
        await self.http_service.close()
        self.cache_service.clear()
    
    async def comprehensive_analysis(
        self,
        capture_screenshot: bool = True,
        include_time_records: bool = True,
        use_cache: bool = True
    ) -> AnalysisResponse:
        """Perform comprehensive focus analysis"""
        start_time = time.time()
        
        # Check cache if enabled
        cache_key = f"analysis_{capture_screenshot}_{include_time_records}"
        if use_cache:
            cached_result = self.cache_service.get(cache_key)
            if cached_result:
                cached_result["cached"] = True
                cached_result["processing_time_ms"] = 0
                return AnalysisResponse(**cached_result)
        
        try:
            # Prepare tasks for parallel execution
            tasks = []
            
            # Task 1: Get focus score (if requested)
            if capture_screenshot:
                tasks.append(("focus_score", self._capture_and_analyze_focus()))
            
            # Task 2: Get time summary
            tasks.append(("time_summary", self.time_tracking_service.get_time_summary()))
            
            # Task 3: Get latest record
            tasks.append(("latest_record", self.time_tracking_service.get_latest_record()))
            
            # Task 4: Get all records (if requested)
            if include_time_records:
                tasks.append(("all_records", self.time_tracking_service.get_all_records()))
            
            # Execute tasks concurrently
            results = {}
            task_coroutines = [task[1] for task in tasks]
            task_names = [task[0] for task in tasks]
            
            completed_tasks = await asyncio.gather(*task_coroutines, return_exceptions=True)
            
            for name, result in zip(task_names, completed_tasks):
                if isinstance(result, Exception):
                    logger.error(f"Task {name} failed: {result}")
                    results[name] = None
                else:
                    results[name] = result
            
            # Build response
            response_data = AnalysisResponse()
            
            # Process focus score
            if "focus_score" in results and results["focus_score"] is not None:
                response_data.focus_score = results["focus_score"]
            
            # Process time summary
            if "time_summary" in results and results["time_summary"]:
                summary = results["time_summary"]
                response_data.total_focus_minutes = summary.get("total_focus_minutes", 0)
                response_data.total_leave_minutes = summary.get("total_leave_minutes", 0)
                response_data.focus_sessions = summary.get("focus_sessions", 0)
                response_data.leave_sessions = summary.get("leave_sessions", 0)
            
            # Process latest record
            if "latest_record" in results and results["latest_record"]:
                latest = results["latest_record"]
                response_data.latest_time_record = latest.get("latest_record")
            
            # Process all records
            time_records = []
            if "all_records" in results and results["all_records"]:
                records = results["all_records"].get("records", [])
                response_data.all_time_records = [record["formatted"] for record in records]
                time_records = response_data.all_time_records
            
            # Generate suggestion if we have data
            if any([
                response_data.focus_score is not None and response_data.focus_score >= 0,
                response_data.total_focus_minutes and response_data.total_focus_minutes > 0,
                response_data.total_leave_minutes and response_data.total_leave_minutes > 0
            ]):
                score = response_data.focus_score if response_data.focus_score is not None else 50
                
                suggestion = await self.openai_service.generate_management_suggestion(
                    score,
                    response_data.total_focus_minutes or 0,
                    response_data.total_leave_minutes or 0,
                    time_records
                )
                response_data.suggestion = suggestion
            else:
                response_data.suggestion = "Insufficient data for analysis. Please ensure monitoring is active and screenshot capture is enabled."
            
            # Calculate processing time
            response_data.processing_time_ms = (time.time() - start_time) * 1000
            
            # Cache the result
            if use_cache:
                cache_dict = response_data.model_dump()
                cache_dict.pop("processing_time_ms", None)
                cache_dict.pop("cached", None)
                self.cache_service.set(cache_key, cache_dict)
            
            return response_data
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return AnalysisResponse(error=str(e))
    
    async def _capture_and_analyze_focus(self) -> int:
        """Capture screenshot and get focus score"""
        screenshot_b64 = await self.screenshot_service.capture_screenshot()
        return await self.focus_score_service.analyze_focus_score(screenshot_b64)
    
    async def get_focus_score_only(self) -> FocusScoreResponse:
        """Get current focus score only"""
        screenshot_b64 = await self.screenshot_service.capture_screenshot()
        score = await self.focus_score_service.analyze_focus_score(screenshot_b64)
        
        return FocusScoreResponse(
            focus_score=score,
            timestamp=datetime.now().isoformat()
        )
