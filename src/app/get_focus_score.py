# main.py
import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.controllers.focus_score_controller import focus_score_router
from src.constants.focus_constants import API_TITLE, API_DESCRIPTION, API_VERSION
from src.dependencies import get_focus_score_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Focus Score API")
    yield
    logger.info("Focus Score API shutdown complete")


app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan
)

# Include focus score router
app.include_router(focus_score_router)

# Export settings for testing purposes
settings = get_focus_score_settings()

# Entry point configuration - this file serves as the single main entry point
# for the focus score API service, providing clean separation from other services
if __name__ == "__main__":
    settings = get_focus_score_settings()
    logger.info(f"Starting Focus Score API with model: {settings.model_id}")
    uvicorn.run("get_focus_score:app", host="127.0.0.1", port=8002, reload=True)