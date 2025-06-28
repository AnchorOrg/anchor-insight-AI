"""Input processing module for camera, screen capture, and user feedback."""

import asyncio
import cv2
import numpy as np
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class InputProcessor:
    """Handles input from camera, screen capture, and user feedback."""
    
    def __init__(self, config):
        self.config = config
        self.camera = None
        self.is_initialized = False
        self.latest_frame = None
        self.user_feedback_queue = asyncio.Queue()
    
    async def initialize(self):
        """Initialize camera and other input sources."""
        try:
            # Initialize camera
            self.camera = cv2.VideoCapture(self.config.camera_index)
            if not self.camera.isOpened():
                raise Exception(f"Could not open camera {self.config.camera_index}")
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FPS, self.config.frame_rate)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.is_initialized = True
            logger.info("Input processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize input processor: {e}")
            raise
    
    async def get_camera_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame from camera."""
        if not self.is_initialized or not self.camera:
            return None
        
        ret, frame = self.camera.read()
        if ret:
            self.latest_frame = frame
            return frame
        return None
    
    async def get_screen_capture(self) -> Optional[np.ndarray]:
        """Get screen capture. This would integrate with Chrome extension."""
        # Placeholder for screen capture functionality
        # In a real implementation, this would receive data from Chrome extension
        # For now, return None to indicate no screen capture available
        return None
    
    async def add_user_feedback(self, feedback: str):
        """Add user feedback to the processing queue."""
        await self.user_feedback_queue.put({
            'timestamp': datetime.utcnow(),
            'feedback': feedback
        })
    
    async def get_user_feedback(self) -> Optional[Dict[str, Any]]:
        """Get the latest user feedback if available."""
        try:
            feedback = self.user_feedback_queue.get_nowait()
            return feedback
        except asyncio.QueueEmpty:
            return None
    
    async def get_input_data(self) -> Dict[str, Any]:
        """Get all available input data."""
        input_data = {
            'timestamp': datetime.utcnow(),
            'camera_frame': None,
            'screen_capture': None,
            'user_feedback': None
        }
        
        # Get camera frame
        camera_frame = await self.get_camera_frame()
        if camera_frame is not None:
            input_data['camera_frame'] = camera_frame
        
        # Get screen capture
        screen_capture = await self.get_screen_capture()
        if screen_capture is not None:
            input_data['screen_capture'] = screen_capture
        
        # Get user feedback
        user_feedback = await self.get_user_feedback()
        if user_feedback is not None:
            input_data['user_feedback'] = user_feedback
        
        return input_data
    
    async def cleanup(self):
        """Clean up resources."""
        if self.camera:
            self.camera.release()
        self.is_initialized = False
        logger.info("Input processor cleaned up")