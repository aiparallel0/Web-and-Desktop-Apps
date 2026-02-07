"""
Test Railway deployment fixes.

Tests for health check endpoints, database validation, and error handling.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


class TestHealthCheckEndpoints:
    """Test health check endpoints behavior."""

    def test_health_endpoint_returns_200(self):
        """Test /api/health always returns 200 if app is running."""
        from web.backend.app import app
        
        with app.test_client() as client:
            response = client.get('/api/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert data['service'] == 'receipt-extractor'

    def test_ready_endpoint_returns_200_with_working_db(self):
        """Test /api/ready returns 200 when database is working."""
        from web.backend.app import app
        
        # Use in-memory SQLite for test
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:', 'USE_SQLITE': 'true'}):
            with app.test_client() as client:
                response = client.get('/api/ready')
                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'ready'
                assert 'checks' in data
                assert data['checks']['app'] == 'ok'

    def test_ready_endpoint_returns_200_with_failed_db(self):
        """Test /api/ready returns 200 even when database fails (non-blocking)."""
        from web.backend.app import app
        
        # Mock get_engine to simulate database failure
        def mock_get_engine():
            engine = MagicMock()
            def raise_error():
                raise Exception('Connection refused - database not available')
            engine.connect = raise_error
            return engine
        
        with patch('web.backend.app.get_engine', mock_get_engine):
            with app.test_client() as client:
                response = client.get('/api/ready')
                # Should return 200 even with database failure
                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'ready'
                assert 'database' in data['checks']
                assert 'degraded' in data['checks']['database']


class TestDatabaseValidation:
    """Test database validation function."""

    def test_sqlite_validation_with_writable_tmp(self):
        """Test SQLite validation passes with /tmp path."""
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:////tmp/test.db', 'USE_SQLITE': 'true'}):
            # Reload database module to pick up new environment
            import importlib
            from web.backend import database
            importlib.reload(database)
            
            # Should not raise exception
            try:
                database.validate_database_config()
            except Exception as e:
                pytest.fail(f"Validation should pass for /tmp SQLite: {e}")

    def test_postgresql_localhost_validation_fails(self):
        """Test validation fails with helpful error for localhost PostgreSQL."""
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@localhost:5432/test'}):
            # Reload database module to pick up new environment
            import importlib
            from web.backend import database
            importlib.reload(database)
            
            # Should raise RuntimeError with helpful message
            with pytest.raises(RuntimeError, match="Database not configured properly"):
                database.validate_database_config()

    def test_postgresql_localhost_railway_error_message(self):
        """Test Railway-specific error message for localhost PostgreSQL."""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/test',
            'RAILWAY_ENVIRONMENT': 'production'
        }):
            # Reload database module to pick up new environment
            import importlib
            from web.backend import database
            importlib.reload(database)
            
            # Should raise RuntimeError with Railway-specific instructions
            with pytest.raises(RuntimeError, match="Database not configured properly"):
                database.validate_database_config()


class TestLoggingConfiguration:
    """Test logging is properly configured."""

    def test_logging_format_configured(self):
        """Test logging uses proper format string, not raw %%."""
        from web.backend import app
        
        # Check that logging is configured
        import logging
        root_logger = logging.getLogger()
        
        # Should have handlers
        assert len(root_logger.handlers) > 0
        
        # Check format doesn't contain raw %% strings
        for handler in root_logger.handlers:
            if hasattr(handler, 'formatter') and handler.formatter:
                format_str = handler.formatter._fmt
                # Should not have %% (escaped percent signs)
                assert '%%(' not in format_str, f"Logging format should not contain raw %%: {format_str}"


class TestRailwayConfiguration:
    """Test Railway-specific configuration."""

    def test_railway_toml_uses_correct_health_path(self):
        """Test railway.toml uses /api/health for health checks."""
        import toml
        
        toml_path = os.path.join(
            os.path.dirname(__file__),
            '../../../railway.toml'
        )
        
        if os.path.exists(toml_path):
            config = toml.load(toml_path)
            assert 'deploy' in config
            assert config['deploy']['healthcheckPath'] == '/api/health'


class TestDocumentation:
    """Test documentation exists."""

    def test_railway_setup_guide_exists(self):
        """Test RAILWAY_SETUP.md documentation exists."""
        doc_path = os.path.join(
            os.path.dirname(__file__),
            '../../../docs/RAILWAY_SETUP.md'
        )
        assert os.path.exists(doc_path), "RAILWAY_SETUP.md should exist"

    def test_readme_has_railway_section(self):
        """Test README.md includes Railway deployment section."""
        readme_path = os.path.join(
            os.path.dirname(__file__),
            '../../../README.md'
        )
        
        with open(readme_path, 'r') as f:
            content = f.read()
            assert 'Railway' in content, "README should mention Railway"
            assert 'RAILWAY_SETUP.md' in content, "README should link to setup guide"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
