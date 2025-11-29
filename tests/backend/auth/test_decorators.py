"""
Test suite for authentication and authorization decorators
Tests coverage for web-app/backend/auth/decorators.py
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from flask import Flask, g, jsonify

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'web-app', 'backend'))

from auth.decorators import (
    require_auth,
    require_admin,
    rate_limit,
    require_plan,
    check_usage_limit,
    _rate_limit_storage
)


@pytest.fixture
def app():
    """Create Flask app for testing decorators"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = Mock()
    return session


class TestRequireAuthDecorator:
    """Test the require_auth decorator"""

    def test_require_auth_valid_token(self, app, db_session, test_user):
        """Test that valid token grants access"""
        from auth.jwt_handler import create_access_token

        token = create_access_token(str(test_user.id), test_user.email, test_user.is_admin)

        @app.route('/test')
        @require_auth
        def test_route():
            return jsonify({'message': 'success', 'user_id': g.user_id})

        with app.test_client() as client:
            with patch('auth.decorators.get_db_context') as mock_get_db:
                # Setup mock to return our test session
                mock_get_db.return_value.__enter__.return_value = db_session

                response = client.get('/test', headers={
                    'Authorization': f'Bearer {token}'
                })

                assert response.status_code == 200
                data = response.get_json()
                assert data['message'] == 'success'
                assert data['user_id'] == str(test_user.id)

    def test_require_auth_missing_header(self, app):
        """Test that missing authorization header returns 401"""
        @app.route('/test')
        @require_auth
        def test_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            response = client.get('/test')

            assert response.status_code == 401
            data = response.get_json()
            assert 'error' in data
            assert 'Missing authorization header' in data['error']

    def test_require_auth_invalid_header_format(self, app):
        """Test that invalid header format returns 401"""
        @app.route('/test')
        @require_auth
        def test_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            # Test various invalid formats
            invalid_headers = [
                {'Authorization': 'InvalidFormat'},
                {'Authorization': 'Bearer'},
                {'Authorization': 'NotBearer token'},
                {'Authorization': ''},
            ]

            for headers in invalid_headers:
                response = client.get('/test', headers=headers)
                assert response.status_code == 401

    def test_require_auth_expired_token(self, app, db_session, test_user):
        """Test that expired token is rejected"""
        from auth.jwt_handler import JWT_SECRET, JWT_ALGORITHM
        import jwt

        # Create an expired token
        payload = {
            'user_id': str(test_user.id),
            'email': test_user.email,
            'is_admin': False,
            'type': 'access',
            'exp': datetime.utcnow() - timedelta(minutes=1)  # Expired
        }
        expired_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        @app.route('/test')
        @require_auth
        def test_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            response = client.get('/test', headers={
                'Authorization': f'Bearer {expired_token}'
            })

            assert response.status_code == 401
            data = response.get_json()
            assert 'error' in data

    def test_require_auth_user_not_found(self, app, db_session):
        """Test that token for non-existent user is rejected"""
        from auth.jwt_handler import create_access_token
        import uuid

        # Create token for non-existent user
        fake_user_id = str(uuid.uuid4())
        token = create_access_token(fake_user_id, "fake@example.com", False)

        @app.route('/test')
        @require_auth
        def test_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with patch('auth.decorators.get_db_context') as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = db_session

                response = client.get('/test', headers={
                    'Authorization': f'Bearer {token}'
                })

                assert response.status_code == 401
                data = response.get_json()
                assert 'User not found' in data['error']

    def test_require_auth_inactive_user(self, app, db_session, test_user):
        """Test that inactive user is rejected"""
        from auth.jwt_handler import create_access_token

        # Make user inactive
        test_user.is_active = False
        db_session.commit()

        token = create_access_token(str(test_user.id), test_user.email, False)

        @app.route('/test')
        @require_auth
        def test_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with patch('auth.decorators.get_db_context') as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = db_session

                response = client.get('/test', headers={
                    'Authorization': f'Bearer {token}'
                })

                assert response.status_code == 401
                data = response.get_json()
                assert 'disabled' in data['error']

    def test_require_auth_sets_flask_g_attributes(self, app, db_session, test_user):
        """Test that decorator sets user info in Flask g object"""
        from auth.jwt_handler import create_access_token

        token = create_access_token(str(test_user.id), test_user.email, test_user.is_admin)

        @app.route('/test')
        @require_auth
        def test_route():
            # Access g attributes set by decorator
            return jsonify({
                'user_id': g.user_id,
                'user_email': g.user_email,
                'is_admin': g.is_admin,
                'user_plan': g.user_plan.value
            })

        with app.test_client() as client:
            with patch('auth.decorators.get_db_context') as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = db_session

                response = client.get('/test', headers={
                    'Authorization': f'Bearer {token}'
                })

                assert response.status_code == 200
                data = response.get_json()
                assert data['user_id'] == str(test_user.id)
                assert data['user_email'] == test_user.email
                assert data['is_admin'] == test_user.is_admin


class TestRequireAdminDecorator:
    """Test the require_admin decorator"""

    def test_require_admin_with_admin_user(self, app):
        """Test that admin user can access admin route"""
        @app.route('/admin')
        @require_admin
        def admin_route():
            return jsonify({'message': 'admin access granted'})

        with app.test_client() as client:
            with app.test_request_context('/admin'):
                g.is_admin = True

                response = admin_route()
                assert 'admin access granted' in str(response.get_data())

    def test_require_admin_with_regular_user(self, app):
        """Test that regular user is denied access to admin route"""
        @app.route('/admin')
        @require_admin
        def admin_route():
            return jsonify({'message': 'admin access granted'})

        with app.test_client() as client:
            with app.test_request_context('/admin'):
                g.is_admin = False

                response = admin_route()
                # Should return tuple (response, status_code)
                assert response[1] == 403

    def test_require_admin_without_authentication(self, app):
        """Test that unauthenticated request is denied"""
        @app.route('/admin')
        @require_admin
        def admin_route():
            return jsonify({'message': 'admin access granted'})

        with app.test_client() as client:
            with app.test_request_context('/admin'):
                # No g.is_admin set

                response = admin_route()
                assert response[1] == 403


class TestRateLimitDecorator:
    """Test the rate_limit decorator"""

    def setup_method(self):
        """Clear rate limit storage before each test"""
        _rate_limit_storage.clear()

    def test_rate_limit_within_limit(self, app):
        """Test that requests within limit are allowed"""
        @app.route('/limited')
        @rate_limit(max_requests=5, window_seconds=60)
        def limited_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/limited'):
                g.user_id = 'test-user'

                # Make 5 requests (within limit)
                for i in range(5):
                    response = limited_route()
                    # First element of tuple should not be an error response
                    if isinstance(response, tuple):
                        assert response[1] != 429
                    else:
                        # Single response object means success
                        assert True

    def test_rate_limit_exceeds_limit(self, app):
        """Test that requests exceeding limit are blocked"""
        @app.route('/limited')
        @rate_limit(max_requests=3, window_seconds=60)
        def limited_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/limited'):
                g.user_id = 'test-user'

                # Make 3 requests (at limit)
                for i in range(3):
                    limited_route()

                # 4th request should be rate limited
                response = limited_route()
                assert response[1] == 429
                data = response[0].get_json()
                assert 'Rate limit exceeded' in data['error']

    def test_rate_limit_window_expiry(self, app):
        """Test that rate limit resets after window expires"""
        @app.route('/limited')
        @rate_limit(max_requests=2, window_seconds=1)
        def limited_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/limited'):
                g.user_id = 'test-user'

                # Make 2 requests
                limited_route()
                limited_route()

                # 3rd should be limited
                response = limited_route()
                assert response[1] == 429

                # Wait for window to expire
                import time
                time.sleep(1.1)

                # Should work again
                response = limited_route()
                # Should not be 429
                if isinstance(response, tuple):
                    assert response[1] != 429

    def test_rate_limit_different_users_separate_limits(self, app):
        """Test that different users have separate rate limits"""
        @app.route('/limited')
        @rate_limit(max_requests=2, window_seconds=60)
        def limited_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            # User 1 makes 2 requests
            with app.test_request_context('/limited'):
                g.user_id = 'user-1'
                limited_route()
                limited_route()

            # User 2 should still be able to make requests
            with app.test_request_context('/limited'):
                g.user_id = 'user-2'
                response = limited_route()
                # Should not be rate limited
                if isinstance(response, tuple):
                    assert response[1] != 429

    def test_rate_limit_uses_ip_when_no_user_id(self, app):
        """Test that rate limit falls back to IP address"""
        @app.route('/limited')
        @rate_limit(max_requests=2, window_seconds=60)
        def limited_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/limited', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
                # No g.user_id set
                response = limited_route()
                # Should work
                assert response is not None


class TestRequirePlanDecorator:
    """Test the require_plan decorator"""

    def test_require_plan_free_user_free_feature(self, app):
        """Test that free user can access free features"""
        from database.models import SubscriptionPlan

        @app.route('/free-feature')
        @require_plan('free')
        def free_feature():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/free-feature'):
                g.user_plan = SubscriptionPlan.FREE

                response = free_feature()
                assert 'success' in str(response.get_data())

    def test_require_plan_free_user_pro_feature(self, app):
        """Test that free user cannot access pro features"""
        from database.models import SubscriptionPlan

        @app.route('/pro-feature')
        @require_plan('pro')
        def pro_feature():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/pro-feature'):
                g.user_plan = SubscriptionPlan.FREE

                response = pro_feature()
                assert response[1] == 403
                data = response[0].get_json()
                assert 'requires pro plan' in data['error']

    def test_require_plan_pro_user_pro_feature(self, app):
        """Test that pro user can access pro features"""
        from database.models import SubscriptionPlan

        @app.route('/pro-feature')
        @require_plan('pro')
        def pro_feature():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/pro-feature'):
                g.user_plan = SubscriptionPlan.PRO

                response = pro_feature()
                assert 'success' in str(response.get_data())

    def test_require_plan_enterprise_user_any_feature(self, app):
        """Test that enterprise user can access any feature"""
        from database.models import SubscriptionPlan

        @app.route('/pro-feature')
        @require_plan('pro')
        def pro_feature():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/pro-feature'):
                g.user_plan = SubscriptionPlan.ENTERPRISE

                response = pro_feature()
                assert 'success' in str(response.get_data())

    def test_require_plan_hierarchy(self, app):
        """Test that plan hierarchy works correctly"""
        from database.models import SubscriptionPlan

        @app.route('/business-feature')
        @require_plan('business')
        def business_feature():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            # Free user should be blocked
            with app.test_request_context('/business-feature'):
                g.user_plan = SubscriptionPlan.FREE
                response = business_feature()
                assert response[1] == 403

            # Pro user should be blocked
            with app.test_request_context('/business-feature'):
                g.user_plan = SubscriptionPlan.PRO
                response = business_feature()
                assert response[1] == 403

            # Business user should pass
            with app.test_request_context('/business-feature'):
                g.user_plan = SubscriptionPlan.BUSINESS
                response = business_feature()
                assert 'success' in str(response.get_data())

            # Enterprise user should pass
            with app.test_request_context('/business-feature'):
                g.user_plan = SubscriptionPlan.ENTERPRISE
                response = business_feature()
                assert 'success' in str(response.get_data())


class TestCheckUsageLimitDecorator:
    """Test the check_usage_limit decorator"""

    def test_usage_limit_within_limit(self, app, db_session, test_user):
        """Test that user within usage limit can proceed"""
        # Set user within limit
        test_user.receipts_processed_month = 10
        db_session.commit()

        @app.route('/process')
        @check_usage_limit
        def process_route():
            return jsonify({'message': 'processed'})

        with app.test_client() as client:
            with app.test_request_context('/process'):
                g.user_id = str(test_user.id)
                g.user_plan = test_user.plan

                with patch('auth.decorators.get_db_context') as mock_get_db:
                    mock_get_db.return_value.__enter__.return_value = db_session

                    response = process_route()
                    assert 'processed' in str(response.get_data())

    def test_usage_limit_at_limit(self, app, db_session, test_user):
        """Test that user at usage limit is blocked"""
        from database.models import SubscriptionPlan

        # Set user at free plan limit (50)
        test_user.plan = SubscriptionPlan.FREE
        test_user.receipts_processed_month = 50
        db_session.commit()

        @app.route('/process')
        @check_usage_limit
        def process_route():
            return jsonify({'message': 'processed'})

        with app.test_client() as client:
            with app.test_request_context('/process'):
                g.user_id = str(test_user.id)
                g.user_plan = test_user.plan

                with patch('auth.decorators.get_db_context') as mock_get_db:
                    mock_get_db.return_value.__enter__.return_value = db_session

                    response = process_route()
                    assert response[1] == 429
                    data = response[0].get_json()
                    assert 'usage limit exceeded' in data['error'].lower()

    def test_usage_limit_increments_counter(self, app, db_session, test_user):
        """Test that successful request increments usage counter"""
        initial_count = test_user.receipts_processed_month

        @app.route('/process')
        @check_usage_limit
        def process_route():
            return jsonify({'message': 'processed'})

        with app.test_client() as client:
            with app.test_request_context('/process'):
                g.user_id = str(test_user.id)
                g.user_plan = test_user.plan

                with patch('auth.decorators.get_db_context') as mock_get_db:
                    mock_get_db.return_value.__enter__.return_value = db_session

                    process_route()

                    # Check counter was incremented
                    db_session.refresh(test_user)
                    assert test_user.receipts_processed_month == initial_count + 1

    def test_usage_limit_different_plan_limits(self, app, db_session, test_user):
        """Test that different plans have different limits"""
        from database.models import SubscriptionPlan

        @app.route('/process')
        @check_usage_limit
        def process_route():
            return jsonify({'message': 'processed'})

        # Test free plan limit (50)
        test_user.plan = SubscriptionPlan.FREE
        test_user.receipts_processed_month = 49
        db_session.commit()

        with app.test_client() as client:
            with app.test_request_context('/process'):
                g.user_id = str(test_user.id)
                g.user_plan = test_user.plan

                with patch('auth.decorators.get_db_context') as mock_get_db:
                    mock_get_db.return_value.__enter__.return_value = db_session
                    response = process_route()
                    # Should work (49 < 50)
                    assert 'processed' in str(response.get_data())

        # Test pro plan has higher limit (1000)
        test_user.plan = SubscriptionPlan.PRO
        test_user.receipts_processed_month = 500
        db_session.commit()

        with app.test_client() as client:
            with app.test_request_context('/process'):
                g.user_id = str(test_user.id)
                g.user_plan = test_user.plan

                with patch('auth.decorators.get_db_context') as mock_get_db:
                    mock_get_db.return_value.__enter__.return_value = db_session
                    response = process_route()
                    # Should work (500 < 1000)
                    assert 'processed' in str(response.get_data())


class TestDecoratorChaining:
    """Test that decorators work correctly when chained together"""

    def test_require_auth_and_require_admin_chained(self, app, db_session, test_admin_user):
        """Test chaining require_auth and require_admin"""
        from auth.jwt_handler import create_access_token

        token = create_access_token(
            str(test_admin_user.id),
            test_admin_user.email,
            test_admin_user.is_admin
        )

        @app.route('/admin')
        @require_auth
        @require_admin
        def admin_route():
            return jsonify({'message': 'admin success'})

        with app.test_client() as client:
            with patch('auth.decorators.get_db_context') as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = db_session

                response = client.get('/admin', headers={
                    'Authorization': f'Bearer {token}'
                })

                assert response.status_code == 200

    def test_require_auth_and_rate_limit_chained(self, app, db_session, test_user):
        """Test chaining require_auth and rate_limit"""
        from auth.jwt_handler import create_access_token

        _rate_limit_storage.clear()
        token = create_access_token(str(test_user.id), test_user.email, False)

        @app.route('/limited')
        @require_auth
        @rate_limit(max_requests=2, window_seconds=60)
        def limited_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with patch('auth.decorators.get_db_context') as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = db_session

                headers = {'Authorization': f'Bearer {token}'}

                # First two requests should work
                response1 = client.get('/limited', headers=headers)
                response2 = client.get('/limited', headers=headers)

                # Third should be rate limited
                response3 = client.get('/limited', headers=headers)
                assert response3.status_code == 429
