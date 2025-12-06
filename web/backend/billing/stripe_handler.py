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
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            logger.info(f"Created Stripe customer: {customer.id}")
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create customer: {e}")
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
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)
            
            logger.info(f"Cancelled subscription: {subscription_id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
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
        try:
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
            logger.info(f"Created checkout session: {session.id}")
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
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
        if not self.webhook_secret:
            logger.error("STRIPE_WEBHOOK_SECRET not configured")
            return None
        
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                self.webhook_secret
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Webhook error: {e}")
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
