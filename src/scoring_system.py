"""Scoring system for calculating user performance and attention scores."""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ScoringSystem:
    """Calculates scores based on AI analysis results."""
    
    def __init__(self, config):
        self.config = config
        self.score_history = []
        self.session_start = datetime.utcnow()
    
    def calculate_distraction_score(self, distraction_analysis: Dict[str, Any]) -> float:
        """Calculate distraction score from ViT analysis."""
        if 'error' in distraction_analysis:
            return 0.5  # Default neutral score on error
        
        distraction_score = distraction_analysis.get('distraction_score', 0.5)
        is_distracted = distraction_analysis.get('is_distracted', False)
        
        # Convert to a 0-100 scale where higher is better (less distracted)
        if is_distracted:
            return max(0, (1 - distraction_score) * 100)
        else:
            return min(100, distraction_score * 100)
    
    def calculate_presence_score(self, behavior_analysis: Dict[str, Any]) -> float:
        """Calculate presence score from YOLO analysis."""
        if 'error' in behavior_analysis:
            return 0.0  # Default to absent on error
        
        person_detected = behavior_analysis.get('person_detected', False)
        presence_score = behavior_analysis.get('presence_score', 0.0)
        
        if person_detected:
            return min(100, presence_score * 100)
        else:
            return 0.0
    
    def calculate_behavior_score(self, behavior_analysis: Dict[str, Any]) -> float:
        """Calculate behavior score based on pose and activity."""
        if 'error' in behavior_analysis:
            return 50.0  # Default neutral score on error
        
        behavior_prediction = behavior_analysis.get('behavior_prediction', 'unknown')
        presence_score = behavior_analysis.get('presence_score', 0.0)
        
        behavior_scores = {
            'focused': 90.0,
            'away': 20.0,
            'unknown': 50.0
        }
        
        base_score = behavior_scores.get(behavior_prediction, 50.0)
        
        # Adjust based on presence confidence
        if presence_score > self.config.presence_threshold:
            return min(100, base_score * 1.1)  # Boost for high confidence
        else:
            return max(0, base_score * 0.8)    # Reduce for low confidence
    
    def calculate_feedback_score(self, feedback_analysis: Dict[str, Any]) -> float:
        """Calculate score based on user feedback sentiment."""
        if 'error' in feedback_analysis or not feedback_analysis.get('feedback_processed'):
            return 75.0  # Default positive score when no feedback
        
        analysis_text = feedback_analysis.get('analysis', '').lower()
        
        # Simple sentiment analysis (in production, use proper NLP)
        positive_words = ['good', 'great', 'excellent', 'positive', 'happy', 'satisfied']
        negative_words = ['bad', 'poor', 'terrible', 'negative', 'frustrated', 'annoyed']
        
        positive_count = sum(1 for word in positive_words if word in analysis_text)
        negative_count = sum(1 for word in negative_words if word in analysis_text)
        
        if positive_count > negative_count:
            return min(100, 75 + (positive_count * 5))
        elif negative_count > positive_count:
            return max(0, 75 - (negative_count * 10))
        else:
            return 75.0  # Neutral sentiment
    
    def calculate_overall_score(self, individual_scores: Dict[str, float]) -> float:
        """Calculate weighted overall score."""
        weights = {
            'distraction_score': 0.4,    # 40% weight - most important
            'presence_score': 0.3,       # 30% weight
            'behavior_score': 0.2,       # 20% weight
            'feedback_score': 0.1        # 10% weight
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for score_type, score_value in individual_scores.items():
            if score_type in weights and score_value is not None:
                weighted_sum += score_value * weights[score_type]
                total_weight += weights[score_type]
        
        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return 50.0  # Default neutral score
    
    def calculate_time_metrics(self) -> Dict[str, Any]:
        """Calculate time-based metrics."""
        current_time = datetime.utcnow()
        session_duration = (current_time - self.session_start).total_seconds() / 60  # minutes
        
        # Calculate time-based metrics from recent history
        recent_scores = [score for score in self.score_history 
                        if (current_time - score['timestamp']).total_seconds() < 300]  # Last 5 minutes
        
        if recent_scores:
            distracted_periods = [score for score in recent_scores 
                                if score.get('individual_scores', {}).get('distraction_score', 100) < 50]
            distraction_time = len(distracted_periods) * (300 / len(recent_scores))  # Approximate minutes
        else:
            distraction_time = 0
        
        return {
            'session_duration_minutes': session_duration,
            'distraction_time_minutes': distraction_time,
            'focus_time_minutes': max(0, session_duration - distraction_time),
            'focus_percentage': max(0, 100 - (distraction_time / max(session_duration, 1)) * 100)
        }
    
    def calculate_scores(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all scores from analysis results."""
        try:
            # Extract individual analyses
            distraction_analysis = analysis_results.get('distraction_analysis', {})
            behavior_analysis = analysis_results.get('behavior_analysis', {})
            feedback_analysis = analysis_results.get('feedback_analysis', {})
            
            # Calculate individual scores
            individual_scores = {
                'distraction_score': self.calculate_distraction_score(distraction_analysis),
                'presence_score': self.calculate_presence_score(behavior_analysis),
                'behavior_score': self.calculate_behavior_score(behavior_analysis),
                'feedback_score': self.calculate_feedback_score(feedback_analysis)
            }
            
            # Calculate overall score
            overall_score = self.calculate_overall_score(individual_scores)
            
            # Calculate time metrics
            time_metrics = self.calculate_time_metrics()
            
            # Compile final scores
            final_scores = {
                'timestamp': analysis_results.get('timestamp', datetime.utcnow()),
                'overall_score': overall_score,
                'individual_scores': individual_scores,
                'time_metrics': time_metrics,
                'grade': self._get_grade(overall_score),
                'recommendations': self._get_recommendations(individual_scores)
            }
            
            # Store in history
            self.score_history.append(final_scores)
            
            # Keep only recent history (last 100 entries)
            if len(self.score_history) > 100:
                self.score_history = self.score_history[-100:]
            
            return final_scores
            
        except Exception as e:
            logger.error(f"Error calculating scores: {e}")
            return {
                'timestamp': datetime.utcnow(),
                'overall_score': 50.0,
                'error': str(e)
            }
    
    def _get_grade(self, overall_score: float) -> str:
        """Convert numeric score to letter grade."""
        if overall_score >= 90:
            return 'A'
        elif overall_score >= 80:
            return 'B'
        elif overall_score >= 70:
            return 'C'
        elif overall_score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _get_recommendations(self, individual_scores: Dict[str, float]) -> list:
        """Generate recommendations based on scores."""
        recommendations = []
        
        distraction_score = individual_scores.get('distraction_score', 100)
        presence_score = individual_scores.get('presence_score', 100)
        behavior_score = individual_scores.get('behavior_score', 100)
        
        if distraction_score < 50:
            recommendations.append("Consider taking a short break to refocus")
        
        if presence_score < 30:
            recommendations.append("Please ensure you're positioned clearly in front of the camera")
        
        if behavior_score < 40:
            recommendations.append("Try to maintain an active and engaged posture")
        
        if not recommendations:
            recommendations.append("Great job! Keep up the focused work")
        
        return recommendations