"""
Referral System Service

Handles referral code generation, tracking, and rewards (3 referrals = 1 month free).
"""
import os
import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.referral_service",
            file_path=__file__,
            description="Referral system for user acquisition and rewards",
            dependencies=[],
            exports=["ReferralService", "generate_referral_code", "track_referral", "check_rewards"]
        ))
    except Exception:
        pass

class ReferralService:
    """Service for managing referral program."""
    
    REFERRALS_FOR_REWARD = 3  # Number of referrals needed for reward
    REWARD_MONTHS = 1  # Free months granted as reward
    CODE_LENGTH = 8
    
    def __init__(self):
        """Initialize referral service."""
        pass
    
    def generate_referral_code(self, user_id: str = None) -> str:
        """
        Generate a unique referral code.
        
        Args:
            user_id: Optional user ID to incorporate
            
        Returns:
            Unique referral code (8 characters)
        """
        # Use uppercase letters and digits only (avoid confusing characters like O/0, I/1)
        alphabet = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
        code = ''.join(secrets.choice(alphabet) for _ in range(self.CODE_LENGTH))
        return code
    
    def create_referral(self, db_session, referrer_id: str, referred_email: str = None, referral_code: str = None):
        """
        Create a referral record.
        
        Args:
            db_session: Database session
            referrer_id: ID of user who sent the referral
            referred_email: Email of referred user (optional)
            referral_code: Referral code used
            
        Returns:
            Referral model instance
        """
        try:
            from web.backend.database import Referral
            
            referral = Referral(
                referrer_id=referrer_id,
                referral_code=referral_code,
                email=referred_email,
                status='pending'
            )
            
            db_session.add(referral)
            db_session.commit()
            
            logger.info(f"Referral created: {referrer_id} -> {referred_email}")
            return referral
            
        except Exception as e:
            logger.error(f"Failed to create referral: {e}")
            db_session.rollback()
            return None
    
    def complete_referral(self, db_session, referral_code: str, referred_user_id: str) -> bool:
        """
        Mark referral as completed when referred user signs up.
        
        Args:
            db_session: Database session
            referral_code: Referral code
            referred_user_id: ID of user who signed up
            
        Returns:
            True if completed successfully
        """
        try:
            from web.backend.database import Referral, User
            
            # Find pending referral with this code
            referral = db_session.query(Referral).filter(
                Referral.referral_code == referral_code,
                Referral.status == 'pending'
            ).first()
            
            if not referral:
                logger.warning(f"No pending referral found for code {referral_code}")
                return False
            
            # Update referral
            referral.referred_user_id = referred_user_id
            referral.status = 'signed_up'
            referral.completed_at = datetime.utcnow()
            
            # Update referrer's referral count
            referrer = db_session.query(User).filter(User.id == referral.referrer_id).first()
            if referrer:
                referrer.referral_count = (referrer.referral_count or 0) + 1
            
            # Also update referred user's referred_by field
            referred_user = db_session.query(User).filter(User.id == referred_user_id).first()
            if referred_user:
                referred_user.referred_by = referral.referrer_id
            
            db_session.commit()
            
            logger.info(f"Referral completed: {referral.referrer_id} -> {referred_user_id}")
            
            # Check if referrer earned a reward
            self.check_and_grant_reward(db_session, referral.referrer_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete referral: {e}")
            db_session.rollback()
            return False
    
    def check_and_grant_reward(self, db_session, user_id: str) -> bool:
        """
        Check if user has earned referral rewards and grant them.
        
        Args:
            db_session: Database session
            user_id: User ID to check
            
        Returns:
            True if reward granted
        """
        try:
            from web.backend.database import Referral, User
            
            # Count successful referrals
            completed_referrals = db_session.query(Referral).filter(
                Referral.referrer_id == user_id,
                Referral.status == 'signed_up',
                Referral.reward_granted == False
            ).all()
            
            num_unrewarded = len(completed_referrals)
            
            # Check if user earned a reward
            if num_unrewarded >= self.REFERRALS_FOR_REWARD:
                # Grant reward
                user = db_session.query(User).filter(User.id == user_id).first()
                if user:
                    # Add reward months
                    user.referral_reward_months = (user.referral_reward_months or 0) + self.REWARD_MONTHS
                    
                    # Mark referrals as rewarded
                    for i in range(self.REFERRALS_FOR_REWARD):
                        completed_referrals[i].reward_granted = True
                        completed_referrals[i].reward_granted_at = datetime.utcnow()
                        completed_referrals[i].status = 'rewarded'
                    
                    db_session.commit()
                    
                    logger.info(f"Reward granted to user {user_id}: {self.REWARD_MONTHS} month(s) free")
                    
                    # Send reward notification email
                    try:
                        from web.backend.email_service import EmailService
                        from web.backend.database import User
                        
                        user = db_session.query(User).filter(User.id == user_id).first()
                        if user and user.email:
                            email_service = EmailService()
                            subject = f"🎉 Congrats! You've earned {self.REWARD_MONTHS} month(s) free!"
                            html_content = f"""
                            <html>
                            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                                <h2>Congratulations! 🎉</h2>
                                <p>Great news! You've successfully referred {self.REFERRALS_FOR_REWARD} users who signed up.</p>
                                <p>As a reward, we've added <strong>{self.REWARD_MONTHS} month(s)</strong> of free Pro access to your account!</p>
                                <p>Thank you for spreading the word about Receipt Extractor.</p>
                                <p>Keep referring friends to earn more rewards!</p>
                                <p>Best regards,<br>The Receipt Extractor Team</p>
                            </body>
                            </html>
                            """
                            email_service.send_email(user.email, subject, html_content)
                    except Exception as email_error:
                        # Don't fail the reward grant if email fails
                        logger.warning(f"Failed to send reward notification email: {email_error}")
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check/grant reward: {e}")
            db_session.rollback()
            return False
    
    def get_referral_stats(self, db_session, user_id: str) -> Dict[str, Any]:
        """
        Get referral statistics for a user.
        
        Args:
            db_session: Database session
            user_id: User ID
            
        Returns:
            Dictionary with referral stats
        """
        try:
            from web.backend.database import Referral, User
            
            user = db_session.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            # Count referrals
            total_referrals = db_session.query(Referral).filter(
                Referral.referrer_id == user_id
            ).count()
            
            completed_referrals = db_session.query(Referral).filter(
                Referral.referrer_id == user_id,
                Referral.status.in_(['signed_up', 'rewarded'])
            ).count()
            
            pending_referrals = db_session.query(Referral).filter(
                Referral.referrer_id == user_id,
                Referral.status == 'pending'
            ).count()
            
            # Calculate progress to next reward
            unrewarded_referrals = db_session.query(Referral).filter(
                Referral.referrer_id == user_id,
                Referral.status == 'signed_up',
                Referral.reward_granted == False
            ).count()
            
            progress_to_reward = unrewarded_referrals % self.REFERRALS_FOR_REWARD
            referrals_needed = self.REFERRALS_FOR_REWARD - progress_to_reward
            
            return {
                'referral_code': user.referral_code,
                'total_referrals': total_referrals,
                'completed_referrals': completed_referrals,
                'pending_referrals': pending_referrals,
                'reward_months_earned': user.referral_reward_months or 0,
                'progress_to_next_reward': progress_to_reward,
                'referrals_needed_for_reward': referrals_needed,
                'total_rewards_earned': (user.referral_reward_months or 0) // self.REWARD_MONTHS
            }
            
        except Exception as e:
            logger.error(f"Failed to get referral stats: {e}")
            return {}

# Singleton instance
_referral_service = None

def get_referral_service() -> ReferralService:
    """Get or create ReferralService singleton."""
    global _referral_service
    if _referral_service is None:
        _referral_service = ReferralService()
    return _referral_service

def generate_referral_code(user_id: str = None) -> str:
    """
    Convenience function to generate referral code.
    
    Args:
        user_id: Optional user ID
        
    Returns:
        Referral code
    """
    service = get_referral_service()
    return service.generate_referral_code(user_id)

def track_referral(db_session, referral_code: str, referred_user_id: str) -> bool:
    """
    Convenience function to track referral completion.
    
    Args:
        db_session: Database session
        referral_code: Referral code
        referred_user_id: ID of referred user
        
    Returns:
        True if tracked successfully
    """
    service = get_referral_service()
    return service.complete_referral(db_session, referral_code, referred_user_id)

def check_rewards(db_session, user_id: str) -> bool:
    """
    Convenience function to check and grant rewards.
    
    Args:
        db_session: Database session
        user_id: User ID
        
    Returns:
        True if reward granted
    """
    service = get_referral_service()
    return service.check_and_grant_reward(db_session, user_id)
