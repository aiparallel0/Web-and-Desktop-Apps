"""
Tests for email verification, trial management, and referral system
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch


def test_trial_service_activation():
    """Test trial activation logic"""
    from web.backend.trial_service import TrialService
    
    service = TrialService()
    
    # Mock user object
    user = Mock()
    user.id = "test-user-id"
    user.trial_activated = False
    user.trial_start_date = None
    user.trial_end_date = None
    user.plan = "free"
    
    # Activate trial
    result = service.activate_trial(user)
    
    # Verify activation
    assert result is True
    assert user.trial_activated is True
    assert user.trial_start_date is not None
    assert user.trial_end_date is not None
    assert user.plan == "pro"
    
    # Verify trial duration is 14 days
    duration = (user.trial_end_date - user.trial_start_date).days
    assert duration == 14


def test_trial_service_status():
    """Test trial status checking"""
    from web.backend.trial_service import TrialService
    
    service = TrialService()
    
    # Mock user with active trial
    user = Mock()
    user.trial_activated = True
    user.trial_start_date = datetime.utcnow() - timedelta(days=7)
    user.trial_end_date = datetime.utcnow() + timedelta(days=7)
    
    status = service.check_trial_status(user)
    
    assert status['has_trial'] is True
    assert status['is_active'] is True
    assert status['days_remaining'] == 7
    assert status['expired'] is False


def test_trial_service_expired():
    """Test expired trial detection"""
    from web.backend.trial_service import TrialService
    
    service = TrialService()
    
    # Mock user with expired trial
    user = Mock()
    user.trial_activated = True
    user.trial_start_date = datetime.utcnow() - timedelta(days=20)
    user.trial_end_date = datetime.utcnow() - timedelta(days=6)
    
    status = service.check_trial_status(user)
    
    assert status['has_trial'] is True
    assert status['is_active'] is False
    assert status['days_remaining'] == 0
    assert status['expired'] is True


def test_referral_code_generation():
    """Test referral code generation"""
    from web.backend.referral_service import ReferralService
    
    service = ReferralService()
    
    # Generate code
    code = service.generate_referral_code()
    
    # Verify format
    assert len(code) == 8
    assert code.isalnum()
    assert code.isupper()  # Should be uppercase only


def test_email_service_verification_email():
    """Test email verification email generation"""
    from web.backend.email_service import EmailService
    
    service = EmailService()
    
    # Mock send_email to capture parameters
    with patch.object(service, 'send_email', return_value=True) as mock_send:
        result = service.send_verification_email(
            user_email="test@example.com",
            user_name="Test User",
            verification_token="test-token-123"
        )
        
        assert result is True
        assert mock_send.called
        
        # Verify email was called with correct params
        call_args = mock_send.call_args
        assert call_args[0][0] == "test@example.com"
        assert "Verify" in call_args[0][1]  # Subject contains "Verify"


def test_email_service_welcome_email():
    """Test welcome email generation"""
    from web.backend.email_service import EmailService
    
    service = EmailService()
    
    with patch.object(service, 'send_email', return_value=True) as mock_send:
        result = service.send_welcome_email(
            user_email="test@example.com",
            user_name="Test User",
            referral_code="ABC12345",
            trial_end_date="January 1, 2025"
        )
        
        assert result is True
        assert mock_send.called
        
        call_args = mock_send.call_args
        assert call_args[0][0] == "test@example.com"
        assert "Welcome" in call_args[0][1]


def test_email_service_usage_alert():
    """Test usage alert email generation"""
    from web.backend.email_service import EmailService
    
    service = EmailService()
    
    with patch.object(service, 'send_email', return_value=True) as mock_send:
        result = service.send_usage_alert(
            user_email="test@example.com",
            user_name="Test User",
            receipts_processed=450,
            receipts_limit=500,
            current_plan="pro",
            reset_date="January 1, 2025"
        )
        
        assert result is True
        assert mock_send.called
        
        call_args = mock_send.call_args
        assert call_args[0][0] == "test@example.com"
        assert "Usage Alert" in call_args[0][1] or "90%" in call_args[0][1]


def test_referral_stats_calculation():
    """Test referral statistics calculation"""
    from web.backend.referral_service import ReferralService
    
    service = ReferralService()
    
    # Test reward calculation
    assert service.REFERRALS_FOR_REWARD == 3
    assert service.REWARD_MONTHS == 1
    
    # Verify constants
    assert service.CODE_LENGTH == 8


if __name__ == "__main__":
    # Run tests
    test_trial_service_activation()
    test_trial_service_status()
    test_trial_service_expired()
    test_referral_code_generation()
    test_email_service_verification_email()
    test_email_service_welcome_email()
    test_email_service_usage_alert()
    test_referral_stats_calculation()
    
    print("✅ All tests passed!")
