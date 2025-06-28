"""Configuration management for anchor-insight-AI."""

import os
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional for basic functionality
    pass


class Config:
    """Configuration class for application settings."""
    
    def __init__(self):
        # Database configuration
        self.database_url: str = os.getenv('DATABASE_URL', 'mongodb://localhost:27017/anchor_insight')
        
        # API keys
        self.google_api_key: str = os.getenv('GOOGLE_API_KEY', '')
        
        # Model configurations
        self.vit_model_name: str = os.getenv('VIT_MODEL_NAME', 'google/vit-base-patch16-224')
        self.yolo_model_path: str = os.getenv('YOLO_MODEL_PATH', 'yolov11n.pt')
        
        # Scoring thresholds
        self.distraction_threshold: float = float(os.getenv('DISTRACTION_THRESHOLD', '0.7'))
        self.presence_threshold: float = float(os.getenv('PRESENCE_THRESHOLD', '0.8'))
        
        # Camera settings
        self.camera_index: int = int(os.getenv('CAMERA_INDEX', '0'))
        self.frame_rate: int = int(os.getenv('FRAME_RATE', '30'))
        
        # Logging
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        if not self.google_api_key:
            print("Warning: GOOGLE_API_KEY not set. LLM functionality will be limited.")
        
        if not os.path.exists('models') and not self.yolo_model_path.startswith('yolo'):
            print("Warning: YOLO model path may not be valid.")
        
        return True