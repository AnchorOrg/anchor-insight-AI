"""
Main entry point for the anchor-insight-AI application.
Provides real-time scoring and notifications based on user behavior analysis.
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from src.input_processor import InputProcessor
from src.ai_models import AIModelManager
from src.scoring_system import ScoringSystem
from src.notification_system import NotificationSystem
from src.database import DatabaseManager
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnchorInsightAI:
    """Main application class for real-time AI analysis and scoring."""
    
    def __init__(self):
        self.config = Config()
        self.db_manager = DatabaseManager(self.config.database_url)
        self.input_processor = InputProcessor(self.config)
        self.ai_models = AIModelManager(self.config)
        self.scoring_system = ScoringSystem(self.config)
        self.notification_system = NotificationSystem()
        self.is_running = False
    
    async def initialize(self):
        """Initialize all components."""
        logger.info("Initializing Anchor Insight AI...")
        await self.db_manager.connect()
        await self.ai_models.load_models()
        await self.input_processor.initialize()
        logger.info("Initialization complete.")
    
    async def start_analysis(self):
        """Start the real-time analysis loop."""
        self.is_running = True
        logger.info("Starting real-time analysis...")
        
        while self.is_running:
            try:
                # Get input data
                input_data = await self.input_processor.get_input_data()
                
                if input_data:
                    # Process with AI models
                    analysis_results = await self.ai_models.analyze(input_data)
                    
                    # Calculate scores
                    scores = self.scoring_system.calculate_scores(analysis_results)
                    
                    # Store results
                    await self.db_manager.store_session_data({
                        'timestamp': datetime.utcnow(),
                        'analysis_results': analysis_results,
                        'scores': scores
                    })
                    
                    # Send notifications if needed
                    await self.notification_system.process_scores(scores)
                
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def stop_analysis(self):
        """Stop the analysis loop."""
        self.is_running = False
        logger.info("Stopping analysis...")
        await self.input_processor.cleanup()
        await self.db_manager.disconnect()
    
    async def get_current_status(self) -> Dict[str, Any]:
        """Get current system status and recent scores."""
        recent_data = await self.db_manager.get_recent_sessions(limit=1)
        if recent_data:
            return {
                'status': 'active' if self.is_running else 'inactive',
                'last_analysis': recent_data[0].get('timestamp'),
                'last_scores': recent_data[0].get('scores', {})
            }
        return {'status': 'inactive'}


async def main():
    """Main application entry point."""
    app = AnchorInsightAI()
    
    try:
        await app.initialize()
        await app.start_analysis()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal...")
    finally:
        await app.stop_analysis()


if __name__ == "__main__":
    asyncio.run(main())