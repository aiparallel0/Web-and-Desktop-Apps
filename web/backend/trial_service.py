"""
Trial Management Service

Handles 14-day Pro trial activation, tracking, and expiration logic.
"""
import os
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.trial_service",
            file_path=__file__,
            description="Trial management for 14-day Pro trials",
            dependencies=[],
            exports=["TrialService", "activate_trial", "check_trial_status", "get_trial_days_remaining"]
        ))
    except Exception:
        pass


class TrialService:
    """Service for managing Pro trials."""
    
    TRIAL_DURATION_DAYS = 14
    TRIAL_PLAN = 'pro'
    
    def __init__(self):
        """Initialize trial service."""
        pass
    
    def activate_trial(self, user) -> bool:
        """
        Activate a 14-day Pro trial for a user.
        
        Args:
            user: User model instance
            
        Returns:
            True if trial activated successfully
        """
        try:
            # Check if trial already activated
            if user.trial_activated:
                logger.warning(f"Trial already activated for user {user.id}")
                return False
            
            # Activate trial
            user.trial_activated = True
            user.trial_start_date = datetime.utcnow()
            user.trial_end_date = datetime.utcnow() + timedelta(days=self.TRIAL_DURATION_DAYS)
            user.plan = self.TRIAL_PLAN  # Upgrade to Pro for trial
            
            logger.info(f"Trial activated for user {user.id}, expires {user.trial_end_date}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate trial for user {user.id}: {e}")
            return False
    
    def check_trial_status(self, user) -> Dict[str, Any]:
        """
        Check trial status for a user.
        
        Args:
            user: User model instance
            
        Returns:
            Dictionary with trial status information
        """
        if not user.trial_activated:
            return {
                'has_trial': False,
                'is_active': False,
                'days_remaining': 0,
                'expired': False
            }
        
        now = datetime.utcnow()
        is_active = user.trial_end_date > now if user.trial_end_date else False
        days_remaining = (user.trial_end_date - now).days if user.trial_end_date and is_active else 0
        
        return {
            'has_trial': True,
            'is_active': is_active,
            'days_remaining': max(0, days_remaining),
            'expired': user.trial_end_date <= now if user.trial_end_date else False,
            'trial_start': user.trial_start_date.isoformat() if user.trial_start_date else None,
            'trial_end': user.trial_end_date.isoformat() if user.trial_end_date else None
        }
    
    def get_trial_days_remaining(self, user) -> int:
        """
        Get number of days remaining in trial.
        
        Args:
            user: User model instance
            
        Returns:
            Days remaining (0 if no trial or expired)
        """
        if not user.trial_activated or not user.trial_end_date:
            return 0
        
        now = datetime.utcnow()
        if user.trial_end_date <= now:
            return 0
        
        return (user.trial_end_date - now).days
    
    def should_send_expiration_reminder(self, user, reminder_days: int) -> bool:
        """
        Check if expiration reminder should be sent.
        
        Args:
            user: User model instance
            reminder_days: Send reminder when this many days remain
            
        Returns:
            True if reminder should be sent
        """
        days_remaining = self.get_trial_days_remaining(user)
        return days_remaining == reminder_days and user.trial_activated
    
    def expire_trial(self, user) -> bool:
        """
        Expire trial and downgrade user to free plan.
        
        Args:
            user: User model instance
            
        Returns:
            True if expired successfully
        """
        try:
            if not user.trial_activated:
                return False
            
            # Downgrade to free plan
            user.plan = 'free'
            
            logger.info(f"Trial expired for user {user.id}, downgraded to free plan")
            return True
            
        except Exception as e:
            logger.error(f"Failed to expire trial for user {user.id}: {e}")
            return False


# Singleton instance
_trial_service = None


def get_trial_service() -> TrialService:
    """Get or create TrialService singleton."""
    global _trial_service
    if _trial_service is None:
        _trial_service = TrialService()
    return _trial_service


def activate_trial(user) -> bool:
    """
    Convenience function to activate trial.
    
    Args:
        user: User model instance
        
    Returns:
        True if activated successfully
    """
    service = get_trial_service()
    return service.activate_trial(user)


def check_trial_status(user) -> Dict[str, Any]:
    """
    Convenience function to check trial status.
    
    Args:
        user: User model instance
        
    Returns:
        Trial status dictionary
    """
    service = get_trial_service()
    return service.check_trial_status(user)


def get_trial_days_remaining(user) -> int:
    """
    Convenience function to get days remaining.
    
    Args:
        user: User model instance
        
    Returns:
        Days remaining in trial
    """
    service = get_trial_service()
    return service.get_trial_days_remaining(user)
