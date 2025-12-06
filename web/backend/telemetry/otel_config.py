"""
=============================================================================
OPENTELEMETRY CONFIGURATION - Tracing and Metrics Setup
=============================================================================

Configures OpenTelemetry for distributed tracing and metrics collection.

Usage:
    from telemetry import setup_telemetry, get_tracer
    
    # Initialize at app startup
    setup_telemetry(app)
    
    # Use tracer in code
    tracer = get_tracer()
    with tracer.start_as_current_span("my_operation"):
        ...

=============================================================================
"""

import os
import logging
from typing import Optional
from functools import lru_cache
from shared.utils.optional_imports import OptionalImport

logger = logging.getLogger(__name__)

# Import OpenTelemetry packages
_otel_imports = OptionalImport.try_imports({
    'trace': 'opentelemetry.trace',
    'metrics': 'opentelemetry.metrics',
    'TracerProvider': 'opentelemetry.sdk.trace.TracerProvider',
    'MeterProvider': 'opentelemetry.sdk.metrics.MeterProvider',
    'Resource': 'opentelemetry.sdk.resources.Resource',
    'SERVICE_NAME': 'opentelemetry.sdk.resources.SERVICE_NAME',
    'SERVICE_VERSION': 'opentelemetry.sdk.resources.SERVICE_VERSION',
    'BatchSpanProcessor': 'opentelemetry.sdk.trace.export.BatchSpanProcessor',
    'ConsoleSpanExporter': 'opentelemetry.sdk.trace.export.ConsoleSpanExporter',
    'PeriodicExportingMetricReader': 'opentelemetry.sdk.metrics.export.PeriodicExportingMetricReader',
    'ConsoleMetricExporter': 'opentelemetry.sdk.metrics.export.ConsoleMetricExporter'
}, install_msg='pip install opentelemetry-api opentelemetry-sdk')

trace = _otel_imports['trace']
metrics = _otel_imports['metrics']
TracerProvider = _otel_imports['TracerProvider']
MeterProvider = _otel_imports['MeterProvider']
Resource = _otel_imports['Resource']
SERVICE_NAME = _otel_imports['SERVICE_NAME']
SERVICE_VERSION = _otel_imports['SERVICE_VERSION']
BatchSpanProcessor = _otel_imports['BatchSpanProcessor']
ConsoleSpanExporter = _otel_imports['ConsoleSpanExporter']
PeriodicExportingMetricReader = _otel_imports['PeriodicExportingMetricReader']
ConsoleMetricExporter = _otel_imports['ConsoleMetricExporter']
OTEL_AVAILABLE = _otel_imports['TRACE_AVAILABLE']

# Import OTLP exporters
_otlp_imports = OptionalImport.try_imports({
    'OTLPSpanExporter': 'opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter',
    'OTLPMetricExporter': 'opentelemetry.exporter.otlp.proto.grpc.metric_exporter.OTLPMetricExporter'
}, install_msg='pip install opentelemetry-exporter-otlp')

OTLPSpanExporter = _otlp_imports['OTLPSpanExporter']
OTLPMetricExporter = _otlp_imports['OTLPMetricExporter']
OTLP_AVAILABLE = _otlp_imports['OTLPSPANEXPORTER_AVAILABLE']

# Import Flask instrumentation
_flask_inst_imports = OptionalImport.try_imports({
    'FlaskInstrumentor': 'opentelemetry.instrumentation.flask.FlaskInstrumentor',
    'RequestsInstrumentor': 'opentelemetry.instrumentation.requests.RequestsInstrumentor'
}, install_msg='pip install opentelemetry-instrumentation-flask')

FlaskInstrumentor = _flask_inst_imports['FlaskInstrumentor']
RequestsInstrumentor = _flask_inst_imports['RequestsInstrumentor']
FLASK_INSTRUMENTATION_AVAILABLE = _flask_inst_imports['FLASKINSTRUMENTOR_AVAILABLE']


# =============================================================================
# CONFIGURATION
# =============================================================================

OTEL_ENABLED = os.getenv('OTEL_ENABLED', 'true').lower() == 'true'
OTEL_ENDPOINT = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318')
SERVICE_NAME_ENV = os.getenv('OTEL_SERVICE_NAME', 'receipt-extractor')
ENVIRONMENT = os.getenv('FLASK_ENV', 'development')

_tracer_provider: Optional['TracerProvider'] = None
_meter_provider: Optional['MeterProvider'] = None


def setup_telemetry(app=None) -> bool:
    """
    Configure OpenTelemetry for the Flask application.
    
    Args:
        app: Flask application instance
        
    Returns:
        True if telemetry was configured successfully
    """
    global _tracer_provider, _meter_provider
    
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available - telemetry disabled")
        return False
    
    if not OTEL_ENABLED:
        logger.info("OpenTelemetry disabled via OTEL_ENABLED=false")
        return False
    
    try:
        # Create resource with service information
        resource = Resource.create({
            SERVICE_NAME: SERVICE_NAME_ENV,
            SERVICE_VERSION: "2.0.0",
            "deployment.environment": ENVIRONMENT
        })
        
        # =====================================================================
        # TRACING SETUP
        # =====================================================================
        
        _tracer_provider = TracerProvider(resource=resource)
        
        # Add span exporter
        if OTLP_AVAILABLE and OTEL_ENDPOINT:
            try:
                otlp_exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT)
                _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                logger.info(f"OTLP trace exporter configured: {OTEL_ENDPOINT}")
            except Exception as e:
                logger.warning(f"Failed to configure OTLP exporter: {e}")
                # Fallback to console exporter
                _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        else:
            # Use console exporter for development
            if ENVIRONMENT == 'development':
                _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        
        trace.set_tracer_provider(_tracer_provider)
        
        # =====================================================================
        # METRICS SETUP
        # =====================================================================
        
        metric_readers = []
        
        if OTLP_AVAILABLE and OTEL_ENDPOINT:
            try:
                otlp_metric_exporter = OTLPMetricExporter(endpoint=OTEL_ENDPOINT)
                metric_readers.append(
                    PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=60000)
                )
            except Exception as e:
                logger.warning(f"Failed to configure OTLP metric exporter: {e}")
        
        if not metric_readers and ENVIRONMENT == 'development':
            # Console exporter for development
            metric_readers.append(
                PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=60000)
            )
        
        if metric_readers:
            _meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
            metrics.set_meter_provider(_meter_provider)
        
        # =====================================================================
        # FLASK INSTRUMENTATION
        # =====================================================================
        
        if app and FLASK_INSTRUMENTATION_AVAILABLE:
            FlaskInstrumentor().instrument_app(app)
            logger.info("Flask instrumentation enabled")
        
        if FLASK_INSTRUMENTATION_AVAILABLE:
            RequestsInstrumentor().instrument()
            logger.info("Requests instrumentation enabled")
        
        logger.info(f"OpenTelemetry configured for service: {SERVICE_NAME_ENV}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure OpenTelemetry: {e}")
        return False


@lru_cache(maxsize=1)
def get_tracer(name: str = None):
    """
    Get an OpenTelemetry tracer.
    
    Args:
        name: Tracer name (defaults to service name)
        
    Returns:
        Tracer instance or no-op tracer if not available
    """
    if not OTEL_AVAILABLE:
        # Return a no-op tracer-like object
        class NoOpTracer:
            def start_as_current_span(self, name, **kwargs):
                class NoOpSpan:
                    def __enter__(self):
                        return self
                    def __exit__(self, *args):
                        pass
                    def set_attribute(self, key, value):
                        pass
                    def add_event(self, name, attributes=None):
                        pass
                return NoOpSpan()
        return NoOpTracer()
    
    tracer_name = name or SERVICE_NAME_ENV
    return trace.get_tracer(tracer_name)


@lru_cache(maxsize=1)
def get_meter(name: str = None):
    """
    Get an OpenTelemetry meter for metrics.
    
    Args:
        name: Meter name (defaults to service name)
        
    Returns:
        Meter instance or no-op meter if not available
    """
    if not OTEL_AVAILABLE:
        # Return a no-op meter-like object
        class NoOpMeter:
            def create_counter(self, name, **kwargs):
                class NoOpCounter:
                    def add(self, amount, attributes=None):
                        pass
                return NoOpCounter()
            
            def create_histogram(self, name, **kwargs):
                class NoOpHistogram:
                    def record(self, amount, attributes=None):
                        pass
                return NoOpHistogram()
            
            def create_up_down_counter(self, name, **kwargs):
                class NoOpUpDownCounter:
                    def add(self, amount, attributes=None):
                        pass
                return NoOpUpDownCounter()
        
        return NoOpMeter()
    
    meter_name = name or SERVICE_NAME_ENV
    return metrics.get_meter(meter_name)


def shutdown_telemetry():
    """Shutdown OpenTelemetry providers gracefully."""
    global _tracer_provider, _meter_provider
    
    if _tracer_provider:
        _tracer_provider.shutdown()
    
    if _meter_provider:
        _meter_provider.shutdown()
    
    logger.info("OpenTelemetry shutdown complete")
