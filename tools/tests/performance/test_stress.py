"""
Stress Testing Suite
Tests system behavior under extreme load to find breaking points
Gradually increases load until failures occur
"""
import pytest
import time
import concurrent.futures
import statistics
from typing import List, Dict, Any, Tuple
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

try:
    import requests
except ImportError:
    requests = None


class StressTestResult:
    """Container for stress test results with ramp-up tracking"""
    def __init__(self):
        self.results_by_load: Dict[int, List[Dict[str, Any]]] = {}
        
    def add_result(self, concurrent_users: int, duration: float, success: bool, error: str = None):
        if concurrent_users not in self.results_by_load:
            self.results_by_load[concurrent_users] = []
        
        self.results_by_load[concurrent_users].append({
            'duration': duration,
            'success': success,
            'error': error
        })
    
    def get_breaking_point(self, failure_threshold: float = 0.1) -> Tuple[int, Dict[str, Any]]:
        """
        Find the concurrent user load where failure rate exceeds threshold
        Returns: (concurrent_users, stats) or (None, None) if no breaking point found
        """
        for concurrent_users in sorted(self.results_by_load.keys()):
            results = self.results_by_load[concurrent_users]
            successes = sum(1 for r in results if r['success'])
            failure_rate = 1 - (successes / len(results))
            
            if failure_rate >= failure_threshold:
                stats = self._calculate_stats(results)
                stats['failure_rate'] = failure_rate
                stats['concurrent_users'] = concurrent_users
                return concurrent_users, stats
        
        return None, None
    
    def get_all_statistics(self) -> Dict[int, Dict[str, Any]]:
        """Get statistics for all load levels"""
        all_stats = {}
        for concurrent_users, results in self.results_by_load.items():
            stats = self._calculate_stats(results)
            stats['concurrent_users'] = concurrent_users
            all_stats[concurrent_users] = stats
        return all_stats
    
    def _calculate_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics from results"""
        successes = [r for r in results if r['success']]
        response_times = [r['duration'] for r in successes]
        
        if not response_times:
            return {
                'success_rate': 0,
                'avg_response_time': 0,
                'max_response_time': 0,
                'total_requests': len(results),
                'errors': len(results)
            }
        
        return {
            'success_rate': (len(successes) / len(results)) * 100,
            'avg_response_time': statistics.mean(response_times),
            'median_response_time': statistics.median(response_times),
            'max_response_time': max(response_times),
            'min_response_time': min(response_times),
            'total_requests': len(results),
            'successful_requests': len(successes),
            'failed_requests': len(results) - len(successes)
        }


def make_request(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Make HTTP request and measure response time"""
    if not requests:
        return {
            'success': False,
            'duration': 0,
            'error': 'requests library not installed'
        }
    
    start_time = time.time()
    try:
        response = requests.get(url, timeout=timeout)
        duration = time.time() - start_time
        success = response.status_code < 400
        
        return {
            'success': success,
            'duration': duration,
            'error': None if success else f"HTTP {response.status_code}"
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            'success': False,
            'duration': duration,
            'error': str(e)
        }


@pytest.fixture(scope='module')
def base_url():
    """Base URL for testing (configurable via environment)"""
    return os.getenv('TEST_BASE_URL', 'http://localhost:5000')


@pytest.mark.stress
@pytest.mark.skipif(requests is None, reason="requests library not installed")
class TestStressRampUp:
    """Stress tests that ramp up load to find breaking points"""
    
    def test_health_endpoint_stress(self, base_url):
        """
        Test: Gradually increase load on health endpoint until failures occur
        Ramps from 10 to 500 concurrent users
        """
        results = StressTestResult()
        load_levels = [10, 25, 50, 100, 200, 300, 500]
        requests_per_level = 50
        
        print("\n--- Health Endpoint Stress Test ---")
        print("Ramping up concurrent users to find breaking point...\n")
        
        for concurrent_users in load_levels:
            print(f"Testing with {concurrent_users} concurrent users...")
            
            def worker():
                return make_request(f"{base_url}/api/health", timeout=10)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [executor.submit(worker) for _ in range(requests_per_level)]
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.add_result(
                        concurrent_users=concurrent_users,
                        duration=result['duration'],
                        success=result['success'],
                        error=result['error']
                    )
            
            # Check results for this level
            level_stats = results.get_all_statistics()[concurrent_users]
            print(f"  Success Rate: {level_stats['success_rate']:.2f}%")
            print(f"  Avg Response Time: {level_stats['avg_response_time']:.3f}s")
            print(f"  Failed Requests: {level_stats['failed_requests']}\n")
            
            # Stop if we hit breaking point
            if level_stats['success_rate'] < 90:
                print(f"Breaking point reached at {concurrent_users} concurrent users")
                break
        
        # Analyze results
        breaking_point, bp_stats = results.get_breaking_point(failure_threshold=0.10)
        
        if breaking_point:
            print(f"\n--- Breaking Point Analysis ---")
            print(f"System breaks at: {breaking_point} concurrent users")
            print(f"Success rate at breaking point: {bp_stats['success_rate']:.2f}%")
            print(f"Average response time: {bp_stats['avg_response_time']:.3f}s")
        else:
            print(f"\n--- Stress Test Results ---")
            print(f"No breaking point found up to {max(load_levels)} concurrent users")
            print(f"System handled all loads successfully")
        
        # Assertions
        assert breaking_point is None or breaking_point >= 50, \
            f"System breaks too early at {breaking_point} users (minimum acceptable: 50)"
    
    def test_models_endpoint_stress(self, base_url):
        """
        Test: Stress test models endpoint (requires model loading)
        Ramps from 5 to 100 concurrent users
        """
        results = StressTestResult()
        load_levels = [5, 10, 20, 50, 100]
        requests_per_level = 30
        
        print("\n--- Models Endpoint Stress Test ---")
        print("Ramping up concurrent users...\n")
        
        for concurrent_users in load_levels:
            print(f"Testing with {concurrent_users} concurrent users...")
            
            def worker():
                return make_request(f"{base_url}/api/models", timeout=15)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [executor.submit(worker) for _ in range(requests_per_level)]
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.add_result(
                        concurrent_users=concurrent_users,
                        duration=result['duration'],
                        success=result['success'],
                        error=result['error']
                    )
            
            level_stats = results.get_all_statistics()[concurrent_users]
            print(f"  Success Rate: {level_stats['success_rate']:.2f}%")
            print(f"  Avg Response Time: {level_stats['avg_response_time']:.3f}s\n")
            
            if level_stats['success_rate'] < 90:
                break
        
        breaking_point, bp_stats = results.get_breaking_point(failure_threshold=0.10)
        
        if breaking_point:
            print(f"\n--- Breaking Point: {breaking_point} concurrent users ---")
        else:
            print(f"\n--- No breaking point found ---")
    
    def test_sustained_load_stress(self, base_url):
        """
        Test: Sustained high load over time
        Maintains 50 concurrent users for 60 seconds
        """
        concurrent_users = 50
        duration_seconds = 60
        results = StressTestResult()
        
        print(f"\n--- Sustained Load Stress Test ---")
        print(f"Maintaining {concurrent_users} concurrent users for {duration_seconds} seconds...\n")
        
        start_time = time.time()
        request_count = 0
        
        def worker():
            return make_request(f"{base_url}/api/health", timeout=10)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            while time.time() - start_time < duration_seconds:
                futures = [executor.submit(worker) for _ in range(concurrent_users)]
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.add_result(
                        concurrent_users=concurrent_users,
                        duration=result['duration'],
                        success=result['success'],
                        error=result['error']
                    )
                    request_count += 1
                
                # Brief pause between waves
                time.sleep(0.5)
        
        stats = results.get_all_statistics()[concurrent_users]
        
        print(f"Total Requests: {request_count}")
        print(f"Success Rate: {stats['success_rate']:.2f}%")
        print(f"Avg Response Time: {stats['avg_response_time']:.3f}s")
        print(f"Max Response Time: {stats['max_response_time']:.3f}s")
        
        # Assertions
        assert stats['success_rate'] >= 95, \
            f"Success rate {stats['success_rate']:.2f}% below 95% under sustained load"
        assert stats['avg_response_time'] < 1.0, \
            f"Average response time {stats['avg_response_time']:.3f}s exceeds 1s under sustained load"


@pytest.mark.stress
@pytest.mark.skipif(requests is None, reason="requests library not installed")
class TestResourceStress:
    """Test system resource limits and recovery"""
    
    def test_memory_stress_recovery(self, base_url):
        """
        Test: System recovers after memory-intensive operations
        Sends burst of requests then checks system stability
        """
        print("\n--- Memory Stress Recovery Test ---")
        
        # Burst phase: Heavy load
        burst_size = 200
        print(f"Phase 1: Sending burst of {burst_size} requests...")
        
        def worker():
            return make_request(f"{base_url}/api/health", timeout=10)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            burst_futures = [executor.submit(worker) for _ in range(burst_size)]
            burst_results = [f.result() for f in concurrent.futures.as_completed(burst_futures)]
        
        burst_successes = sum(1 for r in burst_results if r['success'])
        print(f"Burst complete: {burst_successes}/{burst_size} successful")
        
        # Recovery phase: Check system stability
        time.sleep(5)  # Allow system to recover
        
        print("Phase 2: Testing system recovery...")
        recovery_size = 50
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            recovery_futures = [executor.submit(worker) for _ in range(recovery_size)]
            recovery_results = [f.result() for f in concurrent.futures.as_completed(recovery_futures)]
        
        recovery_successes = sum(1 for r in recovery_results if r['success'])
        recovery_rate = (recovery_successes / recovery_size) * 100
        
        print(f"Recovery test: {recovery_successes}/{recovery_size} successful ({recovery_rate:.2f}%)")
        
        # System should recover to >95% success rate
        assert recovery_rate >= 95, \
            f"System failed to recover: {recovery_rate:.2f}% success rate"


if __name__ == '__main__':
    """
    Run stress tests:
    pytest test_stress.py -v -s
    
    Configure via environment variables:
    export TEST_BASE_URL=http://localhost:5000
    """
    pytest.main([__file__, '-v', '-s'])
