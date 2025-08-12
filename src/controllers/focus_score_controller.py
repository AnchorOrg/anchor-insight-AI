"""
Focus score analysis controller
"""
import time
import logging
from typing import Annotated
from fastapi import APIRouter, File, UploadFile, Depends

from src.dependencies import SettingsDep, OpenAIClientDep
from src.services.focus_score_service import FocusScoreService
from src.models.focus_models import FocusScoreResponse, HealthResponse
from src.constants.focus_constants import API_VERSION

logger = logging.getLogger(__name__)

# Create router for focus score endpoints
focus_score_router = APIRouter(prefix="/analyze", tags=["focus-score"])


def get_focus_score_service(
    client: OpenAIClientDep,
    settings: SettingsDep
) -> FocusScoreService:
    """
    Dependency provider for FocusScoreService
    Uses dependency injection to provide configured service instance
    """
    return FocusScoreService(client, settings)


# Type alias for service dependency
FocusScoreServiceDep = Annotated[FocusScoreService, Depends(get_focus_score_service)]


@focus_score_router.post("/upload", response_model=FocusScoreResponse, summary="Analyze focus by uploading image")
async def analyze_uploads(
    file: Annotated[UploadFile, File(description="User screenshot file")],
    service: FocusScoreServiceDep
):
    """
    Receive uploaded image file, encode it to Base64, and send to OpenAI for analysis.
    Uses dependency injection for service and configuration management.
    """
    # Read file content
    image_bytes = await file.read()
    
    # Use service to process the file
    return await service.analyze_uploaded_file(image_bytes, file.content_type)


# URL endpoint removed based on TODO requirements:
# "From my understanding, this should be totally deleted"
# The URL analysis functionality has been removed to simplify the API
# and focus on file upload analysis only.


@focus_score_router.get("/health", summary="Health check")
def check_health(settings: SettingsDep):
    """Basic health check endpoint"""
    return {
        "status": "ok", 
        "message": "Focus Score API is running",
        "version": API_VERSION,
        "settings": {
            "model": settings.model_id,
            "max_file_size_mb": settings.max_file_size_mb,
            "max_retries": settings.max_retries
        }
    }


@focus_score_router.get("/health/detail", summary="Detailed health check")
async def check_health_detail(service: FocusScoreServiceDep):
    """Detailed health check including OpenAI API connectivity"""
    return await service.health_check()
