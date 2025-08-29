"""
Dependency injection configuration for FastAPI IoC
"""
import logging
from typing import Annotated, Generator
from fastapi import Depends
import openai

from src.config.settings import FocusScoreSettings, get_focus_score_settings

logger = logging.getLogger(__name__)

def get_openai_client(
    settings: Annotated[FocusScoreSettings, Depends(get_focus_score_settings)]
) -> Generator[openai.AsyncOpenAI, None, None]:
    """
    Dependency provider for OpenAI client with proper lifecycle management
    Creates client instance per request and ensures proper cleanup
    """
    client = None
    try:
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        logger.debug("OpenAI client created")
        yield client
    finally:
        if client:
            # OpenAI client doesn't need explicit cleanup, but we log for monitoring
            logger.debug("OpenAI client session ended")


# Type aliases for dependency injection
SettingsDep = Annotated[FocusScoreSettings, Depends(get_focus_score_settings)]
OpenAIClientDep = Annotated[openai.AsyncOpenAI, Depends(get_openai_client)]