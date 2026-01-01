"""
Email sending service for marketing automation

Supports SendGrid and Mailgun for transactional email delivery.
Includes email tracking, template rendering, and error handling.
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.marketing.email_sender",
            file_path=__file__,
            description="Email sending service for marketing automation",
            dependencies=[],
            exports=["EmailSender", "SendGridSender", "MailgunSender", "get_email_sender"]
        ))
    except Exception:
        pass

class EmailSender:
    """Base class for email sending services"""
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        tracking_enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            from_email: Sender email address
            from_name: Sender name
            tracking_enabled: Enable open/click tracking
            metadata: Additional metadata for tracking
            
        Returns:
            Dict with success status and message ID
        """
        raise NotImplementedError("Subclass must implement send_email")
    
    def send_template_email(
        self,
        to_email: str,
        template_id: str,
        template_data: Dict[str, Any],
        subject: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email using a template
        
        Args:
            to_email: Recipient email address
            template_id: Template ID/name
            template_data: Data to render template with
            subject: Email subject (may be in template)
            from_email: Sender email address
            from_name: Sender name
            
        Returns:
            Dict with success status and message ID
        """
        raise NotImplementedError("Subclass must implement send_template_email")

class SendGridSender(EmailSender):
    """SendGrid email sender implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SendGrid sender
        
        Args:
            api_key: SendGrid API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@yourdomain.com')
        self.from_name = os.getenv('SENDGRID_FROM_NAME', 'Receipt Extractor')
        self.api_url = 'https://api.sendgrid.com/v3/mail/send'
        
        if not self.api_key:
            logger.warning("SendGrid API key not configured")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        tracking_enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email via SendGrid API"""
        if not self.api_key:
            return {'success': False, 'error': 'SendGrid API key not configured'}
        
        payload = {
            'personalizations': [{
                'to': [{'email': to_email}],
                'subject': subject
            }],
            'from': {
                'email': from_email or self.from_email,
                'name': from_name or self.from_name
            },
            'content': [
                {'type': 'text/html', 'value': html_content}
            ],
            'tracking_settings': {
                'click_tracking': {'enable': tracking_enabled},
                'open_tracking': {'enable': tracking_enabled}
            }
        }
        
        # Add plain text version if provided
        if text_content:
            payload['content'].insert(0, {'type': 'text/plain', 'value': text_content})
        
        # Add custom metadata
        if metadata:
            payload['custom_args'] = metadata
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully to {to_email}")
                return {
                    'success': True,
                    'message_id': response.headers.get('X-Message-Id'),
                    'provider': 'sendgrid'
                }
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'SendGrid error: {response.status_code}',
                    'details': response.text
                }
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_template_email(
        self,
        to_email: str,
        template_id: str,
        template_data: Dict[str, Any],
        subject: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email using SendGrid dynamic template"""
        if not self.api_key:
            return {'success': False, 'error': 'SendGrid API key not configured'}
        
        payload = {
            'personalizations': [{
                'to': [{'email': to_email}],
                'dynamic_template_data': template_data
            }],
            'from': {
                'email': from_email or self.from_email,
                'name': from_name or self.from_name
            },
            'template_id': template_id
        }
        
        if subject:
            payload['personalizations'][0]['subject'] = subject
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 202:
                logger.info(f"Template email sent successfully to {to_email}")
                return {
                    'success': True,
                    'message_id': response.headers.get('X-Message-Id'),
                    'provider': 'sendgrid'
                }
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'SendGrid error: {response.status_code}',
                    'details': response.text
                }
        except Exception as e:
            logger.error(f"Failed to send template email via SendGrid: {e}")
            return {'success': False, 'error': str(e)}

class MailgunSender(EmailSender):
    """Mailgun email sender implementation"""
    
    def __init__(self, api_key: Optional[str] = None, domain: Optional[str] = None):
        """
        Initialize Mailgun sender
        
        Args:
            api_key: Mailgun API key (defaults to env var)
            domain: Mailgun domain (defaults to env var)
        """
        self.api_key = api_key or os.getenv('MAILGUN_API_KEY')
        self.domain = domain or os.getenv('MAILGUN_DOMAIN')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@yourdomain.com')
        self.from_name = os.getenv('SENDGRID_FROM_NAME', 'Receipt Extractor')
        
        if not self.api_key or not self.domain:
            logger.warning("Mailgun API key or domain not configured")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        tracking_enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email via Mailgun API"""
        if not self.api_key or not self.domain:
            return {'success': False, 'error': 'Mailgun API key or domain not configured'}
        
        api_url = f'https://api.mailgun.net/v3/{self.domain}/messages'
        
        sender_email = from_email or self.from_email
        sender_name = from_name or self.from_name
        from_field = f"{sender_name} <{sender_email}>"
        
        data = {
            'from': from_field,
            'to': to_email,
            'subject': subject,
            'html': html_content,
            'o:tracking': 'yes' if tracking_enabled else 'no',
            'o:tracking-clicks': 'yes' if tracking_enabled else 'no',
            'o:tracking-opens': 'yes' if tracking_enabled else 'no'
        }
        
        if text_content:
            data['text'] = text_content
        
        # Add custom metadata
        if metadata:
            for key, value in metadata.items():
                data[f'v:{key}'] = str(value)
        
        try:
            response = requests.post(
                api_url,
                auth=('api', self.api_key),
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Email sent successfully to {to_email}")
                return {
                    'success': True,
                    'message_id': result.get('id'),
                    'provider': 'mailgun'
                }
            else:
                logger.error(f"Mailgun error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Mailgun error: {response.status_code}',
                    'details': response.text
                }
        except Exception as e:
            logger.error(f"Failed to send email via Mailgun: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_template_email(
        self,
        to_email: str,
        template_id: str,
        template_data: Dict[str, Any],
        subject: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email using Mailgun template"""
        if not self.api_key or not self.domain:
            return {'success': False, 'error': 'Mailgun API key or domain not configured'}
        
        api_url = f'https://api.mailgun.net/v3/{self.domain}/messages'
        
        sender_email = from_email or self.from_email
        sender_name = from_name or self.from_name
        from_field = f"{sender_name} <{sender_email}>"
        
        data = {
            'from': from_field,
            'to': to_email,
            'template': template_id,
            'h:X-Mailgun-Variables': str(template_data),
            'o:tracking': 'yes',
            'o:tracking-clicks': 'yes',
            'o:tracking-opens': 'yes'
        }
        
        if subject:
            data['subject'] = subject
        
        try:
            response = requests.post(
                api_url,
                auth=('api', self.api_key),
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Template email sent successfully to {to_email}")
                return {
                    'success': True,
                    'message_id': result.get('id'),
                    'provider': 'mailgun'
                }
            else:
                logger.error(f"Mailgun error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Mailgun error: {response.status_code}',
                    'details': response.text
                }
        except Exception as e:
            logger.error(f"Failed to send template email via Mailgun: {e}")
            return {'success': False, 'error': str(e)}

class MockEmailSender(EmailSender):
    """Mock email sender for testing"""
    
    def __init__(self):
        """Initialize mock sender"""
        self.sent_emails: List[Dict[str, Any]] = []
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        tracking_enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Mock send email (just logs)"""
        email_data = {
            'to': to_email,
            'subject': subject,
            'html': html_content[:100],  # Store first 100 chars
            'text': text_content[:100] if text_content else None,
            'from_email': from_email,
            'from_name': from_name,
            'tracking': tracking_enabled,
            'metadata': metadata,
            'sent_at': datetime.utcnow().isoformat()
        }
        self.sent_emails.append(email_data)
        logger.info(f"[MOCK] Email sent to {to_email}: {subject}")
        return {
            'success': True,
            'message_id': f'mock_{len(self.sent_emails)}',
            'provider': 'mock'
        }
    
    def send_template_email(
        self,
        to_email: str,
        template_id: str,
        template_data: Dict[str, Any],
        subject: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mock send template email"""
        email_data = {
            'to': to_email,
            'template_id': template_id,
            'template_data': template_data,
            'subject': subject,
            'from_email': from_email,
            'from_name': from_name,
            'sent_at': datetime.utcnow().isoformat()
        }
        self.sent_emails.append(email_data)
        logger.info(f"[MOCK] Template email sent to {to_email}: {template_id}")
        return {
            'success': True,
            'message_id': f'mock_{len(self.sent_emails)}',
            'provider': 'mock'
        }
    
    def get_sent_emails(self) -> List[Dict[str, Any]]:
        """Get all sent emails (for testing)"""
        return self.sent_emails
    
    def clear(self):
        """Clear sent emails"""
        self.sent_emails = []

def get_email_sender() -> EmailSender:
    """
    Get configured email sender based on environment
    
    Returns:
        EmailSender instance (SendGrid, Mailgun, or Mock)
    """
    email_service = os.getenv('EMAIL_SERVICE', 'sendgrid').lower()
    
    if email_service == 'sendgrid':
        return SendGridSender()
    elif email_service == 'mailgun':
        return MailgunSender()
    elif email_service == 'mock':
        return MockEmailSender()
    else:
        logger.warning(f"Unknown email service: {email_service}, using mock")
        return MockEmailSender()

__all__ = [
    'EmailSender',
    'SendGridSender',
    'MailgunSender',
    'MockEmailSender',
    'get_email_sender'
]
