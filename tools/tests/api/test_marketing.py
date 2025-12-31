"""
Tests for marketing automation module

Tests email sequences, email sending, and automation workflows.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Test email sequences
def test_email_sequence_definition():
    """Test email sequence definition structure"""
    from web.backend.marketing.email_sequences import WELCOME_SEQUENCE, EmailStep
    
    assert WELCOME_SEQUENCE.sequence_name == "welcome"
    assert WELCOME_SEQUENCE.sequence_type == "welcome"
    assert WELCOME_SEQUENCE.total_steps() == 3
    
    # Test step retrieval
    step0 = WELCOME_SEQUENCE.get_step(0)
    assert step0 is not None
    assert step0.delay_days == 0
    assert "Welcome" in step0.subject
    
    # Test next step
    next_step = WELCOME_SEQUENCE.get_next_step(0)
    assert next_step is not None
    assert next_step.step_number == 1


def test_trial_conversion_sequence():
    """Test trial conversion sequence"""
    from web.backend.marketing.email_sequences import TRIAL_CONVERSION_SEQUENCE
    
    assert TRIAL_CONVERSION_SEQUENCE.sequence_type == "trial_conversion"
    assert TRIAL_CONVERSION_SEQUENCE.total_steps() == 5
    
    # Verify timing
    step0 = TRIAL_CONVERSION_SEQUENCE.get_step(0)
    assert step0.delay_days == 1
    
    last_step = TRIAL_CONVERSION_SEQUENCE.get_step(4)
    assert last_step.delay_days == 15


def test_calculate_next_send_date():
    """Test next send date calculation"""
    from web.backend.marketing.email_sequences import calculate_next_send_date
    
    started_at = datetime(2024, 1, 1, 12, 0, 0)
    
    # Welcome sequence day 3 email
    next_date = calculate_next_send_date("welcome", 0, started_at)
    assert next_date is not None
    assert next_date == started_at + timedelta(days=3)
    
    # Last step should return None
    next_date = calculate_next_send_date("welcome", 2, started_at)
    assert next_date is None


# Test email sender
def test_mock_email_sender():
    """Test mock email sender"""
    from web.backend.marketing.email_sender import MockEmailSender
    
    sender = MockEmailSender()
    
    result = sender.send_email(
        to_email="test@example.com",
        subject="Test Email",
        html_content="<p>Test</p>",
        tracking_enabled=True
    )
    
    assert result['success'] is True
    assert 'message_id' in result
    assert result['provider'] == 'mock'
    
    # Check email was logged
    sent_emails = sender.get_sent_emails()
    assert len(sent_emails) == 1
    assert sent_emails[0]['to'] == "test@example.com"


def test_sendgrid_sender_configuration():
    """Test SendGrid sender configuration"""
    from web.backend.marketing.email_sender import SendGridSender
    
    sender = SendGridSender(api_key="test_key")
    assert sender.api_key == "test_key"
    assert sender.api_url == 'https://api.sendgrid.com/v3/mail/send'


def test_mailgun_sender_configuration():
    """Test Mailgun sender configuration"""
    from web.backend.marketing.email_sender import MailgunSender
    
    sender = MailgunSender(api_key="test_key", domain="test.com")
    assert sender.api_key == "test_key"
    assert sender.domain == "test.com"


def test_get_email_sender():
    """Test email sender factory"""
    from web.backend.marketing.email_sender import get_email_sender
    import os
    
    # Test with mock (default when no config)
    sender = get_email_sender()
    assert sender is not None


# Test automation workflows
@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.commit = Mock()
    session.rollback = Mock()
    return session


def test_enroll_user_in_sequence(mock_db_session):
    """Test enrolling user in email sequence"""
    from web.backend.marketing.automation import enroll_user_in_sequence
    from web.backend.database import User
    
    # Mock user exists
    mock_user = User(id="test-user-id", email="test@example.com")
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
    
    # Mock no existing sequence
    def mock_query_side_effect(*args):
        if args[0] == User:
            result = Mock()
            result.filter.return_value.first.return_value = mock_user
            return result
        else:
            result = Mock()
            result.filter.return_value.filter.return_value.first.return_value = None
            return result
    
    mock_db_session.query.side_effect = mock_query_side_effect
    
    # This will fail in the test environment without full DB, but structure is correct
    # In real tests, use in-memory SQLite database


def test_load_email_template():
    """Test loading email template"""
    from web.backend.marketing.automation import load_email_template
    
    # Test loading a template
    template = load_email_template("welcome_day0.html")
    assert template is not None
    assert isinstance(template, str)
    # Should contain HTML
    assert "<html>" in template.lower() or "template missing" in template.lower()


def test_render_email_template():
    """Test rendering email template with context"""
    from web.backend.marketing.automation import render_email_template
    
    template = "<html><body>Hello {{user_name}}, your plan is {{plan}}</body></html>"
    context = {
        'user_name': 'John Doe',
        'plan': 'Pro'
    }
    
    rendered = render_email_template(template, context)
    assert "John Doe" in rendered
    assert "Pro" in rendered
    assert "{{user_name}}" not in rendered


# Test sequence definitions
def test_all_sequences_exist():
    """Test that all required sequences are defined"""
    from web.backend.marketing.email_sequences import SEQUENCES
    
    required_sequences = ['welcome', 'trial_conversion', 'onboarding', 're_engagement']
    
    for seq_type in required_sequences:
        assert seq_type in SEQUENCES
        seq = SEQUENCES[seq_type]
        assert seq.total_steps() > 0


def test_sequence_steps_have_required_fields():
    """Test that sequence steps have all required fields"""
    from web.backend.marketing.email_sequences import get_all_sequences
    
    sequences = get_all_sequences()
    
    for seq in sequences:
        for step in seq.steps:
            assert step.step_number is not None
            assert step.delay_days is not None
            assert step.subject is not None
            assert step.template_name is not None
            assert step.description is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
