"""AI models integration for ViT, YOLO, and LLM analysis."""

import asyncio
import logging
import cv2
import numpy as np
from typing import Dict, Any, Optional
from PIL import Image
import torch
from transformers import ViTImageProcessor, ViTForImageClassification
from ultralytics import YOLO
import google.generativeai as genai

logger = logging.getLogger(__name__)


class AIModelManager:
    """Manages AI models for image analysis and user behavior detection."""
    
    def __init__(self, config):
        self.config = config
        self.vit_model = None
        self.vit_processor = None
        self.yolo_model = None
        self.genai_configured = False
        self.models_loaded = False
    
    async def load_models(self):
        """Load all AI models."""
        try:
            # Load ViT model for distraction analysis
            await self._load_vit_model()
            
            # Load YOLO model for pose detection
            await self._load_yolo_model()
            
            # Configure Google Generative AI
            await self._configure_genai()
            
            self.models_loaded = True
            logger.info("All AI models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load AI models: {e}")
            raise
    
    async def _load_vit_model(self):
        """Load Vision Transformer model for image classification."""
        try:
            self.vit_processor = ViTImageProcessor.from_pretrained(self.config.vit_model_name)
            self.vit_model = ViTForImageClassification.from_pretrained(self.config.vit_model_name)
            logger.info("ViT model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ViT model: {e}")
            raise
    
    async def _load_yolo_model(self):
        """Load YOLO model for pose detection."""
        try:
            self.yolo_model = YOLO(self.config.yolo_model_path)
            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise
    
    async def _configure_genai(self):
        """Configure Google Generative AI."""
        try:
            if self.config.google_api_key:
                genai.configure(api_key=self.config.google_api_key)
                self.genai_configured = True
                logger.info("Google Generative AI configured successfully")
            else:
                logger.warning("Google API key not provided, LLM features disabled")
        except Exception as e:
            logger.error(f"Failed to configure Google Generative AI: {e}")
    
    async def analyze_distraction(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze image for distraction indicators using ViT."""
        if not self.vit_model or not self.vit_processor:
            return {'error': 'ViT model not loaded'}
        
        try:
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Process image
            inputs = self.vit_processor(images=pil_image, return_tensors="pt")
            
            # Get predictions
            with torch.no_grad():
                outputs = self.vit_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Calculate distraction score (this is simplified - in reality you'd need
            # a model specifically trained for distraction detection)
            distraction_score = float(torch.max(predictions))
            
            return {
                'distraction_score': distraction_score,
                'is_distracted': distraction_score < self.config.distraction_threshold,
                'confidence': float(torch.max(predictions))
            }
            
        except Exception as e:
            logger.error(f"Error in distraction analysis: {e}")
            return {'error': str(e)}
    
    async def analyze_user_behavior(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze user behavior using YOLO pose detection."""
        if not self.yolo_model:
            return {'error': 'YOLO model not loaded'}
        
        try:
            # Run YOLO inference
            results = self.yolo_model(image)
            
            # Extract keypoints and analyze behavior
            behavior_data = {
                'person_detected': False,
                'presence_score': 0.0,
                'pose_data': {},
                'behavior_prediction': 'unknown'
            }
            
            for result in results:
                if result.boxes:
                    # Person detected
                    behavior_data['person_detected'] = True
                    
                    # Calculate presence score based on detection confidence
                    max_confidence = max([box.conf.item() for box in result.boxes])
                    behavior_data['presence_score'] = float(max_confidence)
                    
                    # Simple behavior prediction based on presence
                    if max_confidence > self.config.presence_threshold:
                        behavior_data['behavior_prediction'] = 'focused'
                    else:
                        behavior_data['behavior_prediction'] = 'away'
                
                # Extract pose keypoints if available
                if hasattr(result, 'keypoints') and result.keypoints:
                    behavior_data['pose_data'] = {
                        'keypoints': result.keypoints.xy.tolist() if result.keypoints.xy is not None else []
                    }
            
            return behavior_data
            
        except Exception as e:
            logger.error(f"Error in behavior analysis: {e}")
            return {'error': str(e)}
    
    async def analyze_feedback(self, feedback_text: str) -> Dict[str, Any]:
        """Analyze user feedback using LLM."""
        if not self.genai_configured:
            return {'error': 'Google Generative AI not configured'}
        
        try:
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""
            Analyze the following user feedback and provide insights:
            "{feedback_text}"
            
            Please provide:
            1. Sentiment (positive/negative/neutral)
            2. Key concerns or issues mentioned
            3. Suggestions for improvement
            4. Urgency level (low/medium/high)
            
            Respond in JSON format.
            """
            
            response = await asyncio.create_task(
                asyncio.to_thread(model.generate_content, prompt)
            )
            
            return {
                'analysis': response.text,
                'feedback_processed': True
            }
            
        except Exception as e:
            logger.error(f"Error in feedback analysis: {e}")
            return {'error': str(e)}
    
    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze all input data using appropriate models."""
        analysis_results = {
            'timestamp': input_data['timestamp'],
            'distraction_analysis': {},
            'behavior_analysis': {},
            'feedback_analysis': {}
        }
        
        # Analyze camera frame for distraction
        if input_data.get('camera_frame') is not None:
            analysis_results['distraction_analysis'] = await self.analyze_distraction(
                input_data['camera_frame']
            )
            
            # Also analyze camera frame for behavior
            analysis_results['behavior_analysis'] = await self.analyze_user_behavior(
                input_data['camera_frame']
            )
        
        # Analyze screen capture (if available)
        if input_data.get('screen_capture') is not None:
            screen_distraction = await self.analyze_distraction(
                input_data['screen_capture']
            )
            analysis_results['screen_distraction_analysis'] = screen_distraction
        
        # Analyze user feedback
        if input_data.get('user_feedback'):
            feedback_text = input_data['user_feedback'].get('feedback', '')
            if feedback_text:
                analysis_results['feedback_analysis'] = await self.analyze_feedback(
                    feedback_text
                )
        
        return analysis_results