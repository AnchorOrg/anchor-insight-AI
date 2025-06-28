"""Database manager for storing session data and analysis results."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for storing analysis results and session data."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.client = None
        self.db = None
        self.sessions_collection = None
        self.scores_collection = None
        self.notifications_collection = None
        self.is_connected = False
    
    async def connect(self):
        """Connect to the database."""
        try:
            self.client = MongoClient(self.database_url, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database (extract from URL or use default)
            db_name = self.database_url.split('/')[-1] if '/' in self.database_url else 'anchor_insight'
            self.db = self.client[db_name]
            
            # Get collections
            self.sessions_collection = self.db['sessions']
            self.scores_collection = self.db['scores']
            self.notifications_collection = self.db['notifications']
            
            # Create indexes for better performance
            await self._create_indexes()
            
            self.is_connected = True
            logger.info("Database connected successfully")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to database: {e}")
            logger.warning("Running without database storage")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            self.is_connected = False
    
    async def _create_indexes(self):
        """Create database indexes for performance."""
        if not self.is_connected:
            return
        
        try:
            # Index on timestamp for time-based queries
            self.sessions_collection.create_index([("timestamp", -1)])
            self.scores_collection.create_index([("timestamp", -1)])
            self.notifications_collection.create_index([("timestamp", -1)])
            
            # Index on session_id for session-related queries
            self.scores_collection.create_index([("session_id", 1)])
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    async def store_session_data(self, session_data: Dict[str, Any]) -> Optional[str]:
        """Store session analysis data."""
        if not self.is_connected:
            logger.debug("Database not connected, skipping storage")
            return None
        
        try:
            # Add metadata
            session_data.update({
                'created_at': datetime.utcnow(),
                'data_type': 'session_analysis'
            })
            
            # Insert into sessions collection
            result = self.sessions_collection.insert_one(session_data)
            
            # Also store scores separately for easier querying
            if 'scores' in session_data:
                scores_data = session_data['scores'].copy()
                scores_data.update({
                    'session_id': str(result.inserted_id),
                    'timestamp': session_data['timestamp'],
                    'created_at': datetime.utcnow()
                })
                self.scores_collection.insert_one(scores_data)
            
            logger.debug(f"Session data stored with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store session data: {e}")
            return None
    
    async def store_notification(self, notification: Dict[str, Any]) -> Optional[str]:
        """Store notification data."""
        if not self.is_connected:
            return None
        
        try:
            notification.update({
                'created_at': datetime.utcnow(),
                'data_type': 'notification'
            })
            
            result = self.notifications_collection.insert_one(notification)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store notification: {e}")
            return None
    
    async def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent session data."""
        if not self.is_connected:
            return []
        
        try:
            cursor = self.sessions_collection.find().sort('timestamp', -1).limit(limit)
            sessions = []
            
            for session in cursor:
                # Convert ObjectId to string for JSON serialization
                session['_id'] = str(session['_id'])
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get recent sessions: {e}")
            return []
    
    async def get_session_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get session statistics for the last N hours."""
        if not self.is_connected:
            return {}
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get scores from the time period
            cursor = self.scores_collection.find({
                'timestamp': {'$gte': cutoff_time}
            }).sort('timestamp', 1)
            
            scores = list(cursor)
            
            if not scores:
                return {'period_hours': hours, 'total_sessions': 0}
            
            # Calculate statistics
            overall_scores = [s.get('overall_score', 0) for s in scores]
            distraction_scores = [s.get('individual_scores', {}).get('distraction_score', 0) for s in scores]
            
            stats = {
                'period_hours': hours,
                'total_sessions': len(scores),
                'average_overall_score': sum(overall_scores) / len(overall_scores) if overall_scores else 0,
                'average_distraction_score': sum(distraction_scores) / len(distraction_scores) if distraction_scores else 0,
                'min_score': min(overall_scores) if overall_scores else 0,
                'max_score': max(overall_scores) if overall_scores else 0,
                'first_session': scores[0]['timestamp'] if scores else None,
                'last_session': scores[-1]['timestamp'] if scores else None
            }
            
            # Calculate focus time
            total_focus_time = 0
            for score in scores:
                time_metrics = score.get('time_metrics', {})
                focus_time = time_metrics.get('focus_time_minutes', 0)
                total_focus_time += focus_time
            
            stats['total_focus_time_minutes'] = total_focus_time
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}
    
    async def get_score_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get score trends over the last N days."""
        if not self.is_connected:
            return []
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            # Aggregate scores by day
            pipeline = [
                {'$match': {'timestamp': {'$gte': cutoff_time}}},
                {'$group': {
                    '_id': {
                        'year': {'$year': '$timestamp'},
                        'month': {'$month': '$timestamp'},
                        'day': {'$dayOfMonth': '$timestamp'}
                    },
                    'avg_overall_score': {'$avg': '$overall_score'},
                    'avg_distraction_score': {'$avg': '$individual_scores.distraction_score'},
                    'session_count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]
            
            results = list(self.scores_collection.aggregate(pipeline))
            
            # Format results
            trends = []
            for result in results:
                date_info = result['_id']
                trends.append({
                    'date': f"{date_info['year']}-{date_info['month']:02d}-{date_info['day']:02d}",
                    'average_overall_score': round(result['avg_overall_score'], 2),
                    'average_distraction_score': round(result.get('avg_distraction_score', 0), 2),
                    'session_count': result['session_count']
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get score trends: {e}")
            return []
    
    async def cleanup_old_data(self, days: int = 30):
        """Clean up old data beyond the specified days."""
        if not self.is_connected:
            return
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            # Remove old sessions
            sessions_result = self.sessions_collection.delete_many({
                'timestamp': {'$lt': cutoff_time}
            })
            
            # Remove old scores
            scores_result = self.scores_collection.delete_many({
                'timestamp': {'$lt': cutoff_time}
            })
            
            # Remove old notifications
            notifications_result = self.notifications_collection.delete_many({
                'timestamp': {'$lt': cutoff_time}
            })
            
            logger.info(f"Cleaned up old data: {sessions_result.deleted_count} sessions, "
                       f"{scores_result.deleted_count} scores, "
                       f"{notifications_result.deleted_count} notifications")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    async def disconnect(self):
        """Disconnect from the database."""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("Database disconnected")