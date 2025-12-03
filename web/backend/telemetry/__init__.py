"""
=============================================================================
TELEMETRY MODULE - OpenTelemetry Integration
=============================================================================

Provides comprehensive logging and telemetry for the application:
- OpenTelemetry tracing and metrics
- Custom metrics for receipt extraction
- Analytics tracking
- Structured JSON logging
- CEFR (Circular Exchange Framework) integration

Environment Variables:
- OTEL_EXPORTER_OTLP_ENDPOINT: OpenTelemetry collector endpoint
- OTEL_SERVICE_NAME: Service name for tracing

=============================================================================
"""

from .otel_config import setup_telemetry, get_tracer, get_meter
from .custom_metrics import (
    track_extraction,
    track_error,
    track_api_request,
    get_metrics_summary
)
from .analytics import AnalyticsTracker, track_event, track_user_action
from .logging_config import setup_logging, get_json_logger, JSONFormatter
from .cefr_bridge import (
    CEFRBridge,
    get_cefr_bridge,
    report_to_cefr,
    report_feedback_to_cefr
)

__all__ = [
    # OpenTelemetry
    'setup_telemetry',
    'get_tracer',
    'get_meter',
    # Metrics
    'track_extraction',
    'track_error',
    'track_api_request',
    'get_metrics_summary',
    # Analytics
    'AnalyticsTracker',
    'track_event',
    'track_user_action',
    # Logging
    'setup_logging',
    'get_json_logger',
    'JSONFormatter',
    # CEFR
    'CEFRBridge',
    'get_cefr_bridge',
    'report_to_cefr',
    'report_feedback_to_cefr',
]
