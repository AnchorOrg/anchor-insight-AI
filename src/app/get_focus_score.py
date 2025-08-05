# main.py
import base64
import httpx
import openai
import uvicorn
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from typing import Annotated, Optional
import asyncio
from functools import wraps
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    model_id: str = Field("gpt-4o-mini", env="MODEL_ID")
    max_file_size_mb: int = Field(10, env="MAX_FILE_SIZE_MB")
    url_timeout_seconds: int = Field(30, env="URL_TIMEOUT_SECONDS")
    max_retries: int = Field(3, env="MAX_RETRIES")
    retry_delay_seconds: int = Field(2, env="RETRY_DELAY_SECONDS")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

app = FastAPI(
    title="Focus Analysis API",
    description="An API service that uses GPT-4o-mini to analyze screenshots and return focus scores",
    version="1.0.0"
)

# Allowed image MIME types
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", 
    "image/gif", "image/webp", "image/bmp"
}

# AsyncOpenAI client
client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

class FocusResponse(BaseModel):
    focus_score: int = Field(..., ge=0, le=100, description="Focus score (0-100)")
    confidence: Optional[str] = Field(None, description="Confidence level of the analysis")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")

class UrlRequest(BaseModel):
    image_url: str = Field(..., description="Public URL of the image to analyze")
    
    @validator('image_url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

PROMPT = (
    "This is a screenshot taken from a user's computer screen. Please analyze the probability of the user being distracted at this moment.\n"
    "Note: To assess distraction probability, consider whether the user is working, such as using code editors, video editors, work software, etc., "
    "or analyze whether the screenshot shows a webpage and what content it contains. If watching a video, is it work-related? "
    "For example, if watching educational videos, consider it as working or studying; if watching entertainment or gaming videos, consider it as resting or being distracted.\n"
    "Please directly output a focus attention score, where 0 means completely distracted and 100 means highly focused. "
    "You can freely choose a score between 0-100 to evaluate the user's attention focus level.\n"
    "Please return in JSON format: {\"focus_score\": number}"
)

def retry_on_failure(max_retries: int = 3, delay: int = 2):
    """Decorator for retry logic"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed")
            raise last_exception
        return wrapper
    return decorator

@retry_on_failure(max_retries=settings.max_retries, delay=settings.retry_delay_seconds)
async def get_focus_score_from_openai(img_b64: str) -> tuple[int, float]:
    """Asynchronously call OpenAI API and parse focus score with retry logic"""
    start_time = time.time()
    
    try:
        # Use async method `client.chat.completions.create`
        response = await client.chat.completions.create(
            model=settings.model_id,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a focus analysis assistant that only returns JSON."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                        },
                    ],
                },
            ],
            temperature=0.1,  # Lower randomness for more stable results
            max_tokens=1000
        )
        
        payload = response.choices[0].message.model_dump()
        score_data = openai.pydantic_v1.parse_raw_as(FocusResponse, payload['content'])
        score = score_data.focus_score

        if not (0 <= score <= 100):
            raise ValueError(f"Returned score is out of valid range: {score}")
        
        processing_time = time.time() - start_time
        logger.info(f"Successfully analyzed image, score: {score}, time: {processing_time:.2f}s")
        
        return score, processing_time
            
    except openai.APIError as e:
        logger.error(f"OpenAI API Error: {e}")
        raise HTTPException(status_code=502, detail="External API service error")
    except Exception as e:
        logger.error(f"Unknown error occurred while parsing response: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")

@app.post("/analyze/upload", response_model=FocusResponse, summary="Analyze focus by uploading image")
async def analyze_from_upload(file: Annotated[UploadFile, File(description="User screenshot file")]):
    """
    Receive uploaded image file, encode it to Base64, and send to OpenAI for analysis.
    """
    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    # Asynchronously read file content
    image_bytes = await file.read()
    
    # Validate file size
    file_size_mb = len(image_bytes) / (1024 * 1024)
    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=400, 
            detail=f"File size {file_size_mb:.2f}MB exceeds maximum allowed size of {settings.max_file_size_mb}MB"
        )
    
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    
    try:
        img_b64 = base64.b64encode(image_bytes).decode('utf-8')
        score, processing_time = await get_focus_score_from_openai(img_b64)
        
        return FocusResponse(
            focus_score=score,
            confidence="high" if 0 <= score <= 100 else "low",
            processing_time=processing_time
        )
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        raise

@app.post("/analyze/url", response_model=FocusResponse, summary="Analyze focus by image URL")
async def analyze_from_url(request: UrlRequest):
    """
    Download image from given URL, encode it to Base64, and send to OpenAI for analysis.
    """
    try:
        # Use async HTTP client to fetch image with extended timeout
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.get(
                request.image_url, 
                timeout=settings.url_timeout_seconds,
                follow_redirects=True
            )
            resp.raise_for_status()  # Raise exception if HTTP status code is not 2xx
            
            # Validate content type
            content_type = resp.headers.get('content-type', '').lower()
            if not any(allowed in content_type for allowed in ALLOWED_MIME_TYPES):
                raise HTTPException(
                    status_code=400, 
                    detail=f"URL does not point to a valid image. Content-Type: {content_type}"
                )
            
            image_bytes = resp.content
            
            # Validate downloaded file size
            file_size_mb = len(image_bytes) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Image size {file_size_mb:.2f}MB exceeds maximum allowed size of {settings.max_file_size_mb}MB"
                )

        img_b64 = base64.b64encode(image_bytes).decode('utf-8')
        score, processing_time = await get_focus_score_from_openai(img_b64)
        
        return FocusResponse(
            focus_score=score,
            confidence="high" if 0 <= score <= 100 else "low",
            processing_time=processing_time
        )
    except httpx.RequestError as e:
        logger.error(f"Error fetching image from URL: {e}")
        raise HTTPException(status_code=400, detail=f"Unable to fetch image from URL: {e}")
    except Exception as e:
        logger.error(f"Error processing URL image: {e}")
        raise

@app.get("/", summary="Health check")
def read_root():
    return {
        "status": "ok", 
        "message": "Focus Score API is running",
        "version": "1.0.0",
        "settings": {
            "model": settings.model_id,
            "max_file_size_mb": settings.max_file_size_mb,
            "max_retries": settings.max_retries
        }
    }

@app.get("/health", summary="Detailed health check")
async def health_check():
    """Perform detailed health check including OpenAI API connectivity"""
    try:
        # Test OpenAI API connectivity
        test_response = await client.models.list()
        openai_status = "connected" if test_response else "unknown"
    except Exception as e:
        openai_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "openai_api": openai_status,
        "timestamp": time.time()
    }

if __name__ == "__main__":
    logger.info(f"Starting Focus Score API with model: {settings.model_id}")
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)