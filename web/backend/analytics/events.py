"""
Analytics event definitions

Defines standard events to track throughout the user lifecycle:
- User signup and authentication
- Receipt processing and API usage
- Trial and subscription events
- Feature usage and engagement
"""
import logging
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# CEFR integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.analytics.events",
            file_path=__file__,
            description="Analytics event definitions and tracking schemas",
            dependencies=[],
            exports=["EventType", "EventProperties", "create_event"]
        ))
    except Exception:
        pass

class EventType(str, Enum):
    """Standard analytics event types"""
    
    # User Lifecycle Events
    USER_SIGNUP = "user_signup"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    EMAIL_VERIFIED = "email_verified"
    PASSWORD_RESET = "password_reset"
    
    # Onboarding Events
    ONBOARDING_STARTED = "onboarding_started"
    ONBOARDING_STEP_COMPLETED = "onboarding_step_completed"
    ONBOARDING_COMPLETED = "onboarding_completed"
    ONBOARDING_SKIPPED = "onboarding_skipped"
    
    # Receipt Processing Events
    RECEIPT_UPLOADED = "receipt_uploaded"
    RECEIPT_PROCESSED = "receipt_processed"
    RECEIPT_EXPORTED = "receipt_exported"
    RECEIPT_DELETED = "receipt_deleted"
    BATCH_PROCESSING_STARTED = "batch_processing_started"
    BATCH_PROCESSING_COMPLETED = "batch_processing_completed"
    
    # API Usage Events
    API_KEY_CREATED = "api_key_created"
    API_KEY_DELETED = "api_key_deleted"
    API_REQUEST_MADE = "api_request_made"
    API_ERROR = "api_error"
    
    # Trial & Subscription Events
    TRIAL_STARTED = "trial_started"
    TRIAL_ENDING_WARNING_VIEWED = "trial_ending_warning_viewed"
    TRIAL_ENDED = "trial_ended"
    UPGRADE_BUTTON_CLICKED = "upgrade_button_clicked"
    PRICING_PAGE_VIEWED = "pricing_page_viewed"
    CHECKOUT_STARTED = "checkout_started"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    SUBSCRIPTION_DOWNGRADED = "subscription_downgraded"
    SUBSCRIPTION_CANCELED = "subscription_canceled"
    SUBSCRIPTION_RENEWED = "subscription_renewed"
    
    # Feature Usage Events
    MODEL_SELECTED = "model_selected"
    CLOUD_STORAGE_CONNECTED = "cloud_storage_connected"
    CLOUD_STORAGE_DISCONNECTED = "cloud_storage_disconnected"
    TRAINING_JOB_STARTED = "training_job_started"
    TRAINING_JOB_COMPLETED = "training_job_completed"
    
    # Engagement Events
    DASHBOARD_VIEWED = "dashboard_viewed"
    HELP_ARTICLE_VIEWED = "help_article_viewed"
    SUPPORT_TICKET_CREATED = "support_ticket_created"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    REFERRAL_CODE_SHARED = "referral_code_shared"
    REFERRAL_COMPLETED = "referral_completed"
    
    # Marketing Events
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    LANDING_PAGE_VIEWED = "landing_page_viewed"
    CTA_CLICKED = "cta_clicked"
    
    # Churn Events
    USER_INACTIVE_30_DAYS = "user_inactive_30_days"
    USER_INACTIVE_60_DAYS = "user_inactive_60_days"
    USER_INACTIVE_90_DAYS = "user_inactive_90_days"
    ACCOUNT_DEACTIVATED = "account_deactivated"

class EventProperties:
    """Helper class for event property schemas"""
    
    @staticmethod
    def user_signup(email: str, referral_source: Optional[str] = None, utm_params: Optional[Dict] = None) -> Dict[str, Any]:
        """Properties for user signup event"""
        props = {
            'email': email,
            'timestamp': 'auto'
        }
        if referral_source:
            props['referral_source'] = referral_source
        if utm_params:
            props.update(utm_params)
        return props
    
    @staticmethod
    def receipt_processed(
        model_id: str,
        processing_time: float,
        confidence: Optional[float] = None,
        items_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """Properties for receipt processed event"""
        return {
            'model_id': model_id,
            'processing_time': processing_time,
            'confidence': confidence,
            'items_count': items_count
        }
    
    @staticmethod
    def api_request(
        endpoint: str,
        method: str,
        response_code: int,
        response_time: float
    ) -> Dict[str, Any]:
        """Properties for API request event"""
        return {
            'endpoint': endpoint,
            'method': method,
            'response_code': response_code,
            'response_time': response_time
        }
    
    @staticmethod
    def payment(
        plan: str,
        amount: float,
        currency: str = 'USD',
        payment_method: Optional[str] = None,
        success: bool = True
    ) -> Dict[str, Any]:
        """Properties for payment event"""
        return {
            'plan': plan,
            'amount': amount,
            'currency': currency,
            'payment_method': payment_method,
            'success': success
        }
    
    @staticmethod
    def feature_usage(
        feature_name: str,
        feature_value: Any = None,
        duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """Properties for feature usage event"""
        return {
            'feature_name': feature_name,
            'feature_value': feature_value,
            'duration': duration
        }

def create_event(
    event_type: EventType,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
    utm_params: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a standardized event object
    
    Args:
        event_type: Type of event from EventType enum
        user_id: User UUID (optional for anonymous events)
        session_id: Session identifier
        properties: Event-specific properties
        utm_params: UTM tracking parameters
        
    Returns:
        Event dictionary ready for tracking
    """
    event = {
        'event': event_type.value if isinstance(event_type, EventType) else event_type,
        'properties': properties or {},
    }
    
    if user_id:
        event['user_id'] = user_id
    
    if session_id:
        event['session_id'] = session_id
    
    # Add UTM parameters
    if utm_params:
        event['utm_source'] = utm_params.get('utm_source')
        event['utm_medium'] = utm_params.get('utm_medium')
        event['utm_campaign'] = utm_params.get('utm_campaign')
        event['utm_term'] = utm_params.get('utm_term')
        event['utm_content'] = utm_params.get('utm_content')
    
    return event

__all__ = [
    'EventType',
    'EventProperties',
    'create_event'
]
