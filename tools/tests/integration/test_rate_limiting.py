"""
Integration tests for rate limiting enforcement.

These tests verify rate limiting works correctly across:
- Multiple request types
- Different client identifiers
- Window expiration and reset
- Limit configuration
"""
import pytest
import time


class TestRateLimitEnforcement:
    """Test rate limiting is properly enforced."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for testing."""
        try:
            from web.backend.security.rate_limiting import RateLimiter
            return RateLimiter(backend='memory')
        except ImportError:
            pytest.skip("Rate limiting module not available")
    
    def test_rate_limit_basic_enforcement(self, rate_limiter):
        """Test basic rate limit is enforced."""
        client_id = "basic-test-client"
        max_requests = 10
        window_seconds = 60
        
        # All requests within limit should pass
        for i in range(10):
            result, _ = rate_limiter.is_allowed(client_id, max_requests, window_seconds)
            assert result is True, f"Request {i+1}/10 should be allowed"
        
        # 11th request should fail
        result, _ = rate_limiter.is_allowed(client_id, max_requests, window_seconds)
        assert result is False, "11th request should be denied"
    
    def test_rate_limit_separate_clients(self, rate_limiter):
        """Test rate limits are tracked per client."""
        client_a = "client-a"
        client_b = "client-b"
        max_requests = 10
        window_seconds = 60
        
        # Use up client A's limit
        for _ in range(10):
            rate_limiter.is_allowed(client_a, max_requests, window_seconds)
        
        # Client A should be limited
        allowed, _ = rate_limiter.is_allowed(client_a, max_requests, window_seconds)
        assert allowed is False
        
        # Client B should still have full limit
        allowed, _ = rate_limiter.is_allowed(client_b, max_requests, window_seconds)
        assert allowed is True
    
    def test_rate_limit_window_reset(self):
        """Test rate limit resets after window expires."""
        try:
            from web.backend.security.rate_limiting import RateLimiter
        except ImportError:
            pytest.skip("Rate limiting module not available")
        
        limiter = RateLimiter(backend='memory')
        client_id = "reset-client"
        max_requests = 2
        window_seconds = 1  # 1 second window
        
        # Use up limit
        limiter.is_allowed(client_id, max_requests, window_seconds)
        limiter.is_allowed(client_id, max_requests, window_seconds)
        allowed, _ = limiter.is_allowed(client_id, max_requests, window_seconds)
        assert allowed is False
        
        # Wait for window to expire (use 1.3s for reliable timing across system loads)
        time.sleep(1.3)
        
        # Should be allowed again
        allowed, _ = limiter.is_allowed(client_id, max_requests, window_seconds)
        assert allowed is True
    
    def test_rate_limit_info_returned(self, rate_limiter):
        """Test rate limit info is returned with response."""
        client_id = "info-client"
        max_requests = 5
        window_seconds = 60
        
        # Make a request
        allowed, info = rate_limiter.is_allowed(client_id, max_requests, window_seconds)
        
        assert allowed is True
        assert 'limit' in info
        assert 'remaining' in info
        assert 'reset' in info
        assert info['limit'] == max_requests


class TestRateLimitConfiguration:
    """Test rate limit configuration options."""
    
    def test_custom_limit_configuration(self):
        """Test custom rate limit values."""
        try:
            from web.backend.security.rate_limiting import RateLimiter
        except ImportError:
            pytest.skip("Rate limiting module not available")
        
        limiter = RateLimiter(backend='memory')
        
        # Very low limit
        client_low = "low-client"
        allowed, _ = limiter.is_allowed(client_low, 1, 60)
        assert allowed is True
        allowed, _ = limiter.is_allowed(client_low, 1, 60)
        assert allowed is False
        
        # High limit
        client_high = "high-client"
        for _ in range(100):
            allowed, _ = limiter.is_allowed(client_high, 1000, 60)
            assert allowed is True


class TestRateLimitByEndpoint:
    """Test rate limiting by endpoint type."""
    
    def test_different_limits_per_endpoint(self):
        """Test different endpoints can have different limits."""
        try:
            from web.backend.security.rate_limiting import RateLimiter
        except ImportError:
            pytest.skip("Rate limiting module not available")
        
        limiter = RateLimiter(backend='memory')
        
        client_id = "multi-endpoint-client"
        
        # Auth endpoint - lower limit
        auth_key = f"auth:{client_id}"
        for _ in range(5):
            limiter.is_allowed(auth_key, 5, 60)
        allowed, _ = limiter.is_allowed(auth_key, 5, 60)
        assert allowed is False
        
        # API endpoint - higher limit
        api_key = f"api:{client_id}"
        allowed, _ = limiter.is_allowed(api_key, 100, 60)
        assert allowed is True
    
    def test_burst_protection(self):
        """Test protection against request bursts."""
        try:
            from web.backend.security.rate_limiting import RateLimiter
        except ImportError:
            pytest.skip("Rate limiting module not available")
        
        limiter = RateLimiter(backend='memory')
        client_id = "burst-client"
        max_requests = 10
        window_seconds = 1
        
        # Rapid burst of requests
        results = []
        for _ in range(15):
            allowed, _ = limiter.is_allowed(client_id, max_requests, window_seconds)
            results.append(allowed)
        
        # First 10 should pass
        assert all(results[:10])
        
        # Rest should fail
        assert not any(results[10:])


class TestRateLimitHeaders:
    """Test rate limit response info."""
    
    def test_rate_limit_info_generation(self):
        """Test rate limit info is correctly generated."""
        try:
            from web.backend.security.rate_limiting import RateLimiter
        except ImportError:
            pytest.skip("Rate limiting module not available")
        
        limiter = RateLimiter(backend='memory')
        
        client_id = "info-client"
        max_requests = 100
        window_seconds = 3600
        
        allowed, info = limiter.is_allowed(client_id, max_requests, window_seconds)
        
        # Check standard rate limit info
        assert 'limit' in info
        assert 'remaining' in info
        assert 'reset' in info
        assert info['limit'] == max_requests


class TestRateLimitPersistence:
    """Test rate limit state persistence."""
    
    def test_in_memory_persistence(self):
        """Test rate limits persist in memory across checks."""
        try:
            from web.backend.security.rate_limiting import RateLimiter
        except ImportError:
            pytest.skip("Rate limiting module not available")
        
        limiter = RateLimiter(backend='memory')
        client_id = "persist-client"
        max_requests = 5
        window_seconds = 300
        
        # Make some requests
        for _ in range(3):
            limiter.is_allowed(client_id, max_requests, window_seconds)
        
        # Make more requests
        for _ in range(2):
            limiter.is_allowed(client_id, max_requests, window_seconds)
        
        # Should be at limit now
        allowed, _ = limiter.is_allowed(client_id, max_requests, window_seconds)
        assert allowed is False
    
    def test_concurrent_client_isolation(self):
        """Test multiple clients are isolated."""
        try:
            from web.backend.security.rate_limiting import RateLimiter
        except ImportError:
            pytest.skip("Rate limiting module not available")
        
        limiter = RateLimiter(backend='memory')
        
        clients = ["client-1", "client-2", "client-3"]
        max_requests = 3
        window_seconds = 60
        
        # Each client makes requests
        for client in clients:
            for _ in range(3):
                limiter.is_allowed(client, max_requests, window_seconds)
        
        # All clients should be at their limit
        for client in clients:
            allowed, _ = limiter.is_allowed(client, max_requests, window_seconds)
            assert allowed is False
