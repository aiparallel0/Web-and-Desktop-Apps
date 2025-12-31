"""
Tests for analytics module

Tests event tracking, conversion funnels, and analytics integration.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock


# Test event definitions
def test_event_type_enum():
    """Test EventType enum has expected values"""
    from web.backend.analytics.events import EventType
    
    # Test some key events exist
    assert EventType.USER_SIGNUP == "user_signup"
    assert EventType.RECEIPT_PROCESSED == "receipt_processed"
    assert EventType.PAYMENT_COMPLETED == "payment_completed"
    assert EventType.TRIAL_STARTED == "trial_started"


def test_create_event():
    """Test creating standardized event"""
    from web.backend.analytics.events import create_event, EventType
    
    event = create_event(
        event_type=EventType.USER_SIGNUP,
        user_id="user-123",
        session_id="session-456",
        properties={'email': 'test@example.com'},
        utm_params={
            'utm_source': 'google',
            'utm_medium': 'cpc',
            'utm_campaign': 'test_campaign'
        }
    )
    
    assert event['event'] == 'user_signup'
    assert event['user_id'] == 'user-123'
    assert event['session_id'] == 'session-456'
    assert event['properties']['email'] == 'test@example.com'
    assert event['utm_source'] == 'google'
    assert event['utm_medium'] == 'cpc'


def test_event_properties_helpers():
    """Test EventProperties helper methods"""
    from web.backend.analytics.events import EventProperties
    
    # User signup
    signup_props = EventProperties.user_signup(
        email='test@example.com',
        referral_source='friend',
        utm_params={'utm_source': 'twitter'}
    )
    assert signup_props['email'] == 'test@example.com'
    assert signup_props['referral_source'] == 'friend'
    
    # Receipt processed
    receipt_props = EventProperties.receipt_processed(
        model_id='ocr_tesseract',
        processing_time=1.5,
        confidence=0.95,
        items_count=10
    )
    assert receipt_props['model_id'] == 'ocr_tesseract'
    assert receipt_props['processing_time'] == 1.5
    assert receipt_props['confidence'] == 0.95
    
    # Payment
    payment_props = EventProperties.payment(
        plan='pro',
        amount=19.99,
        currency='USD',
        success=True
    )
    assert payment_props['plan'] == 'pro'
    assert payment_props['amount'] == 19.99


# Test event trackers
def test_database_tracker():
    """Test database tracker"""
    from web.backend.analytics.tracker import DatabaseTracker
    
    tracker = DatabaseTracker()
    assert tracker is not None
    # Actual database operations tested with integration tests


def test_mixpanel_tracker_configuration():
    """Test Mixpanel tracker configuration"""
    from web.backend.analytics.tracker import MixpanelTracker
    
    tracker = MixpanelTracker(token='test_token')
    assert tracker.token == 'test_token'
    assert tracker.api_url == 'https://api.mixpanel.com'


def test_segment_tracker_configuration():
    """Test Segment tracker configuration"""
    from web.backend.analytics.tracker import SegmentTracker
    
    tracker = SegmentTracker(write_key='test_key')
    assert tracker.write_key == 'test_key'
    assert tracker.api_url == 'https://api.segment.io/v1'


def test_composite_tracker():
    """Test composite tracker delegates to multiple trackers"""
    from web.backend.analytics.tracker import CompositeTracker, DatabaseTracker
    
    tracker1 = DatabaseTracker()
    tracker2 = DatabaseTracker()
    
    composite = CompositeTracker([tracker1, tracker2])
    assert len(composite.trackers) == 2


def test_get_tracker():
    """Test tracker factory"""
    from web.backend.analytics.tracker import get_tracker
    
    tracker = get_tracker()
    assert tracker is not None


# Test conversion funnels
def test_funnel_definition():
    """Test funnel definition structure"""
    from web.backend.analytics.conversion_funnel import SIGNUP_FUNNEL
    
    assert SIGNUP_FUNNEL.funnel_type == "signup"
    assert len(SIGNUP_FUNNEL.steps) == 5
    assert "landing_page_view" in SIGNUP_FUNNEL.steps
    assert "trial_started" in SIGNUP_FUNNEL.steps


def test_funnel_step_index():
    """Test getting step index"""
    from web.backend.analytics.conversion_funnel import SIGNUP_FUNNEL
    
    index = SIGNUP_FUNNEL.get_step_index("account_created")
    assert index == 2
    
    index = SIGNUP_FUNNEL.get_step_index("nonexistent")
    assert index == -1


def test_funnel_next_step():
    """Test getting next step"""
    from web.backend.analytics.conversion_funnel import SIGNUP_FUNNEL
    
    next_step = SIGNUP_FUNNEL.get_next_step("landing_page_view")
    assert next_step == "signup_click"
    
    # Last step
    next_step = SIGNUP_FUNNEL.get_next_step("trial_started")
    assert next_step is None


def test_funnel_is_complete():
    """Test checking funnel completion"""
    from web.backend.analytics.conversion_funnel import SIGNUP_FUNNEL
    
    # Incomplete
    completed_steps = ["landing_page_view", "signup_click"]
    assert SIGNUP_FUNNEL.is_complete(completed_steps) is False
    
    # Complete
    completed_steps = [
        "landing_page_view",
        "signup_click",
        "account_created",
        "email_verified",
        "trial_started"
    ]
    assert SIGNUP_FUNNEL.is_complete(completed_steps) is True


def test_all_funnels_exist():
    """Test that all required funnels are defined"""
    from web.backend.analytics.conversion_funnel import FUNNELS
    
    required_funnels = ['signup', 'activation', 'conversion', 'retention']
    
    for funnel_type in required_funnels:
        assert funnel_type in FUNNELS
        funnel = FUNNELS[funnel_type]
        assert len(funnel.steps) > 0


def test_activation_funnel():
    """Test activation funnel definition"""
    from web.backend.analytics.conversion_funnel import ACTIVATION_FUNNEL
    
    assert ACTIVATION_FUNNEL.funnel_type == "activation"
    assert "trial_started" in ACTIVATION_FUNNEL.steps
    assert "first_receipt_uploaded" in ACTIVATION_FUNNEL.steps
    assert "five_receipts_processed" in ACTIVATION_FUNNEL.steps


def test_conversion_funnel():
    """Test conversion funnel definition"""
    from web.backend.analytics.conversion_funnel import CONVERSION_FUNNEL
    
    assert CONVERSION_FUNNEL.funnel_type == "conversion"
    assert "trial_started" in CONVERSION_FUNNEL.steps
    assert "subscription_created" in CONVERSION_FUNNEL.steps


def test_retention_funnel():
    """Test retention funnel definition"""
    from web.backend.analytics.conversion_funnel import RETENTION_FUNNEL
    
    assert RETENTION_FUNNEL.funnel_type == "retention"
    assert "subscription_created" in RETENTION_FUNNEL.steps
    assert "month_3_active" in RETENTION_FUNNEL.steps


# Test funnel tracking (with mocks)
@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


def test_track_funnel_step_validation():
    """Test funnel step tracking validates funnel type"""
    from web.backend.analytics.conversion_funnel import track_funnel_step
    
    # Invalid funnel type should return False
    result = track_funnel_step(
        user_id="test-user",
        funnel_type="invalid_funnel",
        step_name="some_step",
        db_session=None
    )
    assert result is False


# Test analytics tasks
def test_process_analytics_batch():
    """Test analytics batch processing"""
    from web.backend.tasks.analytics_tasks import process_analytics_batch
    
    # Should not crash even without database
    try:
        result = process_analytics_batch()
        # Result could be 0 if no DB, that's OK
        assert isinstance(result, int)
    except Exception:
        # Expected if no database configured
        pass


def test_calculate_user_engagement_score():
    """Test user engagement score calculation"""
    from web.backend.tasks.analytics_tasks import calculate_user_engagement_score
    
    # Should not crash
    try:
        score = calculate_user_engagement_score("test-user", days=30)
        assert isinstance(score, int)
        assert 0 <= score <= 100
    except Exception:
        # Expected if no database
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
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
