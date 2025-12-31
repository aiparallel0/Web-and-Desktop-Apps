"""
=============================================================================
CUSTOM METRICS - Receipt Extraction Metrics
=============================================================================

Defines custom metrics for monitoring receipt extraction performance.

Metrics:
- receipt.extractions.total: Total number of extractions
- receipt.extraction.duration: Processing time histogram
- receipt.extraction.errors: Error count
- receipt.extraction.confidence: Confidence score histogram

=============================================================================
"""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache

from .otel_config import get_meter

logger = logging.getLogger(__name__)


# =============================================================================
# METRICS DEFINITIONS
# =============================================================================

@lru_cache(maxsize=1)
def _get_metrics():
    """Get or create all metrics instances."""
    try:
        meter = get_meter()
        
        return {
            'extractions_total': meter.create_counter(
                "receipt.extractions.total",
                description="Total number of receipt extractions",
                unit="1"
            ),
            'extraction_errors': meter.create_counter(
                "receipt.extraction.errors",
                description="Number of extraction errors",
                unit="1"
            ),
            'extraction_duration': meter.create_histogram(
                "receipt.extraction.duration",
                description="Receipt extraction processing time",
                unit="s"
            ),
            'confidence_score': meter.create_histogram(
                "receipt.extraction.confidence",
                description="Model confidence scores",
                unit="1"
            ),
            'api_requests': meter.create_counter(
                "api.requests.total",
                description="Total API requests",
                unit="1"
            ),
            'api_errors': meter.create_counter(
                "api.errors.total",
                description="Total API errors",
                unit="1"
            ),
            'api_latency': meter.create_histogram(
                "api.latency",
                description="API request latency",
                unit="ms"
            ),
            'active_users': meter.create_up_down_counter(
                "users.active",
                description="Number of active users",
                unit="1"
            ),
            'storage_bytes': meter.create_up_down_counter(
                "storage.bytes",
                description="Total storage used",
                unit="By"
            )
        }
    except Exception as e:
        logger.error(f"Error creating metrics: {e}")
        # Return empty dict - metrics will fail silently
        return {}


# =============================================================================
# METRICS TRACKING FUNCTIONS
# =============================================================================

@dataclass
class MetricsSnapshot:
    """In-memory metrics snapshot for reporting."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    extractions_total: int = 0
    extractions_success: int = 0
    extractions_failed: int = 0
    avg_processing_time: float = 0.0
    avg_confidence: float = 0.0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    extractions_by_model: Dict[str, int] = field(default_factory=dict)


# In-memory metrics store (for development/debugging)
_metrics_store = MetricsSnapshot()
_processing_times = []
_confidence_scores = []


def track_extraction(
    model_id: str,
    duration: float,
    success: bool,
    confidence: float = None,
    items_extracted: int = 0,
    user_id: str = None
):
    """
    Track a receipt extraction operation.
    
    Args:
        model_id: Model used for extraction
        duration: Processing time in seconds
        success: Whether extraction succeeded
        confidence: Model confidence score (0-1)
        items_extracted: Number of items extracted
        user_id: User ID (for per-user metrics)
    """
    try:
        global _metrics_store, _processing_times, _confidence_scores
        
        metrics = _get_metrics()
        
        # Common attributes
        attributes = {
            "model": model_id,
            "success": str(success)
        }
        
        # Track total extractions (only if metrics available)
        if 'extractions_total' in metrics:
            metrics['extractions_total'].add(1, attributes)
        _metrics_store.extractions_total += 1
        
        if success:
            _metrics_store.extractions_success += 1
        else:
            _metrics_store.extractions_failed += 1
        
        # Track duration
        if 'extraction_duration' in metrics:
            metrics['extraction_duration'].record(duration, attributes)
        _processing_times.append(duration)
        
        # Keep only last 1000 samples
        if len(_processing_times) > 1000:
            _processing_times = _processing_times[-1000:]
        
        _metrics_store.avg_processing_time = sum(_processing_times) / len(_processing_times)
        
        # Track confidence if provided
        if confidence is not None:
            if 'confidence_score' in metrics:
                metrics['confidence_score'].record(confidence, {"model": model_id})
            _confidence_scores.append(confidence)
            
            if len(_confidence_scores) > 1000:
                _confidence_scores = _confidence_scores[-1000:]
            
            _metrics_store.avg_confidence = sum(_confidence_scores) / len(_confidence_scores)
        
        # Track by model
        _metrics_store.extractions_by_model[model_id] = \
            _metrics_store.extractions_by_model.get(model_id, 0) + 1
        
        logger.debug(
            f"Extraction tracked: model={model_id}, duration={duration:.2f}s, "
            f"success={success}, confidence={confidence}"
        )
    except Exception as e:
        # Don't let metrics tracking crash the application
        logger.warning(f"Error tracking extraction metrics: {e}")


def track_error(
    error_type: str,
    error_message: str,
    model_id: str = None,
    user_id: str = None,
    endpoint: str = None
):
    """
    Track an error event.
    
    Args:
        error_type: Type/class of error
        error_message: Error message
        model_id: Model ID if applicable
        user_id: User ID if applicable
        endpoint: API endpoint if applicable
    """
    try:
        global _metrics_store
        
        metrics = _get_metrics()
        
        attributes = {
            "error_type": error_type
        }
        
        if model_id:
            attributes["model"] = model_id
        
        if endpoint:
            attributes["endpoint"] = endpoint
        
        if 'extraction_errors' in metrics:
            metrics['extraction_errors'].add(1, attributes)
        
        # Track error types
        _metrics_store.errors_by_type[error_type] = \
            _metrics_store.errors_by_type.get(error_type, 0) + 1
        
        logger.warning(
            f"Error tracked: type={error_type}, message={error_message}, model={model_id}"
        )
    except Exception as e:
        # Don't let error tracking itself crash the application
        logger.warning(f"Error tracking error metrics: {e}")


def track_api_request(
    endpoint: str,
    method: str,
    status_code: int,
    latency_ms: float,
    user_id: str = None
):
    """
    Track an API request.
    
    Args:
        endpoint: API endpoint path
        method: HTTP method
        status_code: Response status code
        latency_ms: Request latency in milliseconds
        user_id: User ID if authenticated
    """
    try:
        metrics = _get_metrics()
        
        attributes = {
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code)
        }
        
        if 'api_requests' in metrics:
            metrics['api_requests'].add(1, attributes)
        if 'api_latency' in metrics:
            metrics['api_latency'].record(latency_ms, attributes)
        
        if status_code >= 400 and 'api_errors' in metrics:
            metrics['api_errors'].add(1, attributes)
    except Exception as e:
        logger.warning(f"Error tracking API request metrics: {e}")


def track_user_session(user_id: str, action: str):
    """
    Track user session events.
    
    Args:
        user_id: User ID
        action: Action type (login, logout)
    """
    try:
        metrics = _get_metrics()
        
        if 'active_users' not in metrics:
            return
        
        if action == 'login':
            metrics['active_users'].add(1, {"user_id": user_id})
        elif action == 'logout':
            metrics['active_users'].add(-1, {"user_id": user_id})
    except Exception as e:
        logger.warning(f"Error tracking user session metrics: {e}")


def track_storage_usage(bytes_delta: int, user_id: str = None):
    """
    Track storage usage changes.
    
    Args:
        bytes_delta: Change in bytes (positive = added, negative = removed)
        user_id: User ID
    """
    try:
        metrics = _get_metrics()
        
        if 'storage_bytes' not in metrics:
            return
        
        attributes = {}
        if user_id:
            attributes["user_id"] = user_id
        
        metrics['storage_bytes'].add(bytes_delta, attributes)
    except Exception as e:
        logger.warning(f"Error tracking storage usage metrics: {e}")


def get_metrics_summary() -> Dict[str, Any]:
    """
    Get a summary of current metrics.
    
    Returns:
        Dictionary with metrics summary
    """
    try:
        global _metrics_store
        
        return {
            'timestamp': _metrics_store.timestamp.isoformat(),
            'extractions': {
                'total': _metrics_store.extractions_total,
                'success': _metrics_store.extractions_success,
                'failed': _metrics_store.extractions_failed,
                'success_rate': (
                    _metrics_store.extractions_success / _metrics_store.extractions_total
                    if _metrics_store.extractions_total > 0 else 0
                ) * 100
            },
            'performance': {
                'avg_processing_time_seconds': round(_metrics_store.avg_processing_time, 3),
                'avg_confidence': round(_metrics_store.avg_confidence, 3)
            },
            'errors_by_type': _metrics_store.errors_by_type,
            'extractions_by_model': _metrics_store.extractions_by_model
        }
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }


def reset_metrics():
    """Reset in-memory metrics store. For testing purposes."""
    global _metrics_store, _processing_times, _confidence_scores
    
    _metrics_store = MetricsSnapshot()
    _processing_times = []
    _confidence_scores = []
