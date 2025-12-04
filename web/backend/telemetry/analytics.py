"""
=============================================================================
ANALYTICS TRACKER - User Analytics and Event Tracking
=============================================================================

Provides analytics tracking for user behavior and feature usage.
Integrates with the Circular Exchange Framework for data-driven improvements.

=============================================================================
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsEvent:
    """Represents an analytics event."""
    timestamp: datetime
    user_id: Optional[str]
    event_name: str
    properties: Dict[str, Any]
    session_id: Optional[str] = None


class AnalyticsTracker:
    """
    Tracks user analytics events for insights and CEFR integration.
    
    Events are stored in-memory and can be exported to external systems.
    """
    
    def __init__(self, max_events: int = 10000):
        """
        Initialize analytics tracker.
        
        Args:
            max_events: Maximum events to keep in memory
        """
        self._events: List[AnalyticsEvent] = []
        self._max_events = max_events
        self._event_counts: Dict[str, int] = defaultdict(int)
        self._user_sessions: Dict[str, datetime] = {}
        
        logger.info("AnalyticsTracker initialized")
    
    def track(
        self,
        event_name: str,
        user_id: str = None,
        properties: Dict[str, Any] = None,
        session_id: str = None
    ):
        """
        Track an analytics event.
        
        Args:
            event_name: Name of the event
            user_id: User identifier (anonymous if not provided)
            properties: Additional event properties
            session_id: User session identifier
        """
        event = AnalyticsEvent(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            event_name=event_name,
            properties=properties or {},
            session_id=session_id
        )
        
        self._events.append(event)
        self._event_counts[event_name] += 1
        
        # Prune old events if needed
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]
        
        # Update session tracking
        if user_id:
            self._user_sessions[user_id] = datetime.now(timezone.utc)
        
        logger.debug(f"Event tracked: {event_name} for user {user_id}")
    
    def track_extraction(
        self,
        user_id: str,
        model_id: str,
        success: bool,
        duration: float,
        confidence: float = None,
        items_count: int = 0
    ):
        """Track a receipt extraction event."""
        self.track(
            event_name="extraction",
            user_id=user_id,
            properties={
                "model": model_id,
                "success": success,
                "duration_seconds": duration,
                "confidence": confidence,
                "items_extracted": items_count
            }
        )
    
    def track_page_view(
        self,
        user_id: str,
        page: str,
        referrer: str = None
    ):
        """Track a page view event."""
        self.track(
            event_name="page_view",
            user_id=user_id,
            properties={
                "page": page,
                "referrer": referrer
            }
        )
    
    def track_feature_usage(
        self,
        user_id: str,
        feature: str,
        action: str = "used"
    ):
        """Track feature usage."""
        self.track(
            event_name="feature_usage",
            user_id=user_id,
            properties={
                "feature": feature,
                "action": action
            }
        )
    
    def track_error(
        self,
        user_id: str,
        error_type: str,
        error_message: str,
        context: Dict[str, Any] = None
    ):
        """Track an error event."""
        self.track(
            event_name="error",
            user_id=user_id,
            properties={
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {}
            }
        )
    
    def track_feedback(
        self,
        user_id: str,
        feedback_type: str,
        rating: int = None,
        comment: str = None
    ):
        """Track user feedback."""
        self.track(
            event_name="feedback",
            user_id=user_id,
            properties={
                "feedback_type": feedback_type,
                "rating": rating,
                "comment": comment
            }
        )
    
    def get_event_counts(self) -> Dict[str, int]:
        """Get counts of all tracked events."""
        return dict(self._event_counts)
    
    def get_active_users(self, minutes: int = 30) -> int:
        """
        Get count of active users in the last N minutes.
        
        Args:
            minutes: Time window in minutes
            
        Returns:
            Number of active users
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return sum(1 for ts in self._user_sessions.values() if ts > cutoff)
    
    def get_recent_events(
        self,
        event_name: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent events.
        
        Args:
            event_name: Filter by event name (optional)
            limit: Maximum events to return
            
        Returns:
            List of event dictionaries
        """
        events = self._events
        
        if event_name:
            events = [e for e in events if e.event_name == event_name]
        
        events = events[-limit:]
        
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "user_id": e.user_id,
                "event_name": e.event_name,
                "properties": e.properties
            }
            for e in events
        ]
    
    def get_user_journey(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get event history for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum events to return
            
        Returns:
            List of user's events in chronological order
        """
        user_events = [e for e in self._events if e.user_id == user_id][-limit:]
        
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "event_name": e.event_name,
                "properties": e.properties
            }
            for e in user_events
        ]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get analytics summary.
        
        Returns:
            Summary statistics
        """
        now = datetime.now(timezone.utc)
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        events_last_hour = sum(1 for e in self._events if e.timestamp > last_hour)
        events_last_day = sum(1 for e in self._events if e.timestamp > last_day)
        
        # Calculate extraction success rate
        extraction_events = [
            e for e in self._events 
            if e.event_name == "extraction" and e.timestamp > last_day
        ]
        if extraction_events:
            success_count = sum(1 for e in extraction_events if e.properties.get("success"))
            success_rate = success_count / len(extraction_events) * 100
        else:
            success_rate = 0
        
        return {
            "total_events": len(self._events),
            "events_last_hour": events_last_hour,
            "events_last_day": events_last_day,
            "active_users_30min": self.get_active_users(30),
            "event_counts": self.get_event_counts(),
            "extraction_success_rate_24h": round(success_rate, 1)
        }
    
    def export_for_cefr(self) -> Dict[str, Any]:
        """
        Export analytics data for CEFR integration.
        
        Returns:
            Data formatted for Circular Exchange Framework
        """
        # Get extraction events for analysis
        extraction_events = [
            e for e in self._events 
            if e.event_name == "extraction"
        ]
        
        # Analyze model performance
        model_stats = defaultdict(lambda: {"total": 0, "success": 0, "avg_duration": 0, "durations": []})
        
        for event in extraction_events:
            model = event.properties.get("model", "unknown")
            model_stats[model]["total"] += 1
            
            if event.properties.get("success"):
                model_stats[model]["success"] += 1
            
            duration = event.properties.get("duration_seconds", 0)
            if duration:
                model_stats[model]["durations"].append(duration)
        
        # Calculate averages
        for model, stats in model_stats.items():
            if stats["durations"]:
                stats["avg_duration"] = sum(stats["durations"]) / len(stats["durations"])
            del stats["durations"]  # Remove raw data
        
        # Analyze errors
        error_events = [e for e in self._events if e.event_name == "error"]
        error_patterns = defaultdict(int)
        for event in error_events:
            error_type = event.properties.get("error_type", "unknown")
            error_patterns[error_type] += 1
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "period_events": len(self._events),
            "model_performance": dict(model_stats),
            "error_patterns": dict(error_patterns),
            "active_users": self.get_active_users(60),
            "feature_usage": {
                k: v for k, v in self._event_counts.items()
                if k.startswith("feature_")
            }
        }


# =============================================================================
# GLOBAL TRACKER INSTANCE
# =============================================================================

_tracker: Optional[AnalyticsTracker] = None


def get_tracker() -> AnalyticsTracker:
    """Get or create the global analytics tracker."""
    global _tracker
    
    if _tracker is None:
        _tracker = AnalyticsTracker()
    
    return _tracker


def track_event(
    event_name: str,
    user_id: str = None,
    properties: Dict[str, Any] = None
):
    """
    Convenience function to track an event.
    
    Args:
        event_name: Name of the event
        user_id: User identifier
        properties: Event properties
    """
    get_tracker().track(event_name, user_id, properties)


def track_user_action(
    user_id: str,
    action: str,
    target: str = None,
    metadata: Dict[str, Any] = None
):
    """
    Track a user action.
    
    Args:
        user_id: User identifier
        action: Action type (click, submit, view, etc.)
        target: Target element or resource
        metadata: Additional metadata
    """
    properties = {
        "action": action,
        "target": target
    }
    if metadata:
        properties.update(metadata)
    
    get_tracker().track("user_action", user_id, properties)
