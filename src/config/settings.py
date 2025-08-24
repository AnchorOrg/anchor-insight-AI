"""
Configuration settings for the anchor-insight-AI application
"""
from typing import Optional
from functools import lru_cache
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class FocusScoreSettings(BaseSettings):
    """Settings for focus score analysis service"""
    model_config = ConfigDict(
        env_prefix="", 
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    openai_api_key: str = Field(default="test-your-openai-api-key-here", description="OpenAI API key")
    model_id: str = Field(default="gpt-5", description="OpenAI model ID")
    max_file_size_mb: int = Field(default=10, description="Maximum file size in MB")
    url_timeout_seconds: int = Field(default=30, description="URL request timeout")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(default=2, description="Delay between retries")
    
    # OpenAI specific settings
    temperature: float = Field(default=1.0, description="OpenAI temperature setting")
    # Testing mode
    test_mode: bool = Field(default=False, description="Enable test mode")
    
    @field_validator('openai_api_key')
    @classmethod
    def validate_api_key(cls, v, info):
        # Allow test key in test mode  
        values = info.data if info and hasattr(info, 'data') else {}
        if values.get('test_mode', False) or v == "sk-test-key-for-testing":
            return v
            
        if not v or len(v.strip()) < 20:
            raise ValueError('OpenAI API key must be provided and valid')
        if not v.startswith(('sk-', 'sk-proj-')):
            raise ValueError('OpenAI API key must start with sk- or sk-proj-')
        return v.strip()
    
    @field_validator('max_file_size_mb')
    @classmethod
    def validate_file_size(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Max file size must be between 1 and 100 MB')
        return v
    
    @field_validator('max_retries')
    @classmethod
    def validate_retries(cls, v):
        if v < 0 or v > 10:
            raise ValueError('Max retries must be between 0 and 10')
        return v


class MonitorConfig(BaseModel):
    """Configuration for person monitoring"""
    show_window: bool = Field(default=False, description="Whether to show monitoring window")
    model_path: Optional[str] = Field(default=None, description="Path to YOLO model")
    camera_index: int = Field(default=0, description="Camera device index")


class AppSettings(BaseSettings):
    """Application settings"""
    model_config = ConfigDict(
        extra="ignore", 
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    # Environment
    environment: str = Field(default="production", description="Application environment")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8001, description="API port")
    api_reload: bool = Field(default=False, description="API reload in development")
    log_level: str = Field(default="info", description="Logging level")
    
    # Model settings
    default_model_path: str = Field(
        default=r"C:\python-env\YOLOv8-Magic\ultralytics\yolo11m-pose.pt",
        description="Default YOLO model path"
    )
    
    # Performance settings
    target_fps: int = Field(default=10, description="Target FPS for processing")
    frame_buffer_size: int = Field(default=2, description="Frame buffer size")
    camera_width: int = Field(default=640, description="Camera frame width")
    camera_height: int = Field(default=480, description="Camera frame height")
    
    # Detection settings
    confidence_threshold: float = Field(default=0.5, description="YOLO confidence threshold")
    iou_threshold: float = Field(default=0.45, description="YOLO IoU threshold")


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Cached application settings (singleton per process)."""
    return AppSettings()


@lru_cache(maxsize=1)
def get_focus_score_settings() -> FocusScoreSettings:
    """Cached focus score settings (singleton per process)."""
    return FocusScoreSettings()