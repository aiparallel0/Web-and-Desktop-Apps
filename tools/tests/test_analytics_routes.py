"""
Tests for analytics tracking routes
"""
import pytest
import json
from datetime import datetime


def test_analytics_track_event(app, client):
    """Test tracking a single event."""
    event_data = {
        'event': 'page_view',
        'properties': {
            'page': '/pricing.html',
            'referrer': 'google.com'
        },
        'session_id': 'test_session_123',
        'user_id': 'test_user_456'
    }
    
    response = client.post(
        '/api/analytics/track',
        data=json.dumps(event_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True


def test_analytics_track_batch(app, client):
    """Test tracking multiple events in batch."""
    events = [
        {'event': 'click', 'properties': {'element': 'cta_button'}},
        {'event': 'page_view', 'properties': {'page': '/dashboard.html'}}
    ]
    
    response = client.post(
        '/api/analytics/batch',
        data=json.dumps(events),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['processed'] == 2


def test_analytics_track_conversion(app, client):
    """Test tracking conversion event."""
    conversion_data = {
        'event_type': 'signup_completed',
        'user_id': 'user_123',
        'data': {
            'plan': 'pro',
            'source': 'pricing_page'
        }
    }
    
    response = client.post(
        '/api/analytics/conversion',
        data=json.dumps(conversion_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True


def test_analytics_invalid_conversion_type(app, client):
    """Test tracking conversion with invalid event type."""
    conversion_data = {
        'event_type': 'invalid_event',
        'user_id': 'user_123'
    }
    
    response = client.post(
        '/api/analytics/conversion',
        data=json.dumps(conversion_data),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False


def test_analytics_funnel_metrics(app, client):
    """Test getting funnel metrics."""
    # Track some conversion events first
    events = [
        {'event_type': 'signup_started', 'user_id': 'user_1'},
        {'event_type': 'signup_completed', 'user_id': 'user_1'},
        {'event_type': 'trial_activated', 'user_id': 'user_1'}
    ]
    
    for event in events:
        client.post(
            '/api/analytics/conversion',
            data=json.dumps(event),
            content_type='application/json'
        )
    
    # Get funnel metrics
    response = client.get('/api/analytics/metrics/funnel')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'counts' in data['data']
    assert 'rates' in data['data']


def test_analytics_event_metrics(app, client):
    """Test getting event metrics."""
    response = client.get('/api/analytics/metrics/events?hours=24')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'total_events' in data['data']
    assert 'event_counts' in data['data']


def test_analytics_health_check(app, client):
    """Test analytics service health check."""
    response = client.get('/api/analytics/health')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['service'] == 'analytics'
    assert 'events_stored' in data


def test_analytics_missing_event_name(app, client):
    """Test tracking event without event name."""
    response = client.post(
        '/api/analytics/track',
        data=json.dumps({'properties': {}}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False


def test_analytics_batch_invalid_format(app, client):
    """Test batch tracking with invalid format."""
    response = client.post(
        '/api/analytics/batch',
        data=json.dumps({'not': 'an array'}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False


# Fixtures
@pytest.fixture
def app():
    """Create test Flask app."""
    from web.backend.app import app
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()
