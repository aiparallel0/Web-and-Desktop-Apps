"""
OWASP Security Testing Suite
Tests for common web application vulnerabilities based on OWASP Top 10
"""
import pytest
import os
import sys
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

try:
    import requests
except ImportError:
    requests = None


@pytest.fixture(scope='module')
def base_url():
    """Base URL for testing (configurable via environment)"""
    return os.getenv('TEST_BASE_URL', 'http://localhost:5000')


@pytest.mark.security
@pytest.mark.skipif(requests is None, reason="requests library not installed")
class TestAuthenticationSecurity:
    """A01:2021 - Broken Access Control"""
    
    def test_unauthorized_access_blocked(self, base_url):
        """
        Test: Endpoints require authentication
        OWASP: A01:2021 - Broken Access Control
        """
        protected_endpoints = [
            '/api/receipts',
            '/api/receipts/stats',
        ]
        
        for endpoint in protected_endpoints:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            assert response.status_code in [401, 403], \
                f"Endpoint {endpoint} not properly protected (got {response.status_code})"


@pytest.mark.security
@pytest.mark.skipif(requests is None, reason="requests library not installed")
class TestSecurityHeaders:
    """A05:2021 - Security Misconfiguration"""
    
    def test_security_headers_present(self, base_url):
        """
        Test: Critical security headers present
        OWASP: A05:2021 - Security Misconfiguration
        """
        response = requests.get(f"{base_url}/api/health", timeout=10)
        headers = response.headers
        
        # Check for security headers
        security_checks = {
            'X-Content-Type-Options': 'nosniff',
        }
        
        for header, expected_value in security_checks.items():
            assert header in headers, f"Missing security header: {header}"


if __name__ == '__main__':
    """Run security tests: pytest test_owasp.py -v -s"""
    pytest.main([__file__, '-v', '-s'])
