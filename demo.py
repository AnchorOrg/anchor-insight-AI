#!/usr/bin/env python3
"""
Demo script for Anchor Insight AI
Shows basic functionality without requiring full setup
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def demo_scoring_system():
    """Demonstrate the scoring system with mock data."""
    logger.info("=== Anchor Insight AI Demo ===")
    
    try:
        from src.config import Config
        from src.scoring_system import ScoringSystem
        from src.notification_system import NotificationSystem
        
        # Initialize components
        config = Config()
        scoring_system = ScoringSystem(config)
        notification_system = NotificationSystem()
        
        logger.info("✓ Components initialized successfully")
        
        # Simulate analysis results
        mock_analysis_results = [
            {
                'timestamp': datetime.utcnow(),
                'distraction_analysis': {
                    'distraction_score': 0.2,  # Low distraction (good)
                    'is_distracted': False,
                    'confidence': 0.9
                },
                'behavior_analysis': {
                    'person_detected': True,
                    'presence_score': 0.95,
                    'behavior_prediction': 'focused'
                },
                'feedback_analysis': {
                    'feedback_processed': True,
                    'analysis': 'Positive feedback about the system working well'
                }
            },
            {
                'timestamp': datetime.utcnow(),
                'distraction_analysis': {
                    'distraction_score': 0.8,  # High distraction (bad)
                    'is_distracted': True,
                    'confidence': 0.7
                },
                'behavior_analysis': {
                    'person_detected': True,
                    'presence_score': 0.6,
                    'behavior_prediction': 'away'
                },
                'feedback_analysis': {}
            },
            {
                'timestamp': datetime.utcnow(),
                'distraction_analysis': {
                    'distraction_score': 0.1,  # Very focused
                    'is_distracted': False,
                    'confidence': 0.95
                },
                'behavior_analysis': {
                    'person_detected': True,
                    'presence_score': 0.98,
                    'behavior_prediction': 'focused'
                },
                'feedback_analysis': {}
            }
        ]
        
        logger.info("\n=== Processing Mock Analysis Results ===")
        
        for i, analysis_result in enumerate(mock_analysis_results, 1):
            logger.info(f"\n--- Analysis Session {i} ---")
            
            # Calculate scores
            scores = scoring_system.calculate_scores(analysis_result)
            
            # Display results
            logger.info(f"Overall Score: {scores['overall_score']:.1f}/100 (Grade: {scores['grade']})")
            
            individual_scores = scores['individual_scores']
            logger.info(f"  Distraction Score: {individual_scores['distraction_score']:.1f}/100")
            logger.info(f"  Presence Score: {individual_scores['presence_score']:.1f}/100")
            logger.info(f"  Behavior Score: {individual_scores['behavior_score']:.1f}/100")
            logger.info(f"  Feedback Score: {individual_scores['feedback_score']:.1f}/100")
            
            # Show recommendations
            recommendations = scores.get('recommendations', [])
            if recommendations:
                logger.info(f"  Recommendations: {', '.join(recommendations)}")
            
            # Process notifications
            await notification_system.process_scores(scores)
            
            # Small delay between sessions
            await asyncio.sleep(0.5)
        
        # Show notification statistics
        logger.info("\n=== Notification Statistics ===")
        notification_stats = notification_system.get_notification_stats()
        logger.info(f"Total notifications sent: {notification_stats['total_notifications']}")
        
        if notification_stats['total_notifications'] > 0:
            logger.info("Notifications by type:")
            for notif_type, count in notification_stats['by_type'].items():
                logger.info(f"  {notif_type}: {count}")
        
        # Show recent notifications
        recent_notifications = await notification_system.get_recent_notifications(limit=5)
        if recent_notifications:
            logger.info("\n=== Recent Notifications ===")
            for notification in recent_notifications:
                logger.info(f"[{notification['severity'].upper()}] {notification['title']}")
                logger.info(f"  {notification['message']}")
        
        logger.info("\n=== Demo Complete ===")
        logger.info("✓ Scoring system working correctly")
        logger.info("✓ Notification system working correctly")
        logger.info("✓ All components integrated successfully")
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Please install dependencies: pip install -r requirements.txt")
    except Exception as e:
        logger.error(f"Demo error: {e}")


def demo_config():
    """Demonstrate configuration management."""
    logger.info("\n=== Configuration Demo ===")
    
    try:
        from src.config import Config
        
        config = Config()
        logger.info(f"✓ Config loaded successfully")
        logger.info(f"  Distraction threshold: {config.distraction_threshold}")
        logger.info(f"  Presence threshold: {config.presence_threshold}")
        logger.info(f"  Camera index: {config.camera_index}")
        logger.info(f"  Frame rate: {config.frame_rate}")
        
        # Test validation
        is_valid = config.validate()
        logger.info(f"  Configuration valid: {is_valid}")
        
    except Exception as e:
        logger.error(f"Config demo error: {e}")


def show_system_requirements():
    """Show system requirements and setup information."""
    logger.info("\n=== System Requirements ===")
    logger.info("Python 3.8+")
    logger.info("Camera access for real-time analysis")
    logger.info("MongoDB for data storage (optional)")
    logger.info("Google API key for LLM features (optional)")
    
    logger.info("\n=== Installation Instructions ===")
    logger.info("1. pip install -r requirements.txt")
    logger.info("2. Copy .env.example to .env and configure")
    logger.info("3. python main.py  # Start main application")
    logger.info("4. python api.py   # Start web API server")
    
    logger.info("\n=== Features ===")
    logger.info("• Real-time camera analysis")
    logger.info("• AI-powered distraction detection")
    logger.info("• Behavioral analysis with pose detection")
    logger.info("• Smart notification system")
    logger.info("• Performance scoring and trends")
    logger.info("• RESTful API for integration")


async def main():
    """Main demo function."""
    show_system_requirements()
    demo_config()
    await demo_scoring_system()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        sys.exit(1)