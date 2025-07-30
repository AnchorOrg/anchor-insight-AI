#!/usr/bin/env python3
"""
main.py - Focus Management API Gateway
Integrates focus score analysis and time tracking services
"""
import asyncio
import base64
import time
import io
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

import httpx
import pyautogui
from PIL import Image
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import openai
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Settings(BaseSettings):
    """Application settings with environment variable support"""
    # Service endpoints
    focus_time_service_url: str = Field("http://localhost:8001", env="FOCUS_TIME_SERVICE_URL")
    focus_score_service_url: str = Field("http://localhost:8002", env="FOCUS_SCORE_SERVICE_URL")
    
    # OpenAI configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field("o3", env="OPENAI_MODEL") 
    
    # Performance settings
    http_timeout: int = Field(30, env="HTTP_TIMEOUT")
    max_concurrent_requests: int = Field(10, env="MAX_CONCURRENT_REQUESTS")
    cache_ttl_seconds: int = Field(60, env="CACHE_TTL_SECONDS")
    
    # Retry configuration
    max_retries: int = Field(3, env="MAX_RETRIES")
    retry_delay: float = Field(1.0, env="RETRY_DELAY")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Initialize OpenAI client
openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

# Global HTTP client with connection pooling
http_client: Optional[httpx.AsyncClient] = None

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
cache = SimpleCache(settings.cache_ttl_seconds)

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
    global http_client
    # Startup
    logger.info("Starting Focus Management API Gateway")
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
    )
    yield
    # Shutdown
    logger.info("Shutting down Focus Management API Gateway")
    if http_client:
        await http_client.aclose()
    cache.clear()

# Create FastAPI app
app = FastAPI(
    title="Focus Management API Gateway",
    version="3.0.0",
    description="Unified API for focus analysis and time tracking",
    lifespan=lifespan
)

# Retry decorator
async def retry_async(func, *args, max_retries: int = None, delay: float = None, **kwargs):
    """Retry an async function with exponential backoff"""
    max_retries = max_retries or settings.max_retries
    delay = delay or settings.retry_delay
    
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = delay * (2 ** attempt)  # Exponential backoff
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)

# Service communication functions
async def call_focus_time_service(endpoint: str, method: str = "GET", json_data: dict = None) -> dict:
    """Call focus time service with retry logic"""
    url = f"{settings.focus_time_service_url}{endpoint}"
    
    async def make_request():
        if method == "GET":
            response = await http_client.get(url)
        elif method == "POST":
            response = await http_client.post(url, json=json_data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    return await retry_async(make_request)

async def call_focus_score_service(image_base64: str) -> int:
    """Call focus score service with retry logic"""
    url = f"{settings.focus_score_service_url}/analyze/upload"
    
    async def make_request():
        # Convert base64 to file-like object for upload
        image_bytes = base64.b64decode(image_base64)
        files = {"file": ("screenshot.png", image_bytes, "image/png")}
        
        response = await http_client.post(url, files=files)
        response.raise_for_status()
        result = response.json()
        return result.get("focus_score", -1)
    
    return await retry_async(make_request)

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

async def get_management_suggestion(
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
        response = await openai_client.chat.completions.create(
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

# API Endpoints
@app.get("/")
async def root():
    """API information and health check"""
    return {
        "service": "Focus Management API Gateway",
        "version": "3.0.0",
        "status": "operational",
        "endpoints": {
            "/analyze": "Comprehensive focus analysis with suggestions",
            "/monitor/start": "Start person monitoring",
            "/monitor/stop": "Stop person monitoring",
            "/monitor/status": "Get monitoring status",
            "/focus/score": "Get current focus score only",
            "/time/records": "Get all time records",
            "/time/summary": "Get time statistics summary"
        },
        "services": {
            "focus_time": settings.focus_time_service_url,
            "focus_score": settings.focus_score_service_url
        }
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_focus(request: AnalysisRequest = AnalysisRequest()):
    """Comprehensive focus analysis with performance optimization"""
    start_time = time.time()
    
    # Check cache if enabled
    cache_key = f"analysis_{request.capture_screenshot}_{request.include_time_records}"
    if request.use_cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            cached_result["cached"] = True
            cached_result["processing_time_ms"] = 0
            return AnalysisResponse(**cached_result)
    
    try:
        # Prepare tasks for parallel execution
        tasks = []
        
        # Task 1: Get focus score (if requested)
        if request.capture_screenshot:
            tasks.append(("focus_score", capture_and_analyze_focus()))
        
        # Task 2: Get time summary
        tasks.append(("time_summary", call_focus_time_service("/monitor/summary")))
        
        # Task 3: Get latest record
        tasks.append(("latest_record", call_focus_time_service("/monitor/latest")))
        
        # Task 4: Get all records (if requested)
        if request.include_time_records:
            tasks.append(("all_records", call_focus_time_service("/monitor/records")))
        
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
            response_data.total_focus_minutes > 0,
            response_data.total_leave_minutes > 0
        ]):
            score = response_data.focus_score if response_data.focus_score is not None else 50
            
            suggestion = await get_management_suggestion(
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
        if request.use_cache:
            cache_dict = response_data.model_dump()
            cache_dict.pop("processing_time_ms", None)
            cache_dict.pop("cached", None)
            cache.set(cache_key, cache_dict)
        
        return response_data
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def capture_and_analyze_focus() -> int:
    """Capture screenshot and get focus score"""
    screenshot_b64 = await capture_screenshot()
    return await call_focus_score_service(screenshot_b64)

@app.post("/monitor/start")
async def start_monitor(control: MonitorControl):
    """Start person monitoring"""
    try:
        # Check current status first
        status = await call_focus_time_service("/monitor/status")
        if status.get("is_initialized", False):
            return {
                "status": "already_running",
                "message": "Monitoring is already active",
                "current_status": status
            }
        
        # Start monitoring
        config = {
            "show_window": control.show_window,
            "model_path": None,  # Use default
            "camera_index": 0
        }
        
        result = await call_focus_time_service("/monitor/start", method="POST", json_data=config)
        return result
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            return JSONResponse(status_code=200, content={
                "status": "already_running",
                "message": "Monitoring is already active"
            })
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitor/stop")
async def stop_monitor():
    """Stop person monitoring"""
    try:
        result = await call_focus_time_service("/monitor/stop", method="POST")
        
        # Clear cache when monitoring stops
        cache.clear()
        
        return result
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitor/status")
async def get_monitor_status():
    """Get monitoring status with caching"""
    cache_key = "monitor_status"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    try:
        status = await call_focus_time_service("/monitor/status")
        cache.set(cache_key, status)
        return status
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/focus/score")
async def get_focus_score_only():
    """Get current focus score only"""
    try:
        screenshot_b64 = await capture_screenshot()
        score = await call_focus_score_service(screenshot_b64)
        
        return {
            "focus_score": score,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get focus score: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/time/records")
async def get_time_records():
    """Get all time records"""
    try:
        records = await call_focus_time_service("/monitor/records")
        return records
    except Exception as e:
        logger.error(f"Failed to get records: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/time/summary")
async def get_time_summary_endpoint():
    """Get time statistics summary"""
    try:
        summary = await call_focus_time_service("/monitor/summary")
        return summary
    except Exception as e:
        logger.error(f"Failed to get summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Check focus time service
    try:
        await http_client.get(f"{settings.focus_time_service_url}/health")
        health_status["services"]["focus_time"] = "healthy"
    except Exception as e:
        health_status["services"]["focus_time"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check focus score service
    try:
        await http_client.get(f"{settings.focus_score_service_url}/health")
        health_status["services"]["focus_score"] = "healthy"
    except Exception as e:
        health_status["services"]["focus_score"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check OpenAI
    try:
        await openai_client.models.list()
        health_status["services"]["openai"] = "healthy"
    except Exception as e:
        health_status["services"]["openai"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(status_code=status_code, content=health_status)

if __name__ == "__main__":
    print("Starting Focus Management API Gateway v3.0...")
    print("Please ensure the following services are running:")
    print(f"  - Focus Time Service at {settings.focus_time_service_url}")
    print(f"  - Focus Score Service at {settings.focus_score_service_url}")
    print("\nAPI Documentation available at http://localhost:8080/docs")
    print("\nRequired environment variables:")
    print("  - OPENAI_API_KEY: Your OpenAI API key")
    print("  - FOCUS_TIME_SERVICE_URL: URL of focus time service (default: http://localhost:8001)")
    print("  - FOCUS_SCORE_SERVICE_URL: URL of focus score service (default: http://localhost:8002)")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")