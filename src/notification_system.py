"""Notification system for sending alerts and updates based on scores."""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NotificationSystem:
    """Manages notifications based on scoring results."""
    
    def __init__(self):
        self.notification_history = []
        self.last_notification_time = {}
        self.notification_cooldown = 300  # 5 minutes cooldown between similar notifications
    
    async def process_scores(self, scores: Dict[str, Any]):
        """Process scores and send notifications if needed."""
        try:
            overall_score = scores.get('overall_score', 50)
            individual_scores = scores.get('individual_scores', {})
            recommendations = scores.get('recommendations', [])
            
            notifications = []
            
            # Check for low overall performance
            if overall_score < 40:
                notifications.append({
                    'type': 'performance_alert',
                    'severity': 'high',
                    'title': 'Low Performance Alert',
                    'message': f'Your current performance score is {overall_score:.1f}. Consider taking a break.',
                    'recommendations': recommendations
                })
            
            # Check for distraction alerts
            distraction_score = individual_scores.get('distraction_score', 100)
            if distraction_score < 30:
                notifications.append({
                    'type': 'distraction_alert',
                    'severity': 'medium',
                    'title': 'Distraction Detected',
                    'message': 'High levels of distraction detected. Try to refocus on your task.',
                    'recommendations': ['Take a 2-minute mindfulness break', 'Remove distracting elements from view']
                })
            
            # Check for presence alerts
            presence_score = individual_scores.get('presence_score', 100)
            if presence_score < 20:
                notifications.append({
                    'type': 'presence_alert',
                    'severity': 'low',
                    'title': 'Presence Not Detected',
                    'message': 'You appear to be away from your workspace.',
                    'recommendations': ['Ensure good lighting', 'Position yourself clearly in front of the camera']
                })
            
            # Check for positive achievements
            if overall_score > 85:
                notifications.append({
                    'type': 'achievement',
                    'severity': 'info',
                    'title': 'Great Performance!',
                    'message': f'Excellent work! Your current score is {overall_score:.1f}.',
                    'recommendations': ['Keep up the great work!']
                })
            
            # Send notifications (with cooldown)
            for notification in notifications:
                await self.send_notification(notification)
            
        except Exception as e:
            logger.error(f"Error processing scores for notifications: {e}")
    
    async def send_notification(self, notification: Dict[str, Any]):
        """Send a notification with cooldown logic."""
        try:
            notification_type = notification.get('type', 'general')
            current_time = datetime.utcnow()
            
            # Check cooldown
            last_sent = self.last_notification_time.get(notification_type)
            if last_sent:
                time_since_last = (current_time - last_sent).total_seconds()
                if time_since_last < self.notification_cooldown:
                    return  # Skip due to cooldown
            
            # Add timestamp and send
            notification['timestamp'] = current_time
            
            # Log notification (in production, this would send to UI/mobile/email)
            logger.info(f"NOTIFICATION [{notification['severity'].upper()}]: {notification['title']}")
            logger.info(f"Message: {notification['message']}")
            if notification.get('recommendations'):
                logger.info(f"Recommendations: {', '.join(notification['recommendations'])}")
            
            # Store in history
            self.notification_history.append(notification)
            self.last_notification_time[notification_type] = current_time
            
            # Keep only recent history
            if len(self.notification_history) > 50:
                self.notification_history = self.notification_history[-50:]
            
            # In a real implementation, you would also:
            # - Send to web UI via WebSocket
            # - Send push notification to mobile app
            # - Send email for high severity alerts
            # - Update dashboard widgets
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def get_recent_notifications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent notifications."""
        return self.notification_history[-limit:] if self.notification_history else []
    
    async def send_custom_notification(self, title: str, message: str, severity: str = 'info'):
        """Send a custom notification."""
        notification = {
            'type': 'custom',
            'severity': severity,
            'title': title,
            'message': message,
            'recommendations': []
        }
        await self.send_notification(notification)
    
    async def send_session_summary(self, session_stats: Dict[str, Any]):
        """Send a session summary notification."""
        try:
            focus_percentage = session_stats.get('focus_percentage', 0)
            session_duration = session_stats.get('session_duration_minutes', 0)
            
            if session_duration < 5:  # Don't send summary for very short sessions
                return
            
            summary_message = (
                f"Session completed: {session_duration:.1f} minutes total, "
                f"{focus_percentage:.1f}% focused time."
            )
            
            recommendations = []
            if focus_percentage > 80:
                recommendations.append("Excellent focus! Keep up the great work.")
            elif focus_percentage > 60:
                recommendations.append("Good session. Try to minimize distractions next time.")
            else:
                recommendations.append("Consider shorter, more focused work sessions.")
            
            notification = {
                'type': 'session_summary',
                'severity': 'info',
                'title': 'Session Summary',
                'message': summary_message,
                'recommendations': recommendations
            }
            
            await self.send_notification(notification)
            
        except Exception as e:
            logger.error(f"Error sending session summary: {e}")
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        if not self.notification_history:
            return {'total_notifications': 0}
        
        total = len(self.notification_history)
        by_type = {}
        by_severity = {}
        
        for notification in self.notification_history:
            notif_type = notification.get('type', 'unknown')
            severity = notification.get('severity', 'unknown')
            
            by_type[notif_type] = by_type.get(notif_type, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            'total_notifications': total,
            'by_type': by_type,
            'by_severity': by_severity,
            'most_recent': self.notification_history[-1]['timestamp'] if self.notification_history else None
        }