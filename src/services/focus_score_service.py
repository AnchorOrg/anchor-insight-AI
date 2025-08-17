"""
Focus score analysis service
"""
import time
import base64
import asyncio
import logging
import json
from typing import Tuple

import openai
from fastapi import HTTPException

from src.config.settings import FocusScoreSettings
from src.constants.focus_constants import (
    FOCUS_ANALYSIS_PROMPT, ALLOWED_MIME_TYPES, 
    CONFIDENCE_HIGH, BYTES_PER_MB
)
from src.models.focus_models import FocusScoreResponse

logger = logging.getLogger(__name__)


class FocusScoreService:
    """Service for analyzing focus scores from images"""
    
    def __init__(self, openai_client: openai.AsyncOpenAI, settings: FocusScoreSettings):
        self.client = openai_client
        self.settings = settings
        # Store retry configuration as instance attributes
        self.max_retries = settings.max_retries
        self.retry_delay_seconds = settings.retry_delay_seconds
        
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
        last_exception = None
        
        # Retry logic using instance attributes  
        # max_retries=0 means 1 attempt, max_retries=1 means 2 attempts total
        max_attempts = max(1, self.max_retries + 1)
        for attempt in range(max_attempts):
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
                
                # Safe response parsing with validation
                if not response.choices:
                    raise ValueError("OpenAI API returned empty choices array")
                
                choice = response.choices[0]
                if not choice.message:
                    raise ValueError("OpenAI API returned choice without message")
                
                # Safe content extraction
                message_dict = choice.message.model_dump()
                content_str = message_dict.get('content')
                if not content_str:
                    raise ValueError("OpenAI API returned message without content")
                
                # Parse JSON with error handling
                try:
                    content_data = json.loads(content_str)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON response from OpenAI: {e}")
                
                # Pydantic version-compatible parsing
                try:
                    # Try Pydantic v2 first
                    if hasattr(FocusScoreResponse, 'model_validate'):
                        score_data = FocusScoreResponse.model_validate(content_data)
                    else:
                        # Fallback to Pydantic v1
                        score_data = FocusScoreResponse.parse_obj(content_data)
                except Exception as e:
                    raise ValueError(f"Failed to parse response data: {e}")
                
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
                last_exception = e
                if attempt < max_attempts - 1:
                    # Exponential backoff
                    wait_time = self.retry_delay_seconds * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {max_attempts} attempts failed")
                    
        # If we reach here, all retries failed
        logger.error(f"Unexpected error analyzing image: {last_exception}")
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
                confidence=CONFIDENCE_HIGH,
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
