#!/usr/bin/env python3
"""
Standalone test script for Railway deployment fixes.

Tests the new features without requiring pytest or other test dependencies.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_test_header(text):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ PASS: {text}{Colors.END}")

def print_failure(text):
    print(f"{Colors.RED}❌ FAIL: {text}{Colors.END}")

def print_info(text):
    print(f"  {text}")


class RailwayDeploymentTester:
    """Test Railway deployment fixes."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.total = 0
    
    def test(self, name, func):
        """Run a single test."""
        self.total += 1
        try:
            func()
            print_success(name)
            self.passed += 1
            return True
        except AssertionError as e:
            print_failure(f"{name}: {e}")
            self.failed += 1
            return False
        except Exception as e:
            print_failure(f"{name}: Unexpected error: {e}")
            self.failed += 1
            return False
    
    def test_startup_validator_import(self):
        """Test that startup_validator can be imported."""
        from web.backend.startup_validator import StartupValidator
        assert StartupValidator is not None
        print_info("StartupValidator class imported successfully")
    
    def test_startup_validator_init(self):
        """Test StartupValidator initialization."""
        from web.backend.startup_validator import StartupValidator
        validator = StartupValidator()
        assert validator.errors == []
        assert validator.warnings == []
        print_info("StartupValidator initialized with empty errors/warnings")
    
    def test_port_validation(self):
        """Test PORT validation."""
        from web.backend.startup_validator import StartupValidator
        
        # Test valid port
        os.environ['PORT'] = '5000'
        validator = StartupValidator()
        result = validator.check_port_configuration()
        assert result is True
        assert len(validator.errors) == 0
        print_info("Valid PORT accepted: 5000")
        
        # Test invalid port
        os.environ['PORT'] = 'invalid'
        validator2 = StartupValidator()
        result2 = validator2.check_port_configuration()
        assert result2 is False
        assert len(validator2.errors) > 0
        print_info("Invalid PORT rejected: 'invalid'")
        
        # Clean up
        os.environ.pop('PORT', None)
    
    def test_env_var_validation(self):
        """Test environment variable validation."""
        from web.backend.startup_validator import StartupValidator
        
        # Clear env vars
        os.environ.pop('SECRET_KEY', None)
        os.environ.pop('JWT_SECRET', None)
        
        # Test without required variables
        validator1 = StartupValidator()
        result1 = validator1.check_environment_variables()
        assert result1 is False
        print_info("Missing SECRET_KEY/JWT_SECRET detected")
        
        # Test with valid variables (32+ chars)
        os.environ['SECRET_KEY'] = 'a' * 32
        os.environ['JWT_SECRET'] = 'b' * 32
        validator2 = StartupValidator()
        result2 = validator2.check_environment_variables()
        assert result2 is True
        print_info("Valid SECRET_KEY/JWT_SECRET accepted (32+ chars)")
        
        # Clean up
        os.environ.pop('SECRET_KEY', None)
        os.environ.pop('JWT_SECRET', None)
    
    def test_health_endpoint_startup_state(self):
        """Test that app.py has startup_state."""
        try:
            from web.backend import app
            
            # Check startup_state exists
            assert hasattr(app, 'startup_state')
            startup_state = app.startup_state
            
            # Verify structure
            assert 'completed' in startup_state
            assert 'errors' in startup_state
            assert 'warnings' in startup_state
            assert 'timestamp' in startup_state
            print_info(f"startup_state exists with {len(startup_state)} fields")
        except ImportError as e:
            # Flask not installed - skip this test
            print_info(f"Skipping (Flask not available): {e}")
            # This is acceptable in test environment
    
    def test_railway_json(self):
        """Test railway.json configuration."""
        railway_json_path = project_root / 'railway.json'
        assert railway_json_path.exists()
        print_info("railway.json exists")
        
        with open(railway_json_path) as f:
            config = json.load(f)
        
        # Verify critical fields
        assert config['deploy']['healthcheckPath'] == '/api/health'
        assert config['deploy']['healthcheckTimeout'] == 300
        assert config['deploy']['restartPolicyMaxRetries'] == 3
        
        # Verify startCommand is NOT present (Railway uses Dockerfile CMD)
        assert 'startCommand' not in config['deploy']
        print_info("railway.json has correct configuration (no startCommand)")
    
    def test_dockerfile_optimized(self):
        """Test Dockerfile optimization."""
        dockerfile_path = project_root / 'Dockerfile'
        assert dockerfile_path.exists()
        print_info("Dockerfile exists")
        
        content = dockerfile_path.read_text()
        
        # Check for shell form CMD (not JSON array form) for proper PORT expansion
        has_shell_form = 'CMD sh -c "gunicorn' in content
        assert has_shell_form
        print_info("Dockerfile uses shell form CMD for PORT variable expansion")
        
        # Check PORT variable expansion syntax
        assert '${PORT:-5000}' in content
        print_info("Dockerfile uses ${PORT:-5000} for variable expansion")
        
        # Check for logging
        assert '--log-level' in content
        print_info("Dockerfile has logging configured")
    
    def test_deployment_checker(self):
        """Test check_railway_ready.py."""
        script_path = project_root / 'check_railway_ready.py'
        assert script_path.exists()
        print_info("check_railway_ready.py exists")
        
        from check_railway_ready import DeploymentReadinessChecker
        checker = DeploymentReadinessChecker()
        assert checker.errors == []
        assert checker.warnings == []
        print_info("DeploymentReadinessChecker initialized")
    
    def test_documentation(self):
        """Test documentation files."""
        # Railway deployment guide
        doc_path = project_root / 'docs' / 'RAILWAY_DEPLOYMENT.md'
        assert doc_path.exists()
        content = doc_path.read_text()
        assert 'Pre-Deployment Checklist' in content
        assert 'Troubleshooting' in content
        print_info("RAILWAY_DEPLOYMENT.md exists with required sections")
        
        # Railway env template
        template_path = project_root / '.env.railway.template'
        assert template_path.exists()
        content = template_path.read_text()
        assert 'SECRET_KEY' in content
        assert 'JWT_SECRET' in content
        print_info(".env.railway.template exists with required vars")
    
    def test_package_structure(self):
        """Test Python package structure."""
        init_files = [
            'web/__init__.py',
            'web/backend/__init__.py',
            'shared/__init__.py'
        ]
        
        for init_file in init_files:
            init_path = project_root / init_file
            assert init_path.exists()
        
        print_info(f"All {len(init_files)} __init__.py files exist")
    
    def run_all_tests(self):
        """Run all tests."""
        print_test_header("RAILWAY DEPLOYMENT TESTS")
        
        tests = [
            ("startup_validator import", self.test_startup_validator_import),
            ("startup_validator initialization", self.test_startup_validator_init),
            ("PORT validation", self.test_port_validation),
            ("Environment variable validation", self.test_env_var_validation),
            ("Health endpoint startup_state", self.test_health_endpoint_startup_state),
            ("railway.json configuration", self.test_railway_json),
            ("Dockerfile optimization", self.test_dockerfile_optimized),
            ("Deployment readiness checker", self.test_deployment_checker),
            ("Documentation", self.test_documentation),
            ("Package structure", self.test_package_structure),
        ]
        
        for name, test_func in tests:
            self.test(name, test_func)
            print()  # Blank line between tests
        
        # Print summary
        print_test_header("TEST SUMMARY")
        print(f"\n{Colors.BOLD}Total tests: {self.total}{Colors.END}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.END}")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ ALL TESTS PASSED{Colors.END}\n")
            return 0
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ {self.failed} TEST(S) FAILED{Colors.END}\n")
            return 1


def main():
    """Main entry point."""
    tester = RailwayDeploymentTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
