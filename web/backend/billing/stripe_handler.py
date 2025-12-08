"""
=============================================================================
STRIPE HANDLER - Stripe API Operations
=============================================================================

Handles all Stripe API interactions for subscription management.

Usage:
    from billing.stripe_handler import StripeHandler
    
    handler = StripeHandler()
    customer = handler.create_customer("user@example.com", "John Doe")
    session = handler.create_checkout_session(customer.id, "price_xxx")

=============================================================================
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from shared.utils.optional_imports import OptionalImport

# Import telemetry utilities
from shared.utils.telemetry import get_tracer, set_span_attributes

logger = logging.getLogger(__name__)

# Import stripe
stripe_import = OptionalImport('stripe', 'pip install stripe')
stripe = stripe_import.module
STRIPE_AVAILABLE = stripe_import.is_available


class StripeHandler:
    """
    Handler for Stripe API operations.
    
    Provides methods for:
    - Customer management
    - Subscription creation and management
    - Checkout session creation
    - Webhook event processing
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize Stripe handler.
        
        Args:
            api_key: Stripe secret API key (defaults to STRIPE_SECRET_KEY env var)
        """
        if not STRIPE_AVAILABLE:
            raise ImportError("Stripe SDK required. Install with: pip install stripe>=7.0.0")
        
        self.api_key = api_key or os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        if not self.api_key:
            logger.warning("STRIPE_SECRET_KEY not set. Stripe operations will fail.")
        else:
            stripe.api_key = self.api_key
            logger.info("StripeHandler initialized")
    
    # =========================================================================
    # CUSTOMER MANAGEMENT
    # =========================================================================
    
    def create_customer(
        self,
        email: str,
        name: str = None,
        metadata: Dict[str, str] = None
    ) -> Optional[Any]:
        """
        Create a new Stripe customer.
        
        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata
            
        Returns:
            Stripe Customer object or None on error
        """
        tracer = get_tracer()
        with tracer.start_as_current_span("stripe.create_customer") as span:
            try:
                # Sanitize email for logging (show domain only)
                email_domain = email.split('@')[1] if '@' in email else 'unknown'
                
                set_span_attributes(span, {
                    "stripe.operation": "create_customer",
                    "stripe.email_domain": email_domain,
                    "stripe.has_name": name is not None
                })
                
                customer = stripe.Customer.create(
                    email=email,
                    name=name,
                    metadata=metadata or {}
                )
                
                set_span_attributes(span, {
                    "stripe.customer_id": customer.id[:8] + "...",  # Truncate for privacy
                    "stripe.success": True
                })
                
                logger.info(f"Created Stripe customer: {customer.id}")
                return customer
            except stripe.error.StripeError as e:
                logger.error(f"Failed to create customer: {e}")
                span.record_exception(e)
                
                set_span_attributes(span, {
                    "stripe.success": False,
                    "stripe.error_type": type(e).__name__
                })
                
                return None
    
    def get_customer(self, customer_id: str) -> Optional[Any]:
        """
        Retrieve a Stripe customer.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Stripe Customer object or None
        """
        try:
            return stripe.Customer.retrieve(customer_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve customer: {e}")
            return None
    
    def update_customer(
        self,
        customer_id: str,
        email: str = None,
        name: str = None,
        metadata: Dict[str, str] = None
    ) -> Optional[Any]:
        """
        Update a Stripe customer.
        
        Args:
            customer_id: Stripe customer ID
            email: New email
            name: New name
            metadata: Updated metadata
            
        Returns:
            Updated customer or None on error
        """
        try:
            update_data = {}
            if email:
                update_data['email'] = email
            if name:
                update_data['name'] = name
            if metadata:
                update_data['metadata'] = metadata
            
            return stripe.Customer.modify(customer_id, **update_data)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update customer: {e}")
            return None
    
    # =========================================================================
    # SUBSCRIPTION MANAGEMENT
    # =========================================================================
    
    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = 0
    ) -> Optional[Any]:
        """
        Create a subscription for a customer.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            trial_days: Trial period in days
            
        Returns:
            Stripe Subscription object or None
        """
        try:
            subscription_data = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'payment_behavior': 'default_incomplete',
                'expand': ['latest_invoice.payment_intent']
            }
            
            if trial_days > 0:
                subscription_data['trial_period_days'] = trial_days
            
            subscription = stripe.Subscription.create(**subscription_data)
            logger.info(f"Created subscription: {subscription.id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            return None
    
    def get_subscription(self, subscription_id: str) -> Optional[Any]:
        """
        Retrieve a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Stripe Subscription object or None
        """
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription: {e}")
            return None
    
    def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> Optional[Any]:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of billing period
            
        Returns:
            Updated subscription or None
        """
        tracer = get_tracer()
        with tracer.start_as_current_span("stripe.cancel_subscription") as span:
            try:
                set_span_attributes(span, {
                    "stripe.operation": "cancel_subscription",
                    "stripe.subscription_id": subscription_id[:8] + "...",
                    "stripe.at_period_end": at_period_end
                })
                
                if at_period_end:
                    subscription = stripe.Subscription.modify(
                        subscription_id,
                        cancel_at_period_end=True
                    )
                else:
                    subscription = stripe.Subscription.delete(subscription_id)
                
                set_span_attributes(span, {
                    "stripe.success": True,
                    "stripe.cancel_type": "at_period_end" if at_period_end else "immediate"
                })
                
                logger.info(f"Cancelled subscription: {subscription_id}")
                return subscription
            except stripe.error.StripeError as e:
                logger.error(f"Failed to cancel subscription: {e}")
                span.record_exception(e)
                
                set_span_attributes(span, {
                    "stripe.success": False,
                    "stripe.error_type": type(e).__name__
                })
                
                return None
    
    def update_subscription(
        self,
        subscription_id: str,
        new_price_id: str
    ) -> Optional[Any]:
        """
        Update subscription to a new plan.
        
        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New price ID for upgrade/downgrade
            
        Returns:
            Updated subscription or None
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': new_price_id
                }],
                proration_behavior='always_invoice'
            )
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription: {e}")
            return None
    
    # =========================================================================
    # CHECKOUT SESSIONS
    # =========================================================================
    
    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        trial_days: int = 0
    ) -> Optional[Any]:
        """
        Create a Stripe Checkout session.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            trial_days: Trial period in days
            
        Returns:
            Stripe Checkout Session or None
        """
        tracer = get_tracer()
        with tracer.start_as_current_span("stripe.create_checkout_session") as span:
            try:
                set_span_attributes(span, {
                    "stripe.operation": "create_checkout_session",
                    "stripe.customer_id": customer_id[:8] + "...",
                    "stripe.price_id": price_id[:10] + "...",
                    "stripe.trial_days": trial_days
                })
                
                session_data = {
                    'customer': customer_id,
                    'payment_method_types': ['card'],
                    'line_items': [{'price': price_id, 'quantity': 1}],
                    'mode': 'subscription',
                    'success_url': success_url,
                    'cancel_url': cancel_url
                }
                
                if trial_days > 0:
                    session_data['subscription_data'] = {
                        'trial_period_days': trial_days
                    }
                
                session = stripe.checkout.Session.create(**session_data)
                
                set_span_attributes(span, {
                    "stripe.session_id": session.id[:8] + "...",
                    "stripe.success": True
                })
                
                logger.info(f"Created checkout session: {session.id}")
                return session
            except stripe.error.StripeError as e:
                logger.error(f"Failed to create checkout session: {e}")
                span.record_exception(e)
                
                set_span_attributes(span, {
                    "stripe.success": False,
                    "stripe.error_type": type(e).__name__
                })
                
                return None
    
    def create_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> Optional[Any]:
        """
        Create a customer portal session for self-service management.
        
        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal
            
        Returns:
            Stripe Portal Session or None
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            logger.info(f"Created portal session for customer: {customer_id}")
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create portal session: {e}")
            return None
    
    # =========================================================================
    # WEBHOOK HANDLING
    # =========================================================================
    
    def construct_webhook_event(
        self,
        payload: bytes,
        sig_header: str
    ) -> Optional[Any]:
        """
        Construct and verify a webhook event.
        
        Args:
            payload: Raw request body
            sig_header: Stripe-Signature header value
            
        Returns:
            Stripe Event object or None if verification fails
        """
        tracer = get_tracer()
        with tracer.start_as_current_span("stripe.construct_webhook_event") as span:
            set_span_attributes(span, {
                "stripe.operation": "webhook_verification",
                "stripe.payload_size": len(payload),
                "stripe.has_secret": self.webhook_secret is not None
            })
            
            if not self.webhook_secret:
                logger.error("STRIPE_WEBHOOK_SECRET not configured")
                set_span_attributes(span, {
                    "stripe.success": False,
                    "stripe.error": "missing_webhook_secret"
                })
                return None
            
            try:
                event = stripe.Webhook.construct_event(
                    payload,
                    sig_header,
                    self.webhook_secret
                )
                
                set_span_attributes(span, {
                    "stripe.success": True,
                    "stripe.event_type": event.get('type', 'unknown')
                })
                
                return event
            except stripe.error.SignatureVerificationError as e:
                logger.error(f"Webhook signature verification failed: {e}")
                span.record_exception(e)
                
                set_span_attributes(span, {
                    "stripe.success": False,
                    "stripe.error": "signature_verification_failed"
                })
                
                return None
            except Exception as e:
                logger.error(f"Webhook error: {e}")
                span.record_exception(e)
                
                set_span_attributes(span, {
                    "stripe.success": False,
                    "stripe.error_type": type(e).__name__
                })
                
                return None
    
    # =========================================================================
    # INVOICE & PAYMENT
    # =========================================================================
    
    def get_invoices(
        self,
        customer_id: str,
        limit: int = 10
    ) -> list:
        """
        Get invoices for a customer.
        
        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of invoices to return
            
        Returns:
            List of invoices
        """
        try:
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=limit
            )
            return list(invoices.data)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get invoices: {e}")
            return []
    
    def get_upcoming_invoice(self, customer_id: str) -> Optional[Any]:
        """
        Get upcoming invoice for a customer.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Upcoming invoice or None
        """
        try:
            return stripe.Invoice.upcoming(customer=customer_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get upcoming invoice: {e}")
            return None


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

def get_stripe_handler() -> Optional[StripeHandler]:
    """
    Get a configured Stripe handler.
    
    Returns:
        StripeHandler instance or None if Stripe is not configured
    """
    if not STRIPE_AVAILABLE:
        logger.warning("Stripe SDK not available")
        return None
    
    if not os.getenv('STRIPE_SECRET_KEY'):
        logger.warning("STRIPE_SECRET_KEY not configured")
        return None
    
    return StripeHandler()
