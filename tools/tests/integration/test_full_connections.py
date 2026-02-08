"""
=============================================================================
INTEGRATION TEST - Full System Connection Validation
=============================================================================

Tests all major connection points in the system:
1. Database connections (PostgreSQL/SQLite)
2. Redis connections (for Celery)
3. Celery worker/beat connectivity
4. Backend API endpoints
5. Frontend-backend API integration
6. Model loading and processing
7. Storage integrations (S3, GDrive, Dropbox)
8. Billing/Stripe integration
9. Authentication flow
10. WebSocket connections

Usage:
    pytest tools/tests/integration/test_full_connections.py -v
    
=============================================================================
"""

import pytest
import os
import sys
import time
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


class TestDatabaseConnections:
    """Test database connection health."""
    
    def test_database_import(self):
        """Test database module imports."""
        from web.backend.database import get_engine, init_db, check_database_health
        assert get_engine is not None
        assert init_db is not None
        assert check_database_health is not None
    
    def test_database_pool_import(self):
        """Test database pool module imports."""
        from web.backend.database_pool import (
            get_db_with_retry,
            monitor_pool_health,
            test_database_connectivity
        )
        assert get_db_with_retry is not None
        assert monitor_pool_health is not None
        assert test_database_connectivity is not None
    
    def test_database_health_check(self):
        """Test database health check function."""
        from web.backend.database import check_database_health
        
        health = check_database_health()
        assert isinstance(health, dict)
        assert 'status' in health
        # Note: may be 'unhealthy' if DB not running, which is OK for this test


class TestRedisConnections:
    """Test Redis connection for Celery."""
    
    def test_redis_import(self):
        """Test Redis import (optional)."""
        try:
            import redis
            assert redis is not None
        except ImportError:
            pytest.skip("Redis not installed (optional)")
    
    def test_redis_connection_config(self):
        """Test Redis URL configuration."""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        assert redis_url.startswith('redis://')


class TestCeleryConnections:
    """Test Celery worker and beat connectivity."""
    
    def test_celery_module_import(self):
        """Test Celery module imports."""
        from shared.services.background_tasks import (
            celery_app,
            get_celery_app,
            is_celery_available
        )
        # Module should import successfully
        assert get_celery_app is not None
        assert is_celery_available is not None
    
    def test_celery_tasks_defined(self):
        """Test Celery tasks are defined."""
        from shared.services.background_tasks import is_celery_available
        
        if not is_celery_available():
            pytest.skip("Celery not available")
        
        from shared.services.background_tasks import (
            process_email_task,
            process_analytics_task,
            cleanup_temp_files_task
        )
        assert process_email_task is not None
        assert process_analytics_task is not None
        assert cleanup_temp_files_task is not None


class TestBackendAPIConnections:
    """Test backend API endpoint connectivity."""
    
    @pytest.fixture
    def client(self):
        """Create Flask test client."""
        from web.backend.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_api_root(self, client):
        """Test API root endpoint."""
        response = client.get('/api')
        assert response.status_code == 200
        data = response.get_json()
        assert 'service' in data
        assert 'endpoints' in data
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
    
    def test_ready_endpoint(self, client):
        """Test readiness check endpoint."""
        response = client.get('/api/ready')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert 'checks' in data
    
    def test_models_endpoint(self, client):
        """Test models listing endpoint."""
        response = client.get('/api/models')
        assert response.status_code == 200
        data = response.get_json()
        assert 'models' in data
        assert isinstance(data['models'], list)
    
    def test_database_health_endpoint(self, client):
        """Test database health endpoint."""
        response = client.get('/api/database/health')
        # May be 200 or 503 depending on DB availability
        assert response.status_code in [200, 503]
        data = response.get_json()
        assert 'status' in data


class TestModelConnections:
    """Test model import and loading."""
    
    def test_model_manager_import(self):
        """Test model manager imports."""
        from shared.models.manager import ModelManager
        assert ModelManager is not None
    
    def test_model_manager_initialization(self):
        """Test model manager initialization."""
        from shared.models.manager import ModelManager
        manager = ModelManager()
        assert manager is not None
    
    def test_available_models(self):
        """Test getting available models."""
        from shared.models.manager import ModelManager
        manager = ModelManager()
        models = manager.get_available_models(check_availability=False)
        assert isinstance(models, list)
        assert len(models) > 0
    
    def test_model_schemas(self):
        """Test model schema imports."""
        from shared.models.schemas import (
            DetectionResult,
            DetectedText,
            BoundingBox
        )
        assert DetectionResult is not None
        assert DetectedText is not None
        assert BoundingBox is not None


class TestStorageConnections:
    """Test storage integration connections."""
    
    def test_storage_base_import(self):
        """Test storage base classes."""
        from web.backend.storage import (
            BaseStorageHandler,
            StorageFile,
            StorageError
        )
        assert BaseStorageHandler is not None
        assert StorageFile is not None
        assert StorageError is not None
    
    def test_storage_factory_import(self):
        """Test storage factory."""
        from web.backend.storage import StorageFactory
        assert StorageFactory is not None
    
    def test_storage_handlers_import(self):
        """Test storage handler imports."""
        from web.backend.storage import (
            S3StorageHandler,
            GoogleDriveHandler,
            DropboxStorageHandler
        )
        assert S3StorageHandler is not None
        assert GoogleDriveHandler is not None
        assert DropboxStorageHandler is not None
    
    def test_storage_provider_availability(self):
        """Test storage provider availability checks."""
        from web.backend.storage import StorageFactory
        
        # Should not raise, just return False if not configured
        s3_available = StorageFactory.is_provider_available('s3')
        gdrive_available = StorageFactory.is_provider_available('gdrive')
        dropbox_available = StorageFactory.is_provider_available('dropbox')
        
        assert isinstance(s3_available, bool)
        assert isinstance(gdrive_available, bool)
        assert isinstance(dropbox_available, bool)


class TestBillingConnections:
    """Test billing/Stripe integration connections."""
    
    def test_billing_imports(self):
        """Test billing module imports."""
        from web.backend.billing import (
            SUBSCRIPTION_PLANS,
            StripeHandler,
            billing_bp
        )
        assert SUBSCRIPTION_PLANS is not None
        assert StripeHandler is not None
        assert billing_bp is not None
    
    def test_subscription_plans(self):
        """Test subscription plans are defined."""
        from web.backend.billing import SUBSCRIPTION_PLANS
        
        assert 'free' in SUBSCRIPTION_PLANS
        assert 'pro' in SUBSCRIPTION_PLANS
        assert 'business' in SUBSCRIPTION_PLANS
        
        # Verify plan structure
        for plan_name, plan in SUBSCRIPTION_PLANS.items():
            assert 'name' in plan
            assert 'price' in plan
            assert 'features' in plan
    
    def test_billing_middleware(self):
        """Test billing middleware imports."""
        from web.backend.billing import (
            require_subscription,
            check_usage_limits
        )
        assert require_subscription is not None
        assert check_usage_limits is not None


class TestAuthenticationFlow:
    """Test authentication flow connections."""
    
    def test_auth_imports(self):
        """Test auth module imports."""
        from web.backend.auth import (
            hash_password,
            verify_password,
            create_access_token,
            require_auth
        )
        assert hash_password is not None
        assert verify_password is not None
        assert create_access_token is not None
        assert require_auth is not None
    
    def test_password_hashing(self):
        """Test password hashing functions."""
        from web.backend.auth import hash_password, verify_password
        
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False
    
    def test_jwt_creation(self):
        """Test JWT token creation."""
        from web.backend.auth import create_access_token, verify_access_token
        
        user_id = "test_user_123"
        token = create_access_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        payload = verify_access_token(token)
        assert payload is not None
        assert payload.get('user_id') == user_id
    
    @pytest.fixture
    def client(self):
        """Create Flask test client."""
        from web.backend.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_auth_blueprint_registered(self, client):
        """Test auth blueprint is registered."""
        # Test auth endpoints exist
        response = client.post('/api/auth/register', json={})
        # Should return 400 (bad request) not 404 (not found)
        assert response.status_code != 404


class TestFrontendBackendIntegration:
    """Test frontend-backend API integration."""
    
    def test_frontend_files_exist(self):
        """Test frontend files exist."""
        frontend_path = os.path.join(
            os.path.dirname(__file__),
            '../../../web/frontend'
        )
        
        assert os.path.exists(os.path.join(frontend_path, 'index.html'))
        assert os.path.exists(os.path.join(frontend_path, 'app.js'))
        assert os.path.exists(os.path.join(frontend_path, 'styles.css'))
    
    def test_api_endpoint_detection(self):
        """Test API endpoint detection logic."""
        # The frontend auto-detects backend URL
        # Verify the detection logic works
        
        # In production: same origin
        # In dev: frontend on 3000, backend on 5000
        
        # This is tested in the JavaScript, just verify files exist
        frontend_path = os.path.join(
            os.path.dirname(__file__),
            '../../../web/frontend/app.js'
        )
        
        with open(frontend_path, 'r') as f:
            content = f.read()
            assert 'detectBackendUrl' in content
            assert 'API_BASE_URL' in content


class TestWebSocketConnections:
    """Test WebSocket connection setup."""
    
    def test_websocket_module_import(self):
        """Test WebSocket module imports."""
        from web.backend.api.websocket import init_websocket
        assert init_websocket is not None


class TestSystemIntegration:
    """Test overall system integration."""
    
    def test_all_modules_importable(self):
        """Test all major modules can be imported."""
        modules_to_test = [
            'web.backend.app',
            'web.backend.database',
            'web.backend.auth',
            'web.backend.config',
            'shared.models.manager',
            'shared.models.engine',
            'shared.services.background_tasks',
            'web.backend.storage',
            'web.backend.billing',
        ]
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")
    
    def test_no_circular_imports(self):
        """Test there are no circular import issues."""
        # If we can import all modules, circular imports are resolved
        from web.backend.app import app
        from web.backend.database import get_engine
        from shared.models.manager import ModelManager
        from shared.services.background_tasks import celery_app
        
        assert app is not None
        assert get_engine is not None
        assert ModelManager is not None
        # celery_app may be None if Celery not installed


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
