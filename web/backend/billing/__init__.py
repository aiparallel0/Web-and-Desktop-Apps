"""
=============================================================================
BILLING MODULE - Stripe Payment Integration
=============================================================================

This module provides Stripe subscription billing integration for the
Receipt Extractor SaaS platform.

Components:
- plans.py: Subscription plan definitions
- stripe_handler.py: Stripe API operations
- routes.py: Billing API endpoints
- middleware.py: Usage enforcement middleware

Environment Variables Required:
- STRIPE_SECRET_KEY: Stripe secret API key
- STRIPE_PUBLISHABLE_KEY: Stripe publishable key
- STRIPE_WEBHOOK_SECRET: Webhook signing secret

=============================================================================
"""

from .plans import SUBSCRIPTION_PLANS, get_plan_features, is_feature_available
from .stripe_handler import StripeHandler
from .routes import billing_bp, register_billing_routes
from .middleware import require_subscription, check_usage_limits, UsageLimitExceeded

__all__ = [
    # Plans
    'SUBSCRIPTION_PLANS',
    'get_plan_features',
    'is_feature_available',
    # Handler
    'StripeHandler',
    # Routes
    'billing_bp',
    'register_billing_routes',
    # Middleware
    'require_subscription',
    'check_usage_limits',
    'UsageLimitExceeded',
]
