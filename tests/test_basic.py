"""Basic tests for anchor-insight-AI functionality."""

import unittest
import asyncio
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.config import Config
from src.scoring_system import ScoringSystem
from src.notification_system import NotificationSystem


class TestScoringSystem(unittest.TestCase):
    """Test the scoring system functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config()
        self.scoring_system = ScoringSystem(self.config)
    
    def test_calculate_distraction_score(self):
        """Test distraction score calculation."""
        # Test high distraction (low score)
        distraction_analysis = {
            'distraction_score': 0.3,
            'is_distracted': True,
            'confidence': 0.8
        }
        score = self.scoring_system.calculate_distraction_score(distraction_analysis)
        self.assertLess(score, 50)  # Should be low score for high distraction
        
        # Test low distraction (high score)
        distraction_analysis = {
            'distraction_score': 0.9,
            'is_distracted': False,
            'confidence': 0.9
        }
        score = self.scoring_system.calculate_distraction_score(distraction_analysis)
        self.assertGreater(score, 80)  # Should be high score for low distraction
    
    def test_calculate_presence_score(self):
        """Test presence score calculation."""
        # Test person detected
        behavior_analysis = {
            'person_detected': True,
            'presence_score': 0.9,
            'behavior_prediction': 'focused'
        }
        score = self.scoring_system.calculate_presence_score(behavior_analysis)
        self.assertGreater(score, 80)
        
        # Test no person detected
        behavior_analysis = {
            'person_detected': False,
            'presence_score': 0.0,
            'behavior_prediction': 'away'
        }
        score = self.scoring_system.calculate_presence_score(behavior_analysis)
        self.assertEqual(score, 0.0)
    
    def test_calculate_overall_score(self):
        """Test overall score calculation."""
        individual_scores = {
            'distraction_score': 80.0,
            'presence_score': 90.0,
            'behavior_score': 85.0,
            'feedback_score': 75.0
        }
        
        overall_score = self.scoring_system.calculate_overall_score(individual_scores)
        self.assertGreater(overall_score, 70)
        self.assertLess(overall_score, 100)
    
    def test_get_grade(self):
        """Test grade assignment."""
        self.assertEqual(self.scoring_system._get_grade(95), 'A')
        self.assertEqual(self.scoring_system._get_grade(85), 'B')
        self.assertEqual(self.scoring_system._get_grade(75), 'C')
        self.assertEqual(self.scoring_system._get_grade(65), 'D')
        self.assertEqual(self.scoring_system._get_grade(45), 'F')


class TestNotificationSystem(unittest.TestCase):
    """Test the notification system functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.notification_system = NotificationSystem()
    
    def test_notification_cooldown(self):
        """Test notification cooldown logic."""
        # This would need to be tested with actual time delays
        # For now, just test that the method exists and runs
        asyncio.run(self._test_notification_cooldown_async())
    
    async def _test_notification_cooldown_async(self):
        """Async test for notification cooldown."""
        notification = {
            'type': 'test',
            'severity': 'info',
            'title': 'Test Notification',
            'message': 'This is a test',
            'recommendations': []
        }
        
        # Send first notification
        await self.notification_system.send_notification(notification)
        self.assertEqual(len(self.notification_system.notification_history), 1)
        
        # Send same type immediately (should be blocked by cooldown)
        await self.notification_system.send_notification(notification)
        # Still should be 1 due to cooldown
        self.assertEqual(len(self.notification_system.notification_history), 1)
    
    def test_get_notification_stats(self):
        """Test notification statistics."""
        # Test with empty history
        stats = self.notification_system.get_notification_stats()
        self.assertEqual(stats['total_notifications'], 0)
        
        # Add some mock notifications
        self.notification_system.notification_history = [
            {'type': 'alert', 'severity': 'high', 'timestamp': datetime.now()},
            {'type': 'info', 'severity': 'low', 'timestamp': datetime.now()},
            {'type': 'alert', 'severity': 'medium', 'timestamp': datetime.now()}
        ]
        
        stats = self.notification_system.get_notification_stats()
        self.assertEqual(stats['total_notifications'], 3)
        self.assertEqual(stats['by_type']['alert'], 2)
        self.assertEqual(stats['by_type']['info'], 1)


class TestConfig(unittest.TestCase):
    """Test configuration management."""
    
    def test_config_initialization(self):
        """Test that config initializes with default values."""
        config = Config()
        
        # Test that basic attributes exist
        self.assertIsInstance(config.distraction_threshold, float)
        self.assertIsInstance(config.presence_threshold, float)
        self.assertIsInstance(config.camera_index, int)
        self.assertIsInstance(config.frame_rate, int)
    
    def test_config_validation(self):
        """Test config validation."""
        config = Config()
        # Should not raise an exception
        result = config.validate()
        self.assertIsInstance(result, bool)


if __name__ == '__main__':
    unittest.main()