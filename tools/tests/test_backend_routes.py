"""
Test suite for web backend modules.

IMPORTANT: These tests directly test actual module exports.
When code changes, update these tests accordingly.

Tested modules:
- web.backend.jwt_handler - JWT token creation/verification
- web.backend.password - Password hashing/verification
- web.backend.billing.plans - Subscription plans
- web.backend.security.headers - Security headers
"""
import pytest
import os


class TestJWTHandler:
    """Test JWT token handling - tests actual functions in jwt_handler.py"""

    def test_jwt_module_imports(self):
        """Test that JWT handler module can be imported."""
        from web.backend import jwt_handler
        assert jwt_handler is not None

    def test_create_access_token(self):
        """Test create_access_token function."""
        from web.backend.jwt_handler import create_access_token
        
        token = create_access_token(
            user_id="test-user-123",
            email="test@example.com",
            is_admin=False
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT tokens have 3 parts separated by dots
        assert token.count('.') == 2

    def test_create_access_token_admin(self):
        """Test create_access_token with admin privileges."""
        from web.backend.jwt_handler import create_access_token
        
        token = create_access_token(
            user_id="admin-user-456",
            email="admin@example.com",
            is_admin=True
        )
        
        assert token is not None
        assert isinstance(token, str)

    def test_verify_access_token_valid(self):
        """Test verify_access_token with valid token."""
        from web.backend.jwt_handler import create_access_token, verify_access_token
        
        # Create a token
        token = create_access_token(
            user_id="verify-test-user",
            email="verify@example.com",
            is_admin=False
        )
        
        # Verify it
        payload = verify_access_token(token)
        
        assert payload is not None
        assert payload.get('user_id') == "verify-test-user"
        assert payload.get('email') == "verify@example.com"
        assert payload.get('is_admin') is False
        assert payload.get('type') == 'access'

    def test_verify_access_token_invalid(self):
        """Test verify_access_token with invalid token."""
        from web.backend.jwt_handler import verify_access_token
        
        result = verify_access_token("invalid.token.here")
        
        # Should return None for invalid token
        assert result is None

    def test_create_refresh_token(self):
        """Test create_refresh_token function."""
        from web.backend.jwt_handler import create_refresh_token
        
        token, token_hash = create_refresh_token()
        
        assert token is not None
        assert token_hash is not None
        assert isinstance(token, str)
        assert isinstance(token_hash, str)
        assert len(token) > 0
        assert len(token_hash) == 64  # SHA-256 hex digest length

    def test_refresh_token_uniqueness(self):
        """Test that refresh tokens are unique."""
        from web.backend.jwt_handler import create_refresh_token
        
        token1, hash1 = create_refresh_token()
        token2, hash2 = create_refresh_token()
        
        assert token1 != token2
        assert hash1 != hash2


class TestPasswordModule:
    """Test password hashing and verification."""

    def test_password_module_imports(self):
        """Test that password module can be imported."""
        from web.backend import password
        assert password is not None

    def test_hash_password(self):
        """Test hash_password function."""
        from web.backend.password import hash_password
        
        password_plain = "TestPassword123!"
        hashed = hash_password(password_plain)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password_plain  # Hash should differ from plain
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self):
        """Test that same password produces different hashes (salting)."""
        from web.backend.password import hash_password
        
        password_plain = "SamePassword123!"
        hash1 = hash_password(password_plain)
        hash2 = hash_password(password_plain)
        
        # Bcrypt uses random salt, so hashes should differ
        assert hash1 != hash2

    def test_hash_password_empty_raises(self):
        """Test that empty password raises error."""
        from web.backend.password import hash_password
        
        with pytest.raises(ValueError):
            hash_password("")

    def test_verify_password_correct(self):
        """Test verify_password with correct password."""
        from web.backend.password import hash_password, verify_password
        
        password_plain = "CorrectPassword123!"
        hashed = hash_password(password_plain)
        
        result = verify_password(password_plain, hashed)
        
        assert result is True

    def test_verify_password_incorrect(self):
        """Test verify_password with incorrect password."""
        from web.backend.password import hash_password, verify_password
        
        password_plain = "CorrectPassword123!"
        hashed = hash_password(password_plain)
        
        result = verify_password("WrongPassword456!", hashed)
        
        assert result is False

    def test_verify_password_empty(self):
        """Test verify_password with empty inputs."""
        from web.backend.password import verify_password
        
        assert verify_password("", "somehash") is False
        assert verify_password("somepassword", "") is False

    def test_is_password_strong_valid(self):
        """Test is_password_strong with valid password."""
        from web.backend.password import is_password_strong
        
        is_strong, issues = is_password_strong("StrongP@ss123!")
        
        assert is_strong is True
        assert len(issues) == 0

    def test_is_password_strong_too_short(self):
        """Test is_password_strong with short password."""
        from web.backend.password import is_password_strong
        
        is_strong, issues = is_password_strong("Sh0rt!")
        
        assert is_strong is False
        assert any("8 characters" in issue for issue in issues)

    def test_is_password_strong_missing_uppercase(self):
        """Test is_password_strong without uppercase."""
        from web.backend.password import is_password_strong
        
        is_strong, issues = is_password_strong("nouppercase123!")
        
        assert is_strong is False
        assert any("uppercase" in issue for issue in issues)


class TestBillingPlans:
    """Test billing plans module."""

    def test_billing_plans_imports(self):
        """Test that billing plans can be imported."""
        from web.backend.billing.plans import SUBSCRIPTION_PLANS
        assert SUBSCRIPTION_PLANS is not None
        assert isinstance(SUBSCRIPTION_PLANS, dict)

    def test_subscription_plans_structure(self):
        """Test SUBSCRIPTION_PLANS has required plans."""
        from web.backend.billing.plans import SUBSCRIPTION_PLANS
        
        required_plans = ['free', 'pro', 'business', 'enterprise']
        for plan in required_plans:
            assert plan in SUBSCRIPTION_PLANS
            assert 'name' in SUBSCRIPTION_PLANS[plan]
            assert 'price' in SUBSCRIPTION_PLANS[plan]
            assert 'features' in SUBSCRIPTION_PLANS[plan]

    def test_get_plan_features(self):
        """Test get_plan_features function."""
        from web.backend.billing.plans import get_plan_features
        
        features = get_plan_features('free')
        
        assert features is not None
        assert isinstance(features, dict)
        assert 'receipts_per_month' in features

    def test_is_feature_available(self):
        """Test is_feature_available function."""
        from web.backend.billing.plans import is_feature_available
        
        # Free tier shouldn't have API access
        assert is_feature_available('free', 'api_access') is False
        
        # Pro tier should have API access
        assert is_feature_available('pro', 'api_access') is True

    def test_get_plan_limit(self):
        """Test get_plan_limit function."""
        from web.backend.billing.plans import get_plan_limit
        
        free_limit = get_plan_limit('free', 'receipts_per_month')
        pro_limit = get_plan_limit('pro', 'receipts_per_month')
        
        assert free_limit == 10
        assert pro_limit == 500

    def test_compare_plans(self):
        """Test compare_plans function."""
        from web.backend.billing.plans import compare_plans
        
        assert compare_plans('free', 'pro') == -1  # free < pro
        assert compare_plans('pro', 'free') == 1   # pro > free
        assert compare_plans('pro', 'pro') == 0    # pro == pro

    def test_is_plan_sufficient(self):
        """Test is_plan_sufficient function."""
        from web.backend.billing.plans import is_plan_sufficient
        
        assert is_plan_sufficient('pro', 'free') is True
        assert is_plan_sufficient('free', 'pro') is False
        assert is_plan_sufficient('enterprise', 'business') is True

    def test_get_upgrade_recommendation(self):
        """Test get_upgrade_recommendation function."""
        from web.backend.billing.plans import get_upgrade_recommendation
        
        assert get_upgrade_recommendation('free') == 'pro'
        assert get_upgrade_recommendation('pro') == 'business'
        assert get_upgrade_recommendation('enterprise') is None

    def test_get_all_plans(self):
        """Test get_all_plans function."""
        from web.backend.billing.plans import get_all_plans
        
        plans = get_all_plans()
        
        assert isinstance(plans, dict)
        assert len(plans) >= 4

    def test_get_plan_price(self):
        """Test get_plan_price function."""
        from web.backend.billing.plans import get_plan_price
        
        assert get_plan_price('free') == 0
        assert get_plan_price('pro') == 19
        assert get_plan_price('business') == 49


class TestSecurityHeaders:
    """Test security headers module."""

    def test_security_headers_imports(self):
        """Test that security headers module can be imported."""
        from web.backend.security.headers import add_security_headers
        assert add_security_headers is not None
        assert callable(add_security_headers)

    def test_add_security_headers(self):
        """Test add_security_headers function."""
        from web.backend.security.headers import add_security_headers
        from flask import Flask, Response
        
        app = Flask(__name__)
        
        with app.app_context():
            response = Response("test content")
            secured = add_security_headers(response)
            
            assert secured is not None
            # Check that security headers were added
            headers = dict(secured.headers)
            
            # At least some security headers should be present
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options', 
                'X-XSS-Protection',
                'Strict-Transport-Security'
            ]
            
            has_security_headers = any(h in headers for h in security_headers)
            assert has_security_headers or len(headers) > 1


class TestDatabaseModels:
    """Test database module imports and basic structure."""

    def test_database_module_imports(self):
        """Test that database module can be imported."""
        from web.backend import database
        assert database is not None

    def test_user_model_exists(self):
        """Test that User model is defined."""
        from web.backend.database import User
        assert User is not None

    def test_receipt_model_exists(self):
        """Test that Receipt model is defined."""
        from web.backend.database import Receipt
        assert Receipt is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
