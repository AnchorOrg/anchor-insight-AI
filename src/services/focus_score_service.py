"""
Focus score analysis service
"""
import time
import base64
import asyncio
import logging
from typing import Tuple
from functools import wraps

import openai
import httpx
from fastapi import HTTPException

from src.config.settings import FocusScoreSettings
from src.constants.focus_constants import (
    FOCUS_ANALYSIS_PROMPT, ALLOWED_MIME_TYPES, 
    CONFIDENCE_HIGH, CONFIDENCE_LOW, BYTES_PER_MB
)
from src.models.focus_models import FocusScoreResponse

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: int = 2):
    """Decorator for retry logic with exponential backoff"""
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
                        # Exponential backoff
                        wait_time = delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed")
            raise last_exception
        return wrapper
    return decorator


class FocusScoreService:
    """Service for analyzing focus scores from images"""
    
    def __init__(self, openai_client: openai.AsyncOpenAI, settings: FocusScoreSettings):
        self.client = openai_client
        self.settings = settings
        
    @retry_on_failure()
    async def analyze_image_base64(self, img_b64: str) -> Tuple[int, float]:
        """
        Analyze focus score from base64 encoded image
        
        Args:
            img_b64: Base64 encoded image string
            
        Returns:
            Tuple of (focus_score, processing_time)
            
        Raises:
            HTTPException: For API errors or invalid responses
        """
        start_time = time.time()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.model_id,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a focus analysis assistant that only returns JSON."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": FOCUS_ANALYSIS_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                            },
                        ],
                    },
                ],
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens
            )
            
            payload = response.choices[0].message.model_dump()
            score_data = openai.pydantic_v1.parse_raw_as(FocusScoreResponse, payload['content'])
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
    
    async def analyze_uploaded_file(self, file_content: bytes, content_type: str) -> FocusScoreResponse:
        """
        Analyze focus score from uploaded file
        
        Args:
            file_content: Raw file bytes
            content_type: MIME type of the file
            
        Returns:
            FocusScoreResponse with score and metadata
            
        Raises:
            HTTPException: For validation errors or processing failures
        """
        # Validate file type
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
            )
        
        # Validate file size
        file_size_mb = len(file_content) / BYTES_PER_MB
        if file_size_mb > self.settings.max_file_size_mb:
            raise HTTPException(
                status_code=400, 
                detail=f"File size {file_size_mb:.2f}MB exceeds maximum allowed size of {self.settings.max_file_size_mb}MB"
            )
        
        if not file_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        try:
            img_b64 = base64.b64encode(file_content).decode('utf-8')
            score, processing_time = await self.analyze_image_base64(img_b64)
            
            return FocusScoreResponse(
                focus_score=score,
                confidence=CONFIDENCE_HIGH if 0 <= score <= 100 else CONFIDENCE_LOW,
                processing_time=processing_time
            )
        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            raise
    
    # URL analysis method removed based on TODO requirements
    # The analyze_image_url method has been removed to simplify the service
    # and focus on file upload analysis only.
    
    async def health_check(self) -> dict:
        """
        Perform health check for the service
        
        Returns:
            Health status dictionary
        """
        try:
            # Test OpenAI API connectivity
            test_response = await self.client.models.list()
            openai_status = "connected" if test_response else "unknown"
        except Exception as e:
            openai_status = f"error: {str(e)}"
        
        return {
            "status": "healthy",
            "openai_api": openai_status,
            "timestamp": time.time(),
            "settings": {
                "model": self.settings.model_id,
                "max_file_size_mb": self.settings.max_file_size_mb,
                "max_retries": self.settings.max_retries
            }
        }
