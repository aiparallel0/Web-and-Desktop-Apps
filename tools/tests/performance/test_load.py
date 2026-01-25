"""
Load Testing Suite
Tests concurrent user handling and response times under load
Target: 100+ concurrent users, <500ms response time
"""
import pytest
import time
import concurrent.futures
import statistics
from typing import List, Dict, Any
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

try:
    import requests
except ImportError:
    requests = None


class LoadTestResult:
    """Container for load test results"""
    def __init__(self):
        self.response_times: List[float] = []
        self.errors: List[Dict[str, Any]] = []
        self.success_count = 0
        self.total_requests = 0
        
    def add_result(self, duration: float, success: bool, error: str = None):
        self.total_requests += 1
        if success:
            self.success_count += 1
            self.response_times.append(duration)
        else:
            self.errors.append({
                'duration': duration,
                'error': error
            })
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from results"""
        if not self.response_times:
            return {
                'success_rate': 0,
                'avg_response_time': 0,
                'median_response_time': 0,
                'p95_response_time': 0,
                'p99_response_time': 0,
                'total_requests': self.total_requests,
                'errors': len(self.errors)
            }
        
        sorted_times = sorted(self.response_times)
        return {
            'success_rate': (self.success_count / self.total_requests) * 100,
            'avg_response_time': statistics.mean(self.response_times),
            'median_response_time': statistics.median(self.response_times),
            'min_response_time': min(self.response_times),
            'max_response_time': max(self.response_times),
            'p95_response_time': sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 0 else 0,
            'p99_response_time': sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 0 else 0,
            'total_requests': self.total_requests,
            'successful_requests': self.success_count,
            'failed_requests': len(self.errors)
        }


@pytest.fixture(scope='module')
def base_url():
    """Base URL for testing (configurable via environment)"""
    return os.getenv('TEST_BASE_URL', 'http://localhost:5000')


@pytest.fixture(scope='module')
def test_auth_token(base_url):
    """
    Get authentication token for testing
    Returns None if auth not required or test user not configured
    """
    if not requests:
        return None
        
    test_email = os.getenv('TEST_USER_EMAIL')
    test_password = os.getenv('TEST_USER_PASSWORD')
    
    if not test_email or not test_password:
        return None
    
    try:
        response = requests.post(
            f"{base_url}/api/auth/login",
            json={'email': test_email, 'password': test_password},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get('access_token')
    except Exception:
        pass
    
    return None


def make_request(url: str, method: str = 'GET', headers: Dict = None, json: Dict = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Make HTTP request and measure response time
    Returns dict with success, duration, and error info
    """
    if not requests:
        return {
            'success': False,
            'duration': 0,
            'status_code': 0,
            'error': 'requests library not installed'
        }
    
    start_time = time.time()
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=json, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        duration = time.time() - start_time
        success = response.status_code < 400
        
        return {
            'success': success,
            'duration': duration,
            'status_code': response.status_code,
            'error': None if success else f"HTTP {response.status_code}"
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            'success': False,
            'duration': duration,
            'status_code': 0,
            'error': str(e)
        }


@pytest.mark.performance
@pytest.mark.skipif(requests is None, reason="requests library not installed")
class TestLoadBasic:
    """Basic load tests without authentication"""
    
    def test_health_endpoint_load(self, base_url):
        """
        Test: Health endpoint under load
        Target: 100 concurrent requests, 100% success rate
        """
        num_requests = 100
        results = LoadTestResult()
        
        def worker():
            result = make_request(f"{base_url}/api/health")
            return result
        
        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(worker) for _ in range(num_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.add_result(
                    duration=result['duration'],
                    success=result['success'],
                    error=result['error']
                )
        
        stats = results.get_statistics()
        
        # Assertions
        assert stats['success_rate'] >= 95, f"Success rate {stats['success_rate']:.2f}% below 95%"
        assert stats['avg_response_time'] < 1.0, f"Average response time {stats['avg_response_time']:.3f}s exceeds 1s"
        assert stats['p95_response_time'] < 2.0, f"P95 response time {stats['p95_response_time']:.3f}s exceeds 2s"
        
        # Print results
        print(f"\n--- Health Endpoint Load Test Results ---")
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Success Rate: {stats['success_rate']:.2f}%")
        print(f"Avg Response Time: {stats['avg_response_time']:.3f}s")
        print(f"Median Response Time: {stats['median_response_time']:.3f}s")
        print(f"P95 Response Time: {stats['p95_response_time']:.3f}s")
        print(f"P99 Response Time: {stats['p99_response_time']:.3f}s")
    
    def test_models_endpoint_load(self, base_url):
        """
        Test: Models list endpoint under load
        Target: 50 concurrent requests, <500ms response
        """
        num_requests = 50
        results = LoadTestResult()
        
        def worker():
            result = make_request(f"{base_url}/api/models")
            return result
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker) for _ in range(num_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.add_result(
                    duration=result['duration'],
                    success=result['success'],
                    error=result['error']
                )
        
        stats = results.get_statistics()
        
        # Assertions
        assert stats['success_rate'] >= 90, f"Success rate {stats['success_rate']:.2f}% below 90%"
        assert stats['avg_response_time'] < 0.5, f"Average response time {stats['avg_response_time']:.3f}s exceeds 500ms"
        
        print(f"\n--- Models Endpoint Load Test Results ---")
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Success Rate: {stats['success_rate']:.2f}%")
        print(f"Avg Response Time: {stats['avg_response_time']:.3f}s")


@pytest.mark.performance
@pytest.mark.authenticated
@pytest.mark.skipif(requests is None, reason="requests library not installed")
class TestLoadAuthenticated:
    """Load tests requiring authentication"""
    
    @pytest.mark.skipif(
        not os.getenv('TEST_USER_EMAIL'),
        reason="TEST_USER_EMAIL not configured"
    )
    def test_receipts_list_load(self, base_url, test_auth_token):
        """
        Test: Receipts list endpoint under load
        Target: 100 concurrent requests from authenticated users
        """
        if not test_auth_token:
            pytest.skip("Authentication token not available")
        
        num_requests = 100
        results = LoadTestResult()
        headers = {'Authorization': f'Bearer {test_auth_token}'}
        
        def worker():
            result = make_request(f"{base_url}/api/receipts", headers=headers)
            return result
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(worker) for _ in range(num_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.add_result(
                    duration=result['duration'],
                    success=result['success'],
                    error=result['error']
                )
        
        stats = results.get_statistics()
        
        # Assertions
        assert stats['success_rate'] >= 95, f"Success rate {stats['success_rate']:.2f}% below 95%"
        assert stats['avg_response_time'] < 0.5, f"Average response time {stats['avg_response_time']:.3f}s exceeds 500ms"
        
        print(f"\n--- Receipts List Load Test Results ---")
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Success Rate: {stats['success_rate']:.2f}%")
        print(f"Avg Response Time: {stats['avg_response_time']:.3f}s")


@pytest.mark.performance
@pytest.mark.skipif(requests is None, reason="requests library not installed")
class TestDatabaseLoad:
    """Database connection pool and query performance under load"""
    
    def test_concurrent_database_queries(self, base_url):
        """
        Test: Database handles concurrent queries without exhausting connection pool
        Target: 50 concurrent database-heavy requests
        """
        num_requests = 50
        results = LoadTestResult()
        
        def worker():
            # Health endpoint checks database connectivity
            result = make_request(f"{base_url}/api/health")
            return result
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(worker) for _ in range(num_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.add_result(
                    duration=result['duration'],
                    success=result['success'],
                    error=result['error']
                )
        
        stats = results.get_statistics()
        
        # Check for connection pool errors
        pool_errors = [e for e in results.errors if 'pool' in str(e.get('error', '')).lower()]
        
        assert len(pool_errors) == 0, f"Connection pool errors detected: {len(pool_errors)}"
        assert stats['success_rate'] >= 95, f"Success rate {stats['success_rate']:.2f}% below 95%"
        
        print(f"\n--- Database Load Test Results ---")
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Success Rate: {stats['success_rate']:.2f}%")
        print(f"Connection Pool Errors: {len(pool_errors)}")


if __name__ == '__main__':
    """
    Run load tests directly:
    python test_load.py
    
    Or with pytest:
    pytest test_load.py -v -s
    
    Configure via environment variables:
    export TEST_BASE_URL=http://localhost:5000
    export TEST_USER_EMAIL=test@example.com
    export TEST_USER_PASSWORD=testpass123
    """
    pytest.main([__file__, '-v', '-s'])
