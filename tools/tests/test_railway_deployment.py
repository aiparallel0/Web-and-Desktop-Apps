"""
Test suite for Railway deployment fixes.

Tests:
- startup_validator.py functionality
- Health endpoint with startup state
- Environment variable validation
- Railway deployment readiness
"""

import sys
import os
import pytest
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


class TestStartupValidator:
    """Test startup_validator.py functionality."""
    
    def test_startup_validator_imports(self):
        """Test that startup_validator can be imported."""
        from web.backend.startup_validator import StartupValidator
        assert StartupValidator is not None
    
    def test_startup_validator_initialization(self):
        """Test StartupValidator initialization."""
        from web.backend.startup_validator import StartupValidator
        validator = StartupValidator()
        assert validator.errors == []
        assert validator.warnings == []
        assert validator.checks_passed == 0
        assert validator.checks_total == 0
    
    def test_port_validation_valid(self):
        """Test PORT validation with valid port."""
        from web.backend.startup_validator import StartupValidator
        validator = StartupValidator()
        
        # Test valid port
        os.environ['PORT'] = '5000'
        result = validator.check_port_configuration()
        assert result is True
        assert len(validator.errors) == 0
        
        # Clean up
        os.environ.pop('PORT', None)
    
    def test_port_validation_invalid(self):
        """Test PORT validation with invalid port."""
        from web.backend.startup_validator import StartupValidator
        validator = StartupValidator()
        
        # Test invalid port
        os.environ['PORT'] = 'invalid'
        result = validator.check_port_configuration()
        assert result is False
        assert len(validator.errors) > 0
        assert any('must be a number' in e for e in validator.errors)
        
        # Clean up
        os.environ.pop('PORT', None)
    
    def test_port_validation_out_of_range(self):
        """Test PORT validation with out-of-range port."""
        from web.backend.startup_validator import StartupValidator
        validator = StartupValidator()
        
        # Test out-of-range port
        os.environ['PORT'] = '99999'
        result = validator.check_port_configuration()
        assert result is False
        assert len(validator.errors) > 0
        
        # Clean up
        os.environ.pop('PORT', None)
    
    def test_environment_variable_validation(self):
        """Test environment variable validation."""
        from web.backend.startup_validator import StartupValidator
        
        # Test without required variables
        validator1 = StartupValidator()
        os.environ.pop('SECRET_KEY', None)
        os.environ.pop('JWT_SECRET', None)
        result1 = validator1.check_environment_variables()
        assert result1 is False
        assert len(validator1.errors) >= 2
        
        # Test with required variables
        validator2 = StartupValidator()
        os.environ['SECRET_KEY'] = 'a' * 32  # 32 characters
        os.environ['JWT_SECRET'] = 'b' * 32
        result2 = validator2.check_environment_variables()
        assert result2 is True
        assert len(validator2.errors) == 0
        
        # Clean up
        os.environ.pop('SECRET_KEY', None)
        os.environ.pop('JWT_SECRET', None)
    
    def test_disk_space_check(self):
        """Test disk space checking."""
        from web.backend.startup_validator import StartupValidator
        validator = StartupValidator()
        
        # This should pass unless disk is really full
        result = validator.check_disk_space(min_free_gb=0.1)
        # Don't assert result since it depends on actual disk space
        # Just verify it doesn't crash
        assert isinstance(result, bool)


class TestHealthEndpoint:
    """Test enhanced health endpoint."""
    
    def test_health_endpoint_exists(self):
        """Test that health endpoint is defined."""
        from web.backend import app
        app_instance = app.app
        
        # Check route exists
        routes = [rule.rule for rule in app_instance.url_map.iter_rules()]
        assert '/api/health' in routes
    
    def test_startup_state_exists(self):
        """Test that startup_state is defined in app.py."""
        from web.backend import app
        
        # Check startup_state exists
        assert hasattr(app, 'startup_state')
        startup_state = app.startup_state
        
        # Verify structure
        assert 'completed' in startup_state
        assert 'errors' in startup_state
        assert 'warnings' in startup_state
        assert 'timestamp' in startup_state
        
        # Verify types
        assert isinstance(startup_state['completed'], bool)
        assert isinstance(startup_state['errors'], list)
        assert isinstance(startup_state['warnings'], list)
        assert isinstance(startup_state['timestamp'], (int, float))


class TestRailwayConfiguration:
    """Test Railway deployment configuration."""
    
    def test_railway_json_exists(self):
        """Test that railway.json exists."""
        railway_json_path = project_root / 'railway.json'
        assert railway_json_path.exists()
    
    def test_railway_json_valid(self):
        """Test that railway.json is valid JSON."""
        railway_json_path = project_root / 'railway.json'
        with open(railway_json_path) as f:
            config = json.load(f)
        
        # Verify required fields
        assert 'deploy' in config
        deploy = config['deploy']
        
        assert 'healthcheckPath' in deploy
        assert deploy['healthcheckPath'] == '/api/health'
        
        assert 'healthcheckTimeout' in deploy
        assert deploy['healthcheckTimeout'] == 600
        
        assert 'restartPolicyMaxRetries' in deploy
        assert deploy['restartPolicyMaxRetries'] == 3
        
        assert 'sleepApplication' in deploy
        assert deploy['sleepApplication'] is False
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists."""
        dockerfile_path = project_root / 'Dockerfile'
        assert dockerfile_path.exists()
    
    def test_dockerfile_optimized(self):
        """Test that Dockerfile has optimized worker configuration."""
        dockerfile_path = project_root / 'Dockerfile'
        content = dockerfile_path.read_text()
        
        # Check for 2 workers (not 4)
        assert '--workers 2' in content
        assert '--workers 4' not in content
        
        # Check for exec form CMD
        assert 'CMD ["sh", "-c"' in content or 'CMD ["/bin/sh", "-c"' in content
        
        # Check for logging configuration
        assert '--access-logfile -' in content
        assert '--error-logfile -' in content


class TestDeploymentReadiness:
    """Test deployment readiness checker."""
    
    def test_check_railway_ready_exists(self):
        """Test that check_railway_ready.py exists."""
        script_path = project_root / 'check_railway_ready.py'
        assert script_path.exists()
    
    def test_check_railway_ready_imports(self):
        """Test that check_railway_ready.py can be imported."""
        import check_railway_ready
        assert hasattr(check_railway_ready, 'DeploymentReadinessChecker')
    
    def test_deployment_checker_initialization(self):
        """Test DeploymentReadinessChecker initialization."""
        from check_railway_ready import DeploymentReadinessChecker
        checker = DeploymentReadinessChecker()
        assert checker.errors == []
        assert checker.warnings == []
        assert checker.checks_passed == 0
        assert checker.checks_total == 0


class TestDocumentation:
    """Test deployment documentation."""
    
    def test_railway_deployment_guide_exists(self):
        """Test that RAILWAY_DEPLOYMENT.md exists."""
        doc_path = project_root / 'docs' / 'RAILWAY_DEPLOYMENT.md'
        assert doc_path.exists()
    
    def test_railway_deployment_guide_content(self):
        """Test that RAILWAY_DEPLOYMENT.md has required sections."""
        doc_path = project_root / 'docs' / 'RAILWAY_DEPLOYMENT.md'
        content = doc_path.read_text()
        
        # Check for key sections
        assert 'Pre-Deployment Checklist' in content
        assert 'Environment Setup' in content
        assert 'Deployment Steps' in content
        assert 'Troubleshooting' in content
        assert 'Monitoring & Logs' in content
    
    def test_env_railway_template_exists(self):
        """Test that .env.railway.template exists."""
        template_path = project_root / '.env.railway.template'
        assert template_path.exists()
    
    def test_env_railway_template_content(self):
        """Test that .env.railway.template has required variables."""
        template_path = project_root / '.env.railway.template'
        content = template_path.read_text()
        
        # Check for critical variables
        assert 'SECRET_KEY' in content
        assert 'JWT_SECRET' in content
        assert 'FLASK_ENV' in content
        assert 'FLASK_DEBUG' in content
        
        # Check for instructions
        assert 'generate-secrets.py' in content


class TestPackageStructure:
    """Test Python package structure."""
    
    def test_web_init_exists(self):
        """Test that web/__init__.py exists."""
        init_path = project_root / 'web' / '__init__.py'
        assert init_path.exists()
    
    def test_web_backend_init_exists(self):
        """Test that web/backend/__init__.py exists."""
        init_path = project_root / 'web' / 'backend' / '__init__.py'
        assert init_path.exists()


def run_all_tests():
    """Run all Railway deployment tests."""
    print("=" * 70)
    print("RAILWAY DEPLOYMENT TESTS")
    print("=" * 70)
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-k', 'test_'
    ])
    
    return exit_code


if __name__ == '__main__':
    sys.exit(run_all_tests())
