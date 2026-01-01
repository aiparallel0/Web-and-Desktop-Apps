"""
Analytics tracking routes for conversion funnel and user behavior
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.analytics_routes",
            file_path=__file__,
            description="Analytics tracking routes for conversion funnel and user behavior",
            dependencies=[],
            exports=["analytics_bp"]
        ))
    except Exception:
        pass

# Create Blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

# In-memory event storage (in production, use a database or analytics service)
events_store = []
MAX_EVENTS_IN_MEMORY = 10000

@analytics_bp.route('/track', methods=['POST'])
def track_event():
    """
    Track a single analytics event.
    
    Expected payload:
    {
        "event": "page_view",
        "properties": {
            "page": "/pricing.html",
            "referrer": "google.com"
        },
        "timestamp": "2024-12-08T12:00:00Z",
        "session_id": "session_123",
        "user_id": "user_123" (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'event' not in data:
            return jsonify({'success': False, 'error': 'Event name required'}), 400
        
        event = {
            'event': data.get('event'),
            'properties': data.get('properties', {}),
            'timestamp': data.get('timestamp', datetime.utcnow().isoformat()),
            'session_id': data.get('session_id'),
            'user_id': data.get('user_id'),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'received_at': datetime.utcnow().isoformat()
        }
        
        # Store event
        events_store.append(event)
        
        # Trim if too many events
        if len(events_store) > MAX_EVENTS_IN_MEMORY:
            events_store.pop(0)
        
        logger.info(f"Tracked event: {event['event']} from session {event['session_id']}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error tracking event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/batch', methods=['POST'])
def track_batch():
    """
    Track multiple analytics events in a single request.
    
    Expected payload:
    [
        {"event": "click", "properties": {...}},
        {"event": "page_view", "properties": {...}}
    ]
    """
    try:
        data = request.get_json()
        
        if not isinstance(data, list):
            return jsonify({'success': False, 'error': 'Expected array of events'}), 400
        
        processed = 0
        for event_data in data:
            if 'event' in event_data:
                event = {
                    'event': event_data.get('event'),
                    'properties': event_data.get('properties', {}),
                    'timestamp': event_data.get('timestamp', datetime.utcnow().isoformat()),
                    'session_id': event_data.get('session_id'),
                    'user_id': event_data.get('user_id'),
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent'),
                    'received_at': datetime.utcnow().isoformat()
                }
                events_store.append(event)
                processed += 1
        
        # Trim if too many events
        while len(events_store) > MAX_EVENTS_IN_MEMORY:
            events_store.pop(0)
        
        logger.info(f"Tracked {processed} events in batch")
        
        return jsonify({'success': True, 'processed': processed}), 200
        
    except Exception as e:
        logger.error(f"Error tracking batch: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/conversion', methods=['POST'])
def track_conversion():
    """
    Track conversion funnel events.
    
    Expected payload:
    {
        "event_type": "signup_completed",
        "user_id": "user_123",
        "data": {
            "plan": "pro",
            "source": "pricing_page"
        }
    }
    
    Supported event types:
    - signup_started
    - signup_completed
    - trial_activated
    - first_receipt_uploaded
    - upgrade_clicked
    - payment_completed
    """
    try:
        data = request.get_json()
        
        if not data or 'event_type' not in data:
            return jsonify({'success': False, 'error': 'Event type required'}), 400
        
        event_type = data.get('event_type')
        valid_events = [
            'signup_started', 'signup_completed', 'trial_activated',
            'first_receipt_uploaded', 'upgrade_clicked', 'payment_completed'
        ]
        
        if event_type not in valid_events:
            return jsonify({
                'success': False,
                'error': f'Invalid event type. Must be one of: {", ".join(valid_events)}'
            }), 400
        
        conversion_event = {
            'event': 'conversion',
            'event_type': event_type,
            'user_id': data.get('user_id'),
            'properties': data.get('data', {}),
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'received_at': datetime.utcnow().isoformat()
        }
        
        events_store.append(conversion_event)
        
        logger.info(f"Tracked conversion: {event_type} for user {data.get('user_id')}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error tracking conversion: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/metrics/funnel', methods=['GET'])
def get_funnel_metrics():
    """
    Get conversion funnel metrics.
    
    Returns counts for each funnel stage:
    - Signup started
    - Signup completed
    - Trial activated
    - First receipt uploaded
    - Upgrade clicked
    - Payment completed
    """
    try:
        # Count events by type
        funnel_counts = {
            'signup_started': 0,
            'signup_completed': 0,
            'trial_activated': 0,
            'first_receipt_uploaded': 0,
            'upgrade_clicked': 0,
            'payment_completed': 0
        }
        
        for event in events_store:
            if event.get('event') == 'conversion':
                event_type = event.get('event_type')
                if event_type in funnel_counts:
                    funnel_counts[event_type] += 1
        
        # Calculate conversion rates
        funnel_rates = {}
        if funnel_counts['signup_started'] > 0:
            for key in ['signup_completed', 'trial_activated', 'first_receipt_uploaded', 
                       'upgrade_clicked', 'payment_completed']:
                funnel_rates[f'{key}_rate'] = round(
                    (funnel_counts[key] / funnel_counts['signup_started']) * 100, 2
                )
        
        return jsonify({
            'success': True,
            'data': {
                'counts': funnel_counts,
                'rates': funnel_rates,
                'total_events': len(events_store)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting funnel metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/metrics/events', methods=['GET'])
def get_event_metrics():
    """
    Get event metrics summary.
    
    Query parameters:
    - event_name: Filter by specific event name
    - hours: Number of hours to look back (default: 24)
    """
    try:
        event_name = request.args.get('event_name')
        hours = int(request.args.get('hours', 24))
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter events by time
        recent_events = [
            e for e in events_store
            if datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')) > cutoff_time
        ]
        
        # Filter by event name if specified
        if event_name:
            recent_events = [e for e in recent_events if e.get('event') == event_name]
        
        # Count by event type
        event_counts = {}
        for event in recent_events:
            event_type = event.get('event')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'total_events': len(recent_events),
                'event_counts': event_counts,
                'time_range_hours': hours
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting event metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/health', methods=['GET'])
def health_check():
    """Analytics service health check."""
    return jsonify({
        'success': True,
        'service': 'analytics',
        'events_stored': len(events_store),
        'max_capacity': MAX_EVENTS_IN_MEMORY
    }), 200
