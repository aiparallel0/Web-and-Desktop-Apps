"""
Event tracking service

Integrates with multiple analytics services:
- Mixpanel for product analytics
- Segment for data routing
- Google Analytics 4 for web analytics
- Internal database for long-term storage
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import requests
import json

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.analytics.tracker",
            file_path=__file__,
            description="Event tracking service for analytics integrations",
            dependencies=["web.backend.database", "web.backend.analytics.events"],
            exports=["EventTracker", "MixpanelTracker", "SegmentTracker", "get_tracker"]
        ))
    except Exception:
        pass


class EventTracker:
    """Base class for event tracking"""
    
    def track(
        self,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Track an event
        
        Args:
            event_name: Name of the event
            properties: Event properties
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            True if tracked successfully
        """
        raise NotImplementedError("Subclass must implement track")
    
    def identify(
        self,
        user_id: str,
        traits: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Identify a user with traits
        
        Args:
            user_id: User identifier
            traits: User traits/properties
            
        Returns:
            True if identified successfully
        """
        raise NotImplementedError("Subclass must implement identify")


class MixpanelTracker(EventTracker):
    """Mixpanel analytics tracker"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize Mixpanel tracker
        
        Args:
            token: Mixpanel project token (defaults to env var)
        """
        self.token = token or os.getenv('MIXPANEL_TOKEN')
        self.api_url = 'https://api.mixpanel.com'
        
        if not self.token:
            logger.warning("Mixpanel token not configured")
    
    def track(
        self,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """Track event to Mixpanel"""
        if not self.token:
            return False
        
        event_data = {
            'event': event_name,
            'properties': {
                'token': self.token,
                'time': int(datetime.utcnow().timestamp()),
                **(properties or {})
            }
        }
        
        if user_id:
            event_data['properties']['distinct_id'] = user_id
        if session_id:
            event_data['properties']['session_id'] = session_id
        
        try:
            # Encode as base64 for Mixpanel
            import base64
            encoded = base64.b64encode(json.dumps([event_data]).encode()).decode()
            
            response = requests.post(
                f'{self.api_url}/track',
                params={'data': encoded},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug(f"Tracked event to Mixpanel: {event_name}")
                return True
            else:
                logger.error(f"Mixpanel error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to track to Mixpanel: {e}")
            return False
    
    def identify(
        self,
        user_id: str,
        traits: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Identify user to Mixpanel"""
        if not self.token:
            return False
        
        profile_data = {
            '$token': self.token,
            '$distinct_id': user_id,
            '$set': traits or {}
        }
        
        try:
            import base64
            encoded = base64.b64encode(json.dumps([profile_data]).encode()).decode()
            
            response = requests.post(
                f'{self.api_url}/engage',
                params={'data': encoded},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug(f"Identified user to Mixpanel: {user_id}")
                return True
            else:
                logger.error(f"Mixpanel error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to identify to Mixpanel: {e}")
            return False


class SegmentTracker(EventTracker):
    """Segment analytics tracker"""
    
    def __init__(self, write_key: Optional[str] = None):
        """
        Initialize Segment tracker
        
        Args:
            write_key: Segment write key (defaults to env var)
        """
        self.write_key = write_key or os.getenv('SEGMENT_WRITE_KEY')
        self.api_url = 'https://api.segment.io/v1'
        
        if not self.write_key:
            logger.warning("Segment write key not configured")
    
    def track(
        self,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """Track event to Segment"""
        if not self.write_key:
            return False
        
        event_data = {
            'event': event_name,
            'properties': properties or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if user_id:
            event_data['userId'] = user_id
        else:
            event_data['anonymousId'] = session_id or 'anonymous'
        
        try:
            response = requests.post(
                f'{self.api_url}/track',
                json=event_data,
                auth=(self.write_key, ''),
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug(f"Tracked event to Segment: {event_name}")
                return True
            else:
                logger.error(f"Segment error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to track to Segment: {e}")
            return False
    
    def identify(
        self,
        user_id: str,
        traits: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Identify user to Segment"""
        if not self.write_key:
            return False
        
        identify_data = {
            'userId': user_id,
            'traits': traits or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            response = requests.post(
                f'{self.api_url}/identify',
                json=identify_data,
                auth=(self.write_key, ''),
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug(f"Identified user to Segment: {user_id}")
                return True
            else:
                logger.error(f"Segment error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to identify to Segment: {e}")
            return False


class DatabaseTracker(EventTracker):
    """Internal database tracker"""
    
    def track(
        self,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """Track event to database"""
        try:
            from web.backend.database import AnalyticsEvent, get_db_context
            
            with get_db_context() as db:
                event = AnalyticsEvent(
                    user_id=user_id,
                    session_id=session_id,
                    event_name=event_name,
                    event_properties=properties or {}
                )
                db.add(event)
                db.commit()
                
                logger.debug(f"Tracked event to database: {event_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to track to database: {e}")
            return False
    
    def identify(
        self,
        user_id: str,
        traits: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Identify user (no-op for database tracker)"""
        return True


class CompositeTracker(EventTracker):
    """Composite tracker that sends to multiple services"""
    
    def __init__(self, trackers: list):
        """
        Initialize composite tracker
        
        Args:
            trackers: List of EventTracker instances
        """
        self.trackers = trackers
    
    def track(
        self,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """Track event to all trackers"""
        results = []
        for tracker in self.trackers:
            try:
                result = tracker.track(event_name, properties, user_id, session_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Tracker failed: {e}")
                results.append(False)
        
        # Return True if at least one succeeded
        return any(results)
    
    def identify(
        self,
        user_id: str,
        traits: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Identify user to all trackers"""
        results = []
        for tracker in self.trackers:
            try:
                result = tracker.identify(user_id, traits)
                results.append(result)
            except Exception as e:
                logger.error(f"Tracker failed: {e}")
                results.append(False)
        
        return any(results)


def get_tracker() -> EventTracker:
    """
    Get configured event tracker
    
    Returns:
        EventTracker instance
    """
    trackers = []
    
    # Always use database tracker
    trackers.append(DatabaseTracker())
    
    # Add Mixpanel if configured
    if os.getenv('MIXPANEL_TOKEN'):
        trackers.append(MixpanelTracker())
    
    # Add Segment if configured
    if os.getenv('SEGMENT_WRITE_KEY'):
        trackers.append(SegmentTracker())
    
    if len(trackers) == 1:
        return trackers[0]
    else:
        return CompositeTracker(trackers)


__all__ = [
    'EventTracker',
    'MixpanelTracker',
    'SegmentTracker',
    'DatabaseTracker',
    'CompositeTracker',
    'get_tracker'
]
