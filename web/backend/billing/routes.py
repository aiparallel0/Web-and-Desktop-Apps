"""
=============================================================================
BILLING ROUTES - Stripe Payment API Endpoints
=============================================================================

Provides API endpoints for subscription management:
- Create checkout sessions
- Handle webhooks
- Manage subscriptions
- Get billing information

=============================================================================
"""

import os
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, g

from .plans import SUBSCRIPTION_PLANS, get_plan_features
from .stripe_handler import StripeHandler, STRIPE_AVAILABLE

logger = logging.getLogger(__name__)

# Create Blueprint
billing_bp = Blueprint('billing', __name__, url_prefix='/api/billing')

# Lazy database imports
_db_context = None
_User = None
_Subscription = None


def _get_db_context():
    """Lazy import of database context."""
    global _db_context
    if _db_context is None:
        from database import get_db_context
        _db_context = get_db_context
    return _db_context


def _get_models():
    """Lazy import of database models."""
    global _User, _Subscription
    if _User is None:
        from database import User, Subscription
        _User = User
        _Subscription = Subscription
    return _User, _Subscription


def require_auth_billing(f):
    """Simple auth check decorator for billing routes."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from web.backend.auth import verify_access_token
        
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Missing authorization header'}), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'success': False, 'error': 'Invalid authorization header format'}), 401
        
        token = parts[1]
        payload = verify_access_token(token)
        if not payload:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        g.user_id = payload.get('user_id')
        g.user_email = payload.get('email')
        
        return f(*args, **kwargs)
    
    return decorated_function


# =============================================================================
# PLAN INFORMATION
# =============================================================================

@billing_bp.route('/plans', methods=['GET'])
def get_plans():
    """
    Get all available subscription plans.
    
    Returns:
        200: List of plans with features
    """
    plans = []
    for plan_id, plan_data in SUBSCRIPTION_PLANS.items():
        plans.append({
            'id': plan_id,
            'name': plan_data['name'],
            'price': plan_data['price'],
            'description': plan_data.get('description', ''),
            'features': plan_data['features']
        })
    
    return jsonify({
        'success': True,
        'plans': plans
    })


@billing_bp.route('/subscription', methods=['GET'])
@require_auth_billing
def get_subscription():
    """
    Get current user's subscription details.
    
    Returns:
        200: Subscription details
        404: No subscription found
    """
    try:
        User, Subscription = _get_models()
        
        with _get_db_context()() as db:
            user = db.query(User).filter(User.id == g.user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            # Get active subscription
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.status == 'active'
            ).first()
            
            plan_name = user.plan.value if hasattr(user.plan, 'value') else str(user.plan)
            plan_features = get_plan_features(plan_name)
            
            return jsonify({
                'success': True,
                'subscription': {
                    'plan': plan_name,
                    'features': plan_features,
                    'stripe_subscription_id': subscription.stripe_subscription_id if subscription else None,
                    'current_period_end': subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None,
                    'cancel_at_period_end': subscription.cancel_at_period_end if subscription else False
                },
                'usage': {
                    'receipts_processed_month': user.receipts_processed_month,
                    'receipts_limit': plan_features.get('receipts_per_month', 10),
                    'storage_used_bytes': user.storage_used_bytes,
                    'storage_limit_gb': plan_features.get('storage_gb', 0.1)
                }
            })
    except Exception as e:
        logger.error(f"Get subscription error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to get subscription'}), 500


@billing_bp.route('/usage', methods=['GET'])
@require_auth_billing
def get_usage():
    """
    Get current user's usage statistics.
    
    Returns:
        200: Usage statistics
    """
    try:
        User, _ = _get_models()
        
        with _get_db_context()() as db:
            user = db.query(User).filter(User.id == g.user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            plan_name = user.plan.value if hasattr(user.plan, 'value') else str(user.plan)
            plan_features = get_plan_features(plan_name)
            
            receipts_limit = plan_features.get('receipts_per_month', 10)
            if receipts_limit == 'unlimited':
                receipts_percent = 0
            else:
                receipts_percent = min(100, (user.receipts_processed_month / receipts_limit) * 100)
            
            storage_limit_bytes = plan_features.get('storage_gb', 0.1) * 1024 * 1024 * 1024
            storage_percent = min(100, (user.storage_used_bytes / storage_limit_bytes) * 100)
            
            return jsonify({
                'success': True,
                'usage': {
                    'receipts': {
                        'used': user.receipts_processed_month,
                        'limit': receipts_limit,
                        'percent': round(receipts_percent, 1)
                    },
                    'storage': {
                        'used_bytes': user.storage_used_bytes,
                        'used_gb': round(user.storage_used_bytes / (1024 ** 3), 2),
                        'limit_gb': plan_features.get('storage_gb', 0.1),
                        'percent': round(storage_percent, 1)
                    }
                },
                'plan': plan_name
            })
    except Exception as e:
        logger.error(f"Get usage error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to get usage'}), 500


# =============================================================================
# CHECKOUT & PAYMENT
# =============================================================================

@billing_bp.route('/create-checkout', methods=['POST'])
@require_auth_billing
def create_checkout():
    """
    Create a Stripe Checkout session for subscription.
    
    Request body:
        {
            "plan": "pro" or "business",
            "success_url": "https://...",
            "cancel_url": "https://..."
        }
    
    Returns:
        200: Checkout session URL
        400: Invalid plan or Stripe not configured
    """
    if not STRIPE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Stripe is not configured. Please contact support.'
        }), 400
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request body required'}), 400
        
        plan_id = data.get('plan')
        success_url = data.get('success_url', f"{request.host_url}billing/success")
        cancel_url = data.get('cancel_url', f"{request.host_url}billing/cancel")
        
        if plan_id not in SUBSCRIPTION_PLANS:
            return jsonify({'success': False, 'error': 'Invalid plan'}), 400
        
        plan = SUBSCRIPTION_PLANS[plan_id]
        if not plan.get('price_id'):
            return jsonify({
                'success': False,
                'error': f'Plan {plan_id} is not available for self-service. Contact sales.'
            }), 400
        
        User, _ = _get_models()
        handler = StripeHandler()
        
        with _get_db_context()() as db:
            user = db.query(User).filter(User.id == g.user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            # Create or get Stripe customer
            if not user.stripe_customer_id:
                customer = handler.create_customer(user.email, user.full_name)
                if customer:
                    user.stripe_customer_id = customer.id
                    db.commit()
                else:
                    return jsonify({'success': False, 'error': 'Failed to create customer'}), 500
            
            # Create checkout session
            session = handler.create_checkout_session(
                customer_id=user.stripe_customer_id,
                price_id=plan['price_id'],
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            if session:
                return jsonify({
                    'success': True,
                    'checkout_url': session.url,
                    'session_id': session.id
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to create checkout session'}), 500
                
    except Exception as e:
        logger.error(f"Create checkout error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to create checkout'}), 500


@billing_bp.route('/create-portal', methods=['POST'])
@require_auth_billing
def create_portal():
    """
    Create a customer portal session for self-service management.
    
    Request body:
        {
            "return_url": "https://..."
        }
    
    Returns:
        200: Portal session URL
    """
    if not STRIPE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Stripe is not configured'
        }), 400
    
    try:
        data = request.get_json() or {}
        return_url = data.get('return_url', f"{request.host_url}billing")
        
        User, _ = _get_models()
        handler = StripeHandler()
        
        with _get_db_context()() as db:
            user = db.query(User).filter(User.id == g.user_id).first()
            if not user or not user.stripe_customer_id:
                return jsonify({
                    'success': False,
                    'error': 'No billing account found. Please subscribe first.'
                }), 404
            
            session = handler.create_portal_session(
                customer_id=user.stripe_customer_id,
                return_url=return_url
            )
            
            if session:
                return jsonify({
                    'success': True,
                    'portal_url': session.url
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to create portal session'}), 500
                
    except Exception as e:
        logger.error(f"Create portal error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to create portal'}), 500


@billing_bp.route('/cancel', methods=['POST'])
@require_auth_billing
def cancel_subscription():
    """
    Cancel subscription at end of billing period.
    
    Returns:
        200: Subscription cancelled
        404: No subscription found
    """
    if not STRIPE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Stripe is not configured'
        }), 400
    
    try:
        User, Subscription = _get_models()
        handler = StripeHandler()
        
        with _get_db_context()() as db:
            user = db.query(User).filter(User.id == g.user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.status == 'active'
            ).first()
            
            if not subscription:
                return jsonify({'success': False, 'error': 'No active subscription'}), 404
            
            result = handler.cancel_subscription(
                subscription.stripe_subscription_id,
                at_period_end=True
            )
            
            if result:
                subscription.cancel_at_period_end = True
                db.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Subscription will be cancelled at end of billing period',
                    'cancel_at': subscription.current_period_end.isoformat() if subscription.current_period_end else None
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to cancel subscription'}), 500
                
    except Exception as e:
        logger.error(f"Cancel subscription error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to cancel subscription'}), 500


# =============================================================================
# WEBHOOK HANDLING
# =============================================================================

@billing_bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle Stripe webhook events.
    
    Events handled:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    """
    if not STRIPE_AVAILABLE:
        return jsonify({'error': 'Stripe not configured'}), 400
    
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    if not sig_header:
        return jsonify({'error': 'Missing signature'}), 400
    
    try:
        handler = StripeHandler()
        event = handler.construct_webhook_event(payload, sig_header)
        
        if not event:
            return jsonify({'error': 'Invalid signature'}), 400
        
        event_type = event['type']
        logger.info(f"Processing webhook event: {event_type}")
        
        User, Subscription = _get_models()
        
        with _get_db_context()() as db:
            if event_type == 'customer.subscription.created':
                _handle_subscription_created(db, event['data']['object'], User, Subscription)
            
            elif event_type == 'customer.subscription.updated':
                _handle_subscription_updated(db, event['data']['object'], User, Subscription)
            
            elif event_type == 'customer.subscription.deleted':
                _handle_subscription_deleted(db, event['data']['object'], User, Subscription)
            
            elif event_type == 'invoice.payment_succeeded':
                _handle_payment_succeeded(db, event['data']['object'], User)
            
            elif event_type == 'invoice.payment_failed':
                _handle_payment_failed(db, event['data']['object'], User, Subscription)
            
            db.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def _handle_subscription_created(db, subscription_data, User, Subscription):
    """Handle new subscription creation."""
    customer_id = subscription_data['customer']
    
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.warning(f"User not found for customer: {customer_id}")
        return
    
    # Determine plan from price ID
    price_id = subscription_data['items']['data'][0]['price']['id']
    plan_name = _get_plan_from_price_id(price_id)
    
    import uuid
    from database import SubscriptionStatus, SubscriptionPlan
    
    new_sub = Subscription(
        id=uuid.uuid4(),
        user_id=user.id,
        stripe_subscription_id=subscription_data['id'],
        stripe_price_id=price_id,
        plan=SubscriptionPlan(plan_name),
        status=SubscriptionStatus(subscription_data['status']),
        current_period_start=datetime.fromtimestamp(subscription_data['current_period_start']),
        current_period_end=datetime.fromtimestamp(subscription_data['current_period_end'])
    )
    db.add(new_sub)
    
    # Update user's plan
    user.plan = SubscriptionPlan(plan_name)
    
    logger.info(f"Subscription created for user {user.id}: {plan_name}")


def _handle_subscription_updated(db, subscription_data, User, Subscription):
    """Handle subscription update."""
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_data['id']
    ).first()
    
    if not subscription:
        logger.warning(f"Subscription not found: {subscription_data['id']}")
        return
    
    from database import SubscriptionStatus
    
    subscription.status = SubscriptionStatus(subscription_data['status'])
    subscription.current_period_start = datetime.fromtimestamp(subscription_data['current_period_start'])
    subscription.current_period_end = datetime.fromtimestamp(subscription_data['current_period_end'])
    subscription.cancel_at_period_end = subscription_data.get('cancel_at_period_end', False)
    
    logger.info(f"Subscription updated: {subscription_data['id']}")


def _handle_subscription_deleted(db, subscription_data, User, Subscription):
    """Handle subscription deletion."""
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_data['id']
    ).first()
    
    if not subscription:
        return
    
    from database import SubscriptionStatus, SubscriptionPlan
    
    subscription.status = SubscriptionStatus.CANCELED
    subscription.canceled_at = datetime.utcnow()
    
    # Downgrade user to free plan
    user = db.query(User).filter(User.id == subscription.user_id).first()
    if user:
        user.plan = SubscriptionPlan.FREE
    
    logger.info(f"Subscription deleted: {subscription_data['id']}")


def _handle_payment_succeeded(db, invoice_data, User):
    """Handle successful payment."""
    customer_id = invoice_data['customer']
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user:
        logger.info(f"Payment succeeded for user {user.id}")


def _handle_payment_failed(db, invoice_data, User, Subscription):
    """Handle failed payment."""
    customer_id = invoice_data['customer']
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user:
        logger.warning(f"Payment failed for user {user.id}")
        
        # Mark subscription as past_due
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == 'active'
        ).first()
        
        if subscription:
            from database import SubscriptionStatus
            subscription.status = SubscriptionStatus.PAST_DUE


def _get_plan_from_price_id(price_id: str) -> str:
    """Get plan name from Stripe price ID."""
    for plan_name, plan_data in SUBSCRIPTION_PLANS.items():
        if plan_data.get('price_id') == price_id:
            return plan_name
    return 'free'


def register_billing_routes(app):
    """Register billing blueprint with the Flask app."""
    app.register_blueprint(billing_bp)
    logger.info("Billing routes registered")
