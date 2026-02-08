"""
=============================================================================
API CONNECTION HEALTH CHECKER - Comprehensive Endpoint Monitoring
=============================================================================

Monitors all API endpoints for health, performance, and availability.
Provides real-time status dashboard and alerting.

Features:
- Endpoint availability monitoring
- Response time tracking
- Error rate monitoring
- Dependency health checks
- Historical metrics
- Automated health reports

Usage:
    from web.backend.api_health_checker import APIHealthChecker
    
    checker = APIHealthChecker()
    status = checker.check_all_endpoints()
    report = checker.generate_health_report()

=============================================================================
"""

import os
import time
import logging
import requests
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
import json

logger = logging.getLogger(__name__)

# Configuration
CHECK_INTERVAL = int(os.getenv('API_HEALTH_CHECK_INTERVAL', '60'))  # seconds
HISTORY_SIZE = int(os.getenv('API_HEALTH_HISTORY_SIZE', '1000'))
RESPONSE_TIME_THRESHOLD = float(os.getenv('API_RESPONSE_TIME_THRESHOLD', '2.0'))  # seconds
ERROR_RATE_THRESHOLD = float(os.getenv('API_ERROR_RATE_THRESHOLD', '0.05'))  # 5%


@dataclass
class EndpointCheck:
    """Result of a single endpoint health check."""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    timestamp: float
    error_message: Optional[str] = None
    response_size: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class EndpointMetrics:
    """Aggregated metrics for an endpoint."""
    endpoint: str
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = float('inf')
    max_response_time_ms: float = 0.0
    error_rate: float = 0.0
    last_check_time: Optional[float] = None
    last_status: str = 'unknown'  # 'healthy', 'degraded', 'down'
    
    def update(self, check: EndpointCheck):
        """Update metrics with new check result."""
        self.total_checks += 1
        self.last_check_time = check.timestamp
        
        if check.success:
            self.successful_checks += 1
            self.last_status = 'healthy'
        else:
            self.failed_checks += 1
            self.last_status = 'degraded' if check.status_code < 500 else 'down'
        
        # Update response times
        if check.response_time_ms > 0:
            self.min_response_time_ms = min(self.min_response_time_ms, check.response_time_ms)
            self.max_response_time_ms = max(self.max_response_time_ms, check.response_time_ms)
            
            # Rolling average
            prev_avg = self.avg_response_time_ms
            self.avg_response_time_ms = (prev_avg * (self.total_checks - 1) + check.response_time_ms) / self.total_checks
        
        # Calculate error rate
        self.error_rate = self.failed_checks / self.total_checks if self.total_checks > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'endpoint': self.endpoint,
            'total_checks': self.total_checks,
            'successful_checks': self.successful_checks,
            'failed_checks': self.failed_checks,
            'avg_response_time_ms': round(self.avg_response_time_ms, 2),
            'min_response_time_ms': round(self.min_response_time_ms, 2) if self.min_response_time_ms != float('inf') else None,
            'max_response_time_ms': round(self.max_response_time_ms, 2),
            'error_rate': round(self.error_rate, 4),
            'last_check_time': self.last_check_time,
            'last_status': self.last_status
        }


class APIHealthChecker:
    """
    Comprehensive API health monitoring system.
    
    Monitors all registered API endpoints for:
    - Availability
    - Response times
    - Error rates
    - Status codes
    """
    
    # Core endpoints to monitor
    ENDPOINTS_TO_CHECK = [
        ('GET', '/api', 'API root'),
        ('GET', '/api/health', 'Health check'),
        ('GET', '/api/ready', 'Readiness check'),
        ('GET', '/api/version', 'Version info'),
        ('GET', '/api/models', 'Models list'),
        ('GET', '/api/database/health', 'Database health'),
    ]
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API health checker.
        
        Args:
            base_url: Base URL for API (defaults to localhost:5000)
        """
        self.base_url = base_url or os.getenv('API_BASE_URL', 'http://localhost:5000')
        self.is_running = False
        self.monitor_thread = None
        
        # Metrics storage
        self.endpoint_metrics: Dict[str, EndpointMetrics] = {}
        self.check_history: deque = deque(maxlen=HISTORY_SIZE)
        self.issues_log: deque = deque(maxlen=100)
        
        self._lock = threading.Lock()
        
        # Initialize metrics for all endpoints
        for method, path, description in self.ENDPOINTS_TO_CHECK:
            key = f"{method} {path}"
            self.endpoint_metrics[key] = EndpointMetrics(endpoint=key)
    
    def start_monitoring(self):
        """Start background monitoring thread."""
        if self.is_running:
            logger.warning("API health monitoring already running")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name='APIHealthMonitor'
        )
        self.monitor_thread.start()
        logger.info(f"API health monitoring started for {self.base_url}")
    
    def stop_monitoring(self):
        """Stop monitoring thread."""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("API health monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                self.check_all_endpoints()
                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Monitoring error: {e}", exc_info=True)
                time.sleep(CHECK_INTERVAL)
    
    def check_endpoint(self, method: str, path: str, timeout: float = 5.0) -> EndpointCheck:
        """
        Check a single endpoint.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Endpoint path
            timeout: Request timeout in seconds
            
        Returns:
            EndpointCheck result
        """
        url = f"{self.base_url}{path}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json={}, timeout=timeout)
            else:
                response = requests.request(method, url, timeout=timeout)
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            return EndpointCheck(
                endpoint=f"{method} {path}",
                method=method,
                status_code=response.status_code,
                response_time_ms=response_time,
                success=200 <= response.status_code < 400,
                timestamp=time.time(),
                response_size=len(response.content) if response.content else 0
            )
            
        except requests.exceptions.Timeout:
            response_time = timeout * 1000
            return EndpointCheck(
                endpoint=f"{method} {path}",
                method=method,
                status_code=0,
                response_time_ms=response_time,
                success=False,
                timestamp=time.time(),
                error_message="Request timeout"
            )
            
        except requests.exceptions.ConnectionError as e:
            response_time = (time.time() - start_time) * 1000
            return EndpointCheck(
                endpoint=f"{method} {path}",
                method=method,
                status_code=0,
                response_time_ms=response_time,
                success=False,
                timestamp=time.time(),
                error_message=f"Connection error: {str(e)[:100]}"
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return EndpointCheck(
                endpoint=f"{method} {path}",
                method=method,
                status_code=0,
                response_time_ms=response_time,
                success=False,
                timestamp=time.time(),
                error_message=str(e)[:200]
            )
    
    def check_all_endpoints(self) -> Dict[str, EndpointCheck]:
        """
        Check all registered endpoints.
        
        Returns:
            Dictionary mapping endpoint key to check result
        """
        results = {}
        
        for method, path, description in self.ENDPOINTS_TO_CHECK:
            key = f"{method} {path}"
            check = self.check_endpoint(method, path)
            results[key] = check
            
            # Update metrics
            with self._lock:
                if key in self.endpoint_metrics:
                    self.endpoint_metrics[key].update(check)
                
                self.check_history.append(check)
                
                # Log issues
                if not check.success:
                    issue = {
                        'timestamp': check.timestamp,
                        'endpoint': key,
                        'status_code': check.status_code,
                        'error': check.error_message
                    }
                    self.issues_log.append(issue)
                    logger.warning(f"Endpoint {key} failed: {check.error_message}")
                elif check.response_time_ms > RESPONSE_TIME_THRESHOLD * 1000:
                    issue = {
                        'timestamp': check.timestamp,
                        'endpoint': key,
                        'type': 'slow_response',
                        'response_time_ms': check.response_time_ms
                    }
                    self.issues_log.append(issue)
                    logger.warning(f"Endpoint {key} slow: {check.response_time_ms:.0f}ms")
        
        return results
    
    def get_endpoint_metrics(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metrics for endpoint(s).
        
        Args:
            endpoint: Specific endpoint key, or None for all
            
        Returns:
            Metrics dictionary
        """
        with self._lock:
            if endpoint:
                metrics = self.endpoint_metrics.get(endpoint)
                return metrics.to_dict() if metrics else {}
            else:
                return {
                    key: metrics.to_dict()
                    for key, metrics in self.endpoint_metrics.items()
                }
    
    def get_overall_status(self) -> Dict[str, Any]:
        """
        Get overall API health status.
        
        Returns:
            Status dictionary with aggregated metrics
        """
        with self._lock:
            total_endpoints = len(self.endpoint_metrics)
            healthy_count = sum(
                1 for m in self.endpoint_metrics.values()
                if m.last_status == 'healthy'
            )
            degraded_count = sum(
                1 for m in self.endpoint_metrics.values()
                if m.last_status == 'degraded'
            )
            down_count = sum(
                1 for m in self.endpoint_metrics.values()
                if m.last_status == 'down'
            )
            
            # Overall status
            if down_count > 0 or healthy_count == 0:
                overall_status = 'critical'
            elif degraded_count > 0:
                overall_status = 'warning'
            else:
                overall_status = 'healthy'
            
            # Calculate average response time across all endpoints
            avg_response_times = [
                m.avg_response_time_ms
                for m in self.endpoint_metrics.values()
                if m.avg_response_time_ms > 0
            ]
            overall_avg_response = (
                sum(avg_response_times) / len(avg_response_times)
                if avg_response_times else 0
            )
            
            # Calculate overall error rate
            total_checks = sum(m.total_checks for m in self.endpoint_metrics.values())
            total_failures = sum(m.failed_checks for m in self.endpoint_metrics.values())
            overall_error_rate = total_failures / total_checks if total_checks > 0 else 0
            
            return {
                'overall_status': overall_status,
                'total_endpoints': total_endpoints,
                'healthy_endpoints': healthy_count,
                'degraded_endpoints': degraded_count,
                'down_endpoints': down_count,
                'avg_response_time_ms': round(overall_avg_response, 2),
                'overall_error_rate': round(overall_error_rate, 4),
                'total_checks': total_checks,
                'last_check_time': max(
                    (m.last_check_time for m in self.endpoint_metrics.values() if m.last_check_time),
                    default=None
                )
            }
    
    def get_recent_issues(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent health issues.
        
        Args:
            limit: Maximum number of issues to return
            
        Returns:
            List of recent issues
        """
        with self._lock:
            return list(self.issues_log)[-limit:]
    
    def generate_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive health report.
        
        Returns:
            Complete health report dictionary
        """
        overall_status = self.get_overall_status()
        endpoint_metrics = self.get_endpoint_metrics()
        recent_issues = self.get_recent_issues()
        
        # Identify problematic endpoints
        problematic = [
            {
                'endpoint': key,
                'status': metrics['last_status'],
                'error_rate': metrics['error_rate'],
                'avg_response_time_ms': metrics['avg_response_time_ms']
            }
            for key, metrics in endpoint_metrics.items()
            if metrics['last_status'] != 'healthy' or
               metrics['error_rate'] > ERROR_RATE_THRESHOLD or
               metrics['avg_response_time_ms'] > RESPONSE_TIME_THRESHOLD * 1000
        ]
        
        return {
            'generated_at': datetime.now().isoformat(),
            'overall_status': overall_status,
            'endpoint_metrics': endpoint_metrics,
            'problematic_endpoints': problematic,
            'recent_issues': recent_issues,
            'monitoring_config': {
                'base_url': self.base_url,
                'check_interval': CHECK_INTERVAL,
                'response_time_threshold_ms': RESPONSE_TIME_THRESHOLD * 1000,
                'error_rate_threshold': ERROR_RATE_THRESHOLD
            }
        }
    
    def export_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        overall = self.get_overall_status()
        metrics_lines = [
            '# HELP api_endpoints_total Total number of API endpoints monitored',
            '# TYPE api_endpoints_total gauge',
            f'api_endpoints_total {overall["total_endpoints"]}',
            '',
            '# HELP api_endpoints_healthy Number of healthy API endpoints',
            '# TYPE api_endpoints_healthy gauge',
            f'api_endpoints_healthy {overall["healthy_endpoints"]}',
            '',
            '# HELP api_response_time_ms Average API response time in milliseconds',
            '# TYPE api_response_time_ms gauge',
            f'api_response_time_ms {overall["avg_response_time_ms"]}',
            '',
            '# HELP api_error_rate Overall API error rate',
            '# TYPE api_error_rate gauge',
            f'api_error_rate {overall["overall_error_rate"]}',
            ''
        ]
        
        # Per-endpoint metrics
        with self._lock:
            for key, metrics in self.endpoint_metrics.items():
                safe_key = key.replace(' ', '_').replace('/', '_')
                metrics_lines.extend([
                    f'api_endpoint_response_time_ms{{endpoint="{key}"}} {metrics.avg_response_time_ms:.2f}',
                    f'api_endpoint_error_rate{{endpoint="{key}"}} {metrics.error_rate:.4f}',
                ])
        
        return '\n'.join(metrics_lines)


# Global checker instance
_checker_instance = None
_checker_lock = threading.Lock()


def get_api_health_checker(base_url: Optional[str] = None) -> APIHealthChecker:
    """Get or create global API health checker instance."""
    global _checker_instance
    
    with _checker_lock:
        if _checker_instance is None:
            _checker_instance = APIHealthChecker(base_url)
        return _checker_instance


def start_api_monitoring(base_url: Optional[str] = None):
    """Start global API health monitoring."""
    checker = get_api_health_checker(base_url)
    checker.start_monitoring()


def stop_api_monitoring():
    """Stop global API health monitoring."""
    if _checker_instance:
        _checker_instance.stop_monitoring()


def get_api_health_status() -> Dict[str, Any]:
    """Get current API health status."""
    checker = get_api_health_checker()
    return checker.get_overall_status()


__all__ = [
    'APIHealthChecker',
    'EndpointCheck',
    'EndpointMetrics',
    'get_api_health_checker',
    'start_api_monitoring',
    'stop_api_monitoring',
    'get_api_health_status',
]
