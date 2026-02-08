"""
=============================================================================
DATABASE CONNECTION HEALTH MONITOR - Production Monitoring System
=============================================================================

Comprehensive database health monitoring with:
- Real-time connection pool metrics
- Query performance tracking
- Connection leak detection
- Automatic alerting
- Historical metrics storage
- Dashboard integration

Usage:
    from web.backend.database_health_monitor import DatabaseHealthMonitor
    
    monitor = DatabaseHealthMonitor()
    monitor.start_monitoring()
    
    # Get current metrics
    metrics = monitor.get_current_metrics()
    
    # Check for issues
    issues = monitor.check_health_issues()

=============================================================================
"""

import os
import time
import logging
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field, asdict
import json

from sqlalchemy import text, event
from sqlalchemy.exc import OperationalError, TimeoutError as SQLAlchemyTimeoutError

logger = logging.getLogger(__name__)

# Monitoring configuration
MONITOR_INTERVAL = int(os.getenv('DB_MONITOR_INTERVAL', '30'))  # seconds
METRICS_HISTORY_SIZE = int(os.getenv('DB_METRICS_HISTORY_SIZE', '1000'))
ALERT_THRESHOLD_POOL_UTILIZATION = float(os.getenv('DB_ALERT_POOL_UTIL', '0.9'))
ALERT_THRESHOLD_QUERY_LATENCY = float(os.getenv('DB_ALERT_LATENCY', '1.0'))  # seconds


@dataclass
class ConnectionMetrics:
    """Metrics for a single monitoring interval."""
    timestamp: float
    pool_size: int
    connections_checked_out: int
    connections_available: int
    overflow_connections: int
    pool_utilization: float
    query_latency_ms: float
    queries_per_second: float
    active_connections: int
    idle_connections: int
    errors_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @property
    def is_healthy(self) -> bool:
        """Check if metrics indicate healthy state."""
        return (
            self.pool_utilization < 0.9 and
            self.query_latency_ms < 1000 and
            self.errors_count == 0
        )


@dataclass
class HealthIssue:
    """Represents a detected health issue."""
    severity: str  # 'critical', 'warning', 'info'
    category: str  # 'pool', 'performance', 'connections', 'errors'
    message: str
    detected_at: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class DatabaseHealthMonitor:
    """
    Production-grade database health monitoring system.
    
    Features:
    - Real-time metrics collection
    - Historical data tracking
    - Issue detection and alerting
    - Performance analysis
    """
    
    def __init__(self):
        """Initialize health monitor."""
        self.is_running = False
        self.monitor_thread = None
        self.metrics_history: deque = deque(maxlen=METRICS_HISTORY_SIZE)
        self.issues_history: deque = deque(maxlen=100)
        self.last_check_time = None
        self.total_queries_tracked = 0
        self.error_counts = {
            'connection_errors': 0,
            'timeout_errors': 0,
            'query_errors': 0,
            'pool_exhausted': 0
        }
        self._lock = threading.Lock()
    
    def start_monitoring(self):
        """Start background monitoring thread."""
        if self.is_running:
            logger.warning("Monitor already running")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name='DatabaseHealthMonitor'
        )
        self.monitor_thread.start()
        logger.info("Database health monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring thread."""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Database health monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                metrics = self._collect_metrics()
                if metrics:
                    with self._lock:
                        self.metrics_history.append(metrics)
                    
                    # Check for issues
                    issues = self._analyze_metrics(metrics)
                    if issues:
                        with self._lock:
                            self.issues_history.extend(issues)
                        
                        # Log issues
                        for issue in issues:
                            if issue.severity == 'critical':
                                logger.error(f"[DATABASE HEALTH] {issue.message}")
                            elif issue.severity == 'warning':
                                logger.warning(f"[DATABASE HEALTH] {issue.message}")
                            else:
                                logger.info(f"[DATABASE HEALTH] {issue.message}")
                
                time.sleep(MONITOR_INTERVAL)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}", exc_info=True)
                time.sleep(MONITOR_INTERVAL)
    
    def _collect_metrics(self) -> Optional[ConnectionMetrics]:
        """Collect current database metrics."""
        try:
            from web.backend.database import get_engine
            
            engine = get_engine()
            pool = engine.pool
            
            # Get pool statistics
            pool_size = getattr(pool, 'size', lambda: 0)()
            checked_out = getattr(pool, 'checkedout', lambda: 0)()
            overflow = getattr(pool, 'overflow', lambda: 0)()
            
            available = max(0, pool_size - checked_out)
            utilization = checked_out / pool_size if pool_size > 0 else 0.0
            
            # Measure query latency
            start_time = time.time()
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                query_latency = (time.time() - start_time) * 1000  # ms
                error_count = 0
            except Exception as e:
                query_latency = -1
                error_count = 1
                logger.error(f"Health check query failed: {e}")
            
            # Calculate queries per second (estimate)
            qps = 0.0
            if self.last_check_time:
                elapsed = time.time() - self.last_check_time
                if elapsed > 0:
                    qps = self.total_queries_tracked / elapsed
            
            self.last_check_time = time.time()
            
            return ConnectionMetrics(
                timestamp=time.time(),
                pool_size=pool_size,
                connections_checked_out=checked_out,
                connections_available=available,
                overflow_connections=overflow,
                pool_utilization=utilization,
                query_latency_ms=query_latency,
                queries_per_second=qps,
                active_connections=checked_out,
                idle_connections=available,
                errors_count=error_count
            )
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return None
    
    def _analyze_metrics(self, metrics: ConnectionMetrics) -> List[HealthIssue]:
        """Analyze metrics and detect issues."""
        issues = []
        
        # Check pool utilization
        if metrics.pool_utilization >= ALERT_THRESHOLD_POOL_UTILIZATION:
            issues.append(HealthIssue(
                severity='critical' if metrics.pool_utilization >= 0.95 else 'warning',
                category='pool',
                message=f"High pool utilization: {metrics.pool_utilization:.1%} "
                       f"({metrics.connections_checked_out}/{metrics.pool_size} connections)",
                detected_at=metrics.timestamp,
                metrics={'utilization': metrics.pool_utilization}
            ))
        
        # Check query latency
        if metrics.query_latency_ms > ALERT_THRESHOLD_QUERY_LATENCY * 1000:
            issues.append(HealthIssue(
                severity='warning',
                category='performance',
                message=f"High query latency: {metrics.query_latency_ms:.1f}ms",
                detected_at=metrics.timestamp,
                metrics={'latency_ms': metrics.query_latency_ms}
            ))
        
        # Check overflow connections
        if metrics.overflow_connections > 0:
            issues.append(HealthIssue(
                severity='warning',
                category='pool',
                message=f"Pool overflow: {metrics.overflow_connections} extra connections",
                detected_at=metrics.timestamp,
                metrics={'overflow': metrics.overflow_connections}
            ))
        
        # Check errors
        if metrics.errors_count > 0:
            issues.append(HealthIssue(
                severity='critical',
                category='errors',
                message="Database connectivity errors detected",
                detected_at=metrics.timestamp,
                metrics={'error_count': metrics.errors_count}
            ))
        
        return issues
    
    def get_current_metrics(self) -> Optional[Dict[str, Any]]:
        """Get most recent metrics."""
        with self._lock:
            if not self.metrics_history:
                return None
            return self.metrics_history[-1].to_dict()
    
    def get_metrics_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical metrics."""
        with self._lock:
            metrics = list(self.metrics_history)[-limit:]
            return [m.to_dict() for m in metrics]
    
    def get_recent_issues(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent health issues."""
        with self._lock:
            issues = list(self.issues_history)[-limit:]
            return [i.to_dict() for i in issues]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics."""
        with self._lock:
            if not self.metrics_history:
                return {}
            
            metrics_list = list(self.metrics_history)
            
            # Calculate averages
            avg_pool_util = sum(m.pool_utilization for m in metrics_list) / len(metrics_list)
            avg_latency = sum(m.query_latency_ms for m in metrics_list) / len(metrics_list)
            avg_qps = sum(m.queries_per_second for m in metrics_list) / len(metrics_list)
            
            # Find peaks
            max_pool_util = max(m.pool_utilization for m in metrics_list)
            max_latency = max(m.query_latency_ms for m in metrics_list)
            max_qps = max(m.queries_per_second for m in metrics_list)
            
            # Count issues by severity
            issues_list = list(self.issues_history)
            critical_count = sum(1 for i in issues_list if i.severity == 'critical')
            warning_count = sum(1 for i in issues_list if i.severity == 'warning')
            
            return {
                'monitoring_duration_seconds': time.time() - (metrics_list[0].timestamp if metrics_list else time.time()),
                'metrics_collected': len(metrics_list),
                'averages': {
                    'pool_utilization': round(avg_pool_util, 3),
                    'query_latency_ms': round(avg_latency, 2),
                    'queries_per_second': round(avg_qps, 2)
                },
                'peaks': {
                    'max_pool_utilization': round(max_pool_util, 3),
                    'max_query_latency_ms': round(max_latency, 2),
                    'max_queries_per_second': round(max_qps, 2)
                },
                'issues': {
                    'total': len(issues_list),
                    'critical': critical_count,
                    'warning': warning_count,
                    'info': len(issues_list) - critical_count - warning_count
                },
                'errors': self.error_counts
            }
    
    def check_health_issues(self) -> Dict[str, Any]:
        """Check for current health issues."""
        metrics = self.get_current_metrics()
        if not metrics:
            return {
                'status': 'unknown',
                'message': 'No metrics available'
            }
        
        # Get recent issues
        recent_issues = self.get_recent_issues(limit=5)
        
        # Count critical issues in last 5 minutes
        five_min_ago = time.time() - 300
        recent_critical = [
            i for i in recent_issues
            if i['severity'] == 'critical' and i['detected_at'] > five_min_ago
        ]
        
        if recent_critical:
            return {
                'status': 'critical',
                'message': f"{len(recent_critical)} critical issue(s) detected",
                'issues': recent_critical
            }
        
        # Check current metrics
        if metrics['pool_utilization'] >= 0.9:
            return {
                'status': 'warning',
                'message': 'High pool utilization',
                'metrics': metrics
            }
        
        if metrics['query_latency_ms'] > 1000:
            return {
                'status': 'warning',
                'message': 'High query latency',
                'metrics': metrics
            }
        
        return {
            'status': 'healthy',
            'message': 'All systems operational',
            'metrics': metrics
        }
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics for external monitoring systems."""
        stats = self.get_statistics()
        
        if format == 'json':
            return json.dumps(stats, indent=2)
        elif format == 'prometheus':
            # Prometheus format
            lines = [
                f'# HELP db_pool_utilization Current database pool utilization',
                f'# TYPE db_pool_utilization gauge',
                f'db_pool_utilization {stats["averages"]["pool_utilization"]}',
                '',
                f'# HELP db_query_latency_ms Average query latency in milliseconds',
                f'# TYPE db_query_latency_ms gauge',
                f'db_query_latency_ms {stats["averages"]["query_latency_ms"]}',
                '',
                f'# HELP db_queries_per_second Queries per second',
                f'# TYPE db_queries_per_second gauge',
                f'db_queries_per_second {stats["averages"]["queries_per_second"]}',
                '',
                f'# HELP db_issues_total Total database issues detected',
                f'# TYPE db_issues_total counter',
                f'db_issues_total{{severity="critical"}} {stats["issues"]["critical"]}',
                f'db_issues_total{{severity="warning"}} {stats["issues"]["warning"]}',
            ]
            return '\n'.join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global monitor instance
_monitor_instance = None
_monitor_lock = threading.Lock()


def get_monitor() -> DatabaseHealthMonitor:
    """Get or create global monitor instance."""
    global _monitor_instance
    
    with _monitor_lock:
        if _monitor_instance is None:
            _monitor_instance = DatabaseHealthMonitor()
        return _monitor_instance


def start_monitoring():
    """Start global database monitoring."""
    monitor = get_monitor()
    monitor.start_monitoring()


def stop_monitoring():
    """Stop global database monitoring."""
    monitor = get_monitor()
    monitor.stop_monitoring()


def get_health_status() -> Dict[str, Any]:
    """Get current health status."""
    monitor = get_monitor()
    return monitor.check_health_issues()


__all__ = [
    'DatabaseHealthMonitor',
    'ConnectionMetrics',
    'HealthIssue',
    'get_monitor',
    'start_monitoring',
    'stop_monitoring',
    'get_health_status',
]
