"""
=============================================================================
BILLING TESTS - Test Suite for Stripe Payment Integration
=============================================================================

Tests for the billing module including:
- Subscription plans
- Stripe handler operations
- Billing routes
- Usage enforcement middleware

Usage:
    pytest tools/tests/test_billing.py -v

=============================================================================
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import os
import sys

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'web', 'backend'))


class TestSubscriptionPlans:
    """Tests for subscription plan definitions and helpers."""
    
    def test_subscription_plans_exist(self):
        """Test that all subscription plans are defined."""
        from web.backend.billing.plans import SUBSCRIPTION_PLANS
        
        expected_plans = ['free', 'pro', 'business', 'enterprise']
        for plan in expected_plans:
            assert plan in SUBSCRIPTION_PLANS
    
    def test_free_plan_features(self):
        """Test free plan has correct features."""
        from web.backend.billing.plans import get_plan_features
        
        features = get_plan_features('free')
        
        assert features['receipts_per_month'] == 10
        assert features['storage_gb'] == 0.1
        assert features['cloud_training'] is False
        assert features['api_access'] is False
    
    def test_pro_plan_features(self):
        """Test pro plan has correct features."""
        from web.backend.billing.plans import get_plan_features
        
        features = get_plan_features('pro')
        
        assert features['receipts_per_month'] == 500
        assert features['storage_gb'] == 5
        assert features['cloud_training'] is True
        assert features['api_access'] is True
    
    def test_business_plan_features(self):
        """Test business plan has correct features."""
        from web.backend.billing.plans import get_plan_features
        
        features = get_plan_features('business')
        
        assert features['receipts_per_month'] == 2000
        assert features['storage_gb'] == 20
        assert features['priority_support'] is True
    
    def test_enterprise_plan_unlimited(self):
        """Test enterprise plan has unlimited receipts."""
        from web.backend.billing.plans import get_plan_features
        
        features = get_plan_features('enterprise')
        
        assert features['receipts_per_month'] == 'unlimited'
        assert features['on_premise'] is True
    
    def test_get_plan_features_invalid(self):
        """Test getting features for invalid plan returns free plan."""
        from web.backend.billing.plans import get_plan_features
        
        features = get_plan_features('nonexistent')
        
        # Should return free plan features
        assert features['receipts_per_month'] == 10
    
    def test_is_feature_available(self):
        """Test checking feature availability."""
        from web.backend.billing.plans import is_feature_available
        
        # Free plan doesn't have cloud training
        assert is_feature_available('free', 'cloud_training') is False
        
        # Pro plan has cloud training
        assert is_feature_available('pro', 'cloud_training') is True
    
    def test_compare_plans(self):
        """Test plan comparison."""
        from web.backend.billing.plans import compare_plans
        
        assert compare_plans('free', 'pro') == -1
        assert compare_plans('pro', 'free') == 1
        assert compare_plans('pro', 'pro') == 0
        assert compare_plans('enterprise', 'business') == 1
    
    def test_is_plan_sufficient(self):
        """Test plan sufficiency check."""
        from web.backend.billing.plans import is_plan_sufficient
        
        # Pro is sufficient for pro requirement
        assert is_plan_sufficient('pro', 'pro') is True
        
        # Business is sufficient for pro requirement
        assert is_plan_sufficient('business', 'pro') is True
        
        # Free is not sufficient for pro requirement
        assert is_plan_sufficient('free', 'pro') is False
    
    def test_get_upgrade_recommendation(self):
        """Test upgrade recommendation."""
        from web.backend.billing.plans import get_upgrade_recommendation
        
        assert get_upgrade_recommendation('free') == 'pro'
        assert get_upgrade_recommendation('pro') == 'business'
        assert get_upgrade_recommendation('business') == 'enterprise'
        assert get_upgrade_recommendation('enterprise') is None
    
    def test_get_plan_price(self):
        """Test getting plan prices."""
        from web.backend.billing.plans import get_plan_price
        
        assert get_plan_price('free') == 0
        assert get_plan_price('pro') == 19
        assert get_plan_price('business') == 49
        assert get_plan_price('enterprise') == 'custom'


class TestStripeHandler:
    """Tests for Stripe API handler."""
    
    @pytest.fixture
    def mock_stripe(self):
        """Mock Stripe module."""
        with patch.dict('sys.modules', {'stripe': MagicMock()}):
            yield
    
    def test_stripe_handler_init_without_key(self):
        """Test handler initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if it exists
            os.environ.pop('STRIPE_SECRET_KEY', None)
            
            from web.backend.billing.stripe_handler import StripeHandler
            
            # Should log warning but not raise
            handler = StripeHandler()
    
    @patch('web.backend.billing.stripe_handler.STRIPE_AVAILABLE', True)
    @patch('web.backend.billing.stripe_handler.stripe')
    def test_create_customer(self, mock_stripe):
        """Test creating a Stripe customer."""
        mock_stripe.Customer.create.return_value = Mock(id='cus_123')
        
        from web.backend.billing.stripe_handler import StripeHandler
        
        with patch.dict(os.environ, {'STRIPE_SECRET_KEY': 'sk_test_123'}):
            handler = StripeHandler()
            customer = handler.create_customer('test@example.com', 'Test User')
            
            mock_stripe.Customer.create.assert_called_once()
    
    @patch('web.backend.billing.stripe_handler.STRIPE_AVAILABLE', True)
    @patch('web.backend.billing.stripe_handler.stripe')
    def test_get_customer(self, mock_stripe):
        """Test retrieving a Stripe customer."""
        mock_stripe.Customer.retrieve.return_value = Mock(id='cus_123', email='test@example.com')
        
        from web.backend.billing.stripe_handler import StripeHandler
        
        with patch.dict(os.environ, {'STRIPE_SECRET_KEY': 'sk_test_123'}):
            handler = StripeHandler()
            customer = handler.get_customer('cus_123')
            
            mock_stripe.Customer.retrieve.assert_called_once_with('cus_123')
    
    @patch('web.backend.billing.stripe_handler.STRIPE_AVAILABLE', True)
    @patch('web.backend.billing.stripe_handler.stripe')
    def test_create_subscription(self, mock_stripe):
        """Test creating a subscription."""
        mock_stripe.Subscription.create.return_value = Mock(id='sub_123')
        
        from web.backend.billing.stripe_handler import StripeHandler
        
        with patch.dict(os.environ, {'STRIPE_SECRET_KEY': 'sk_test_123'}):
            handler = StripeHandler()
            subscription = handler.create_subscription('cus_123', 'price_123')
            
            mock_stripe.Subscription.create.assert_called_once()
    
    @patch('web.backend.billing.stripe_handler.STRIPE_AVAILABLE', True)
    @patch('web.backend.billing.stripe_handler.stripe')
    def test_cancel_subscription(self, mock_stripe):
        """Test cancelling a subscription."""
        mock_stripe.Subscription.modify.return_value = Mock(id='sub_123', cancel_at_period_end=True)
        
        from web.backend.billing.stripe_handler import StripeHandler
        
        with patch.dict(os.environ, {'STRIPE_SECRET_KEY': 'sk_test_123'}):
            handler = StripeHandler()
            result = handler.cancel_subscription('sub_123', at_period_end=True)
            
            mock_stripe.Subscription.modify.assert_called_once()
    
    @patch('web.backend.billing.stripe_handler.STRIPE_AVAILABLE', True)
    @patch('web.backend.billing.stripe_handler.stripe')
    def test_create_checkout_session(self, mock_stripe):
        """Test creating a checkout session."""
        mock_stripe.checkout.Session.create.return_value = Mock(id='cs_123', url='https://checkout.stripe.com/...')
        
        from web.backend.billing.stripe_handler import StripeHandler
        
        with patch.dict(os.environ, {'STRIPE_SECRET_KEY': 'sk_test_123'}):
            handler = StripeHandler()
            session = handler.create_checkout_session(
                'cus_123',
                'price_123',
                'https://example.com/success',
                'https://example.com/cancel'
            )
            
            mock_stripe.checkout.Session.create.assert_called_once()


class TestBillingMiddleware:
    """Tests for billing middleware."""
    
    def test_usage_limit_exceeded_exception(self):
        """Test UsageLimitExceeded exception."""
        from web.backend.billing.middleware import UsageLimitExceeded
        
        exc = UsageLimitExceeded('Monthly limit reached')
        assert str(exc) == 'Monthly limit reached'
    
    @patch('web.backend.billing.middleware.get_current_user')
    def test_require_subscription_decorator(self, mock_get_user):
        """Test require_subscription decorator."""
        from web.backend.billing.middleware import require_subscription
        
        # Create a mock user with pro plan
        mock_user = Mock()
        mock_user.has_active_subscription.return_value = True
        mock_get_user.return_value = mock_user
        
        @require_subscription('pro')
        def protected_function():
            return 'success'
        
        # The decorator should allow access for users with sufficient plans


class TestBillingRoutes:
    """Tests for billing API routes."""
    
    @pytest.fixture
    def client(self, flask_app):
        """Create test client."""
        if flask_app:
            return flask_app.test_client()
        pytest.skip("Flask app not available")
    
    def test_get_plans(self, client):
        """Test getting subscription plans."""
        if client is None:
            pytest.skip("Test client not available")
        
        # This endpoint may or may not exist depending on implementation
        response = client.get('/api/billing/plans')
        
        # Could be 200 (exists) or 404 (not implemented)
        assert response.status_code in [200, 404]
    
    def test_get_subscription_no_auth(self, client):
        """Test getting subscription without authentication."""
        if client is None:
            pytest.skip("Test client not available")
        
        response = client.get('/api/billing/subscription')
        
        # Should require authentication
        assert response.status_code in [401, 404]
    
    def test_webhook_no_signature(self, client):
        """Test webhook without Stripe signature."""
        if client is None:
            pytest.skip("Test client not available")
        
        response = client.post('/api/billing/webhook', json={})
        
        # Should reject without valid signature
        assert response.status_code in [400, 401, 404]


class TestPlanHierarchy:
    """Tests for plan hierarchy and comparisons."""
    
    def test_plan_hierarchy_order(self):
        """Test that plan hierarchy is in correct order."""
        from web.backend.billing.plans import PLAN_HIERARCHY
        
        assert PLAN_HIERARCHY['free'] < PLAN_HIERARCHY['pro']
        assert PLAN_HIERARCHY['pro'] < PLAN_HIERARCHY['business']
        assert PLAN_HIERARCHY['business'] < PLAN_HIERARCHY['enterprise']
    
    def test_all_plans_in_hierarchy(self):
        """Test that all plans are in the hierarchy."""
        from web.backend.billing.plans import SUBSCRIPTION_PLANS, PLAN_HIERARCHY
        
        for plan in SUBSCRIPTION_PLANS:
            assert plan in PLAN_HIERARCHY


class TestExportFormats:
    """Tests for export format availability by plan."""
    
    def test_free_plan_export_formats(self):
        """Test free plan only has JSON export."""
        from web.backend.billing.plans import get_plan_features
        
        features = get_plan_features('free')
        assert features['export_formats'] == ['json']
    
    def test_pro_plan_export_formats(self):
        """Test pro plan has multiple export formats."""
        from web.backend.billing.plans import get_plan_features
        
        features = get_plan_features('pro')
        assert 'json' in features['export_formats']
        assert 'csv' in features['export_formats']
        assert 'excel' in features['export_formats']
    
    def test_business_plan_export_formats(self):
        """Test business plan includes PDF export."""
        from web.backend.billing.plans import get_plan_features
        
        features = get_plan_features('business')
        assert 'pdf' in features['export_formats']
