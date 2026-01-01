"""
Email sending utilities for transactional emails
Supports trial expiration reminders and other notifications
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False
    PROJECT_CONFIG = None
    ModuleRegistration = None

logger = logging.getLogger(__name__)

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.email_service",
            file_path=__file__,
            description="Email sending service for transactional emails",
            dependencies=[],
            exports=["send_trial_expiration_reminder", "EmailService"]
        ))
    except Exception as e:
        logger.debug(f"Module registration failed: {e}")
        pass

class EmailService:
    """
    Email service for sending transactional emails.
    
    In production, integrate with:
    - SendGrid
    - AWS SES
    - Mailgun
    - Postmark
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize email service.
        
        Args:
            config: Optional email service configuration
        """
        self.config = config or {}
        self.templates_dir = Path(__file__).parent / 'email_templates'
        
    def load_template(self, template_name: str) -> str:
        """
        Load email template from file.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Template content as string
        """
        template_path = self.templates_dir / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")
            
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render template with context variables.
        
        Args:
            template: Template string
            context: Dictionary of variables to replace
            
        Returns:
            Rendered template
        """
        rendered = template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))
        return rendered
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send email using configured provider.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            from_email: Sender email (optional)
            reply_to: Reply-to email (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        from_email = from_email or os.getenv('EMAIL_FROM', 'noreply@receiptextractor.com')
        reply_to = reply_to or os.getenv('EMAIL_REPLY_TO', 'support@receiptextractor.com')
        
        try:
            # NOTE: Email service integration pending
            # Currently logs emails for development. For production deployment:
            # 1. Set EMAIL_PROVIDER env var to 'sendgrid' or 'ses'
            # 2. Configure provider credentials in .env
            # 3. Uncomment provider-specific methods below
            # See: https://github.com/aiparallel0/Web-and-Desktop-Apps/issues/TBD
            logger.info(f"[EMAIL] To: {to_email}, Subject: {subject}")
            logger.debug(f"[EMAIL] Content length: {len(html_content)} chars")
            
            # In production, replace with actual email sending:
            # if os.getenv('EMAIL_PROVIDER') == 'sendgrid':
            #     return self._send_via_sendgrid(to_email, subject, html_content, from_email)
            # elif os.getenv('EMAIL_PROVIDER') == 'ses':
            #     return self._send_via_ses(to_email, subject, html_content, from_email)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_trial_expiration_reminder(
        self,
        user_email: str,
        user_name: str,
        plan_name: str,
        days_remaining: int,
        expiration_date: str,
        receipts_processed: int = 0,
        time_saved: float = 0,
        accuracy_rate: float = 98.0,
        monthly_price: int = 19
    ) -> bool:
        """
        Send trial expiration reminder email.
        
        Args:
            user_email: User's email address
            user_name: User's name
            plan_name: Name of the trial plan
            days_remaining: Days until trial expires
            expiration_date: Trial expiration date (formatted string)
            receipts_processed: Number of receipts processed during trial
            time_saved: Hours saved during trial
            accuracy_rate: Average accuracy rate
            monthly_price: Monthly subscription price
            
        Returns:
            True if sent successfully
        """
        try:
            # Load template
            template = self.load_template('trial_expiration_reminder.html')
            
            # Prepare context
            base_url = os.getenv('BASE_URL', 'https://receiptextractor.com')
            context = {
                'user_name': user_name,
                'plan_name': plan_name,
                'days_remaining': days_remaining,
                'expiration_date': expiration_date,
                'receipts_processed': receipts_processed,
                'time_saved': f"{time_saved:.1f}",
                'accuracy_rate': f"{accuracy_rate:.1f}",
                'monthly_price': monthly_price,
                'upgrade_url': f"{base_url}/pricing.html?plan={plan_name.lower()}",
                'dashboard_url': f"{base_url}/dashboard.html",
                'contact_url': f"{base_url}/contact.html",
                'website_url': base_url,
                'pricing_url': f"{base_url}/pricing.html",
                'help_url': f"{base_url}/help.html",
                'unsubscribe_url': f"{base_url}/unsubscribe?email={user_email}"
            }
            
            # Render template
            html_content = self.render_template(template, context)
            
            # Send email
            subject = f"Your {plan_name} trial ends in {days_remaining} days"
            return self.send_email(user_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send trial expiration reminder: {e}")
            return False
    
    def send_verification_email(
        self,
        user_email: str,
        user_name: str,
        verification_token: str
    ) -> bool:
        """
        Send email verification email.
        
        Args:
            user_email: User's email address
            user_name: User's name
            verification_token: Email verification token
            
        Returns:
            True if sent successfully
        """
        try:
            template = self.load_template('email_verification.html')
            
            base_url = os.getenv('BASE_URL', 'http://localhost:3000')
            context = {
                'user_name': user_name or 'there',
                'verification_url': f"{base_url}/api/auth/verify-email?token={verification_token}",
                'base_url': base_url
            }
            
            html_content = self.render_template(template, context)
            subject = "Verify your email - Receipt Extractor"
            return self.send_email(user_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            return False
    
    def send_welcome_email(
        self,
        user_email: str,
        user_name: str,
        referral_code: str,
        trial_end_date: str
    ) -> bool:
        """
        Send welcome email after email verification.
        
        Args:
            user_email: User's email address
            user_name: User's name
            referral_code: User's referral code
            trial_end_date: Trial expiration date
            
        Returns:
            True if sent successfully
        """
        try:
            template = self.load_template('welcome.html')
            
            base_url = os.getenv('BASE_URL', 'http://localhost:3000')
            context = {
                'user_name': user_name or 'there',
                'referral_code': referral_code,
                'trial_end_date': trial_end_date,
                'dashboard_url': f"{base_url}/dashboard.html",
                'base_url': base_url
            }
            
            html_content = self.render_template(template, context)
            subject = "Welcome to Receipt Extractor - Your 14-Day Pro Trial Starts Now!"
            return self.send_email(user_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False
    
    def send_usage_alert(
        self,
        user_email: str,
        user_name: str,
        receipts_processed: int,
        receipts_limit: int,
        current_plan: str,
        reset_date: str
    ) -> bool:
        """
        Send usage alert email when approaching limit.
        
        Args:
            user_email: User's email address
            user_name: User's name
            receipts_processed: Number of receipts processed
            receipts_limit: Monthly limit
            current_plan: Current subscription plan
            reset_date: Date when usage resets
            
        Returns:
            True if sent successfully
        """
        try:
            template = self.load_template('usage_alert.html')
            
            usage_percentage = int((receipts_processed / receipts_limit) * 100)
            base_url = os.getenv('BASE_URL', 'http://localhost:3000')
            
            context = {
                'user_name': user_name or 'there',
                'usage_percentage': usage_percentage,
                'receipts_processed': receipts_processed,
                'receipts_limit': receipts_limit,
                'current_plan': current_plan.title(),
                'reset_date': reset_date,
                'near_limit': usage_percentage >= 90,
                'upgrade_url': f"{base_url}/pricing.html",
                'base_url': base_url
            }
            
            html_content = self.render_template(template, context)
            subject = f"Usage Alert: {usage_percentage}% of your monthly limit reached"
            return self.send_email(user_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send usage alert: {e}")
            return False

# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get or create EmailService singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

def send_trial_expiration_reminder(
    user_email: str,
    user_name: str,
    plan_name: str,
    days_remaining: int,
    **kwargs
) -> bool:
    """
    Convenience function to send trial expiration reminder.
    
    Args:
        user_email: User's email address
        user_name: User's name
        plan_name: Name of the trial plan
        days_remaining: Days until trial expires
        **kwargs: Additional context variables
        
    Returns:
        True if sent successfully
    """
    service = get_email_service()
    
    # Format expiration date
    expiration_date = kwargs.get('expiration_date')
    if not expiration_date:
        exp_datetime = datetime.utcnow() + timedelta(days=days_remaining)
        expiration_date = exp_datetime.strftime('%B %d, %Y')
    
    return service.send_trial_expiration_reminder(
        user_email=user_email,
        user_name=user_name,
        plan_name=plan_name,
        days_remaining=days_remaining,
        expiration_date=expiration_date,
        **kwargs
    )
