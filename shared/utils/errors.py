"""
Standardized error handling for the Receipt Extractor application.

This module provides:
- Custom exception classes with proper categorization
- Error response formatting
- Error logging utilities
- Exception handlers for Flask

Integrated with Circular Exchange Framework for dynamic error configuration.
"""
import logging
import time
import traceback
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.utils.errors",
            file_path=__file__,
            description="Standardized error handling with custom exception classes and error formatting",
            dependencies=["shared.circular_exchange"],
            exports=["ErrorCategory", "ErrorCode", "ReceiptExtractorError", "ValidationError",
                     "ProcessingError", "ExternalServiceError", "RateLimitError", 
                     "CircuitBreaker", "CircuitBreakerConfig", "get_circuit_breaker"]
        ))
    except Exception:
        pass  # Ignore registration errors


class ErrorCategory(str, Enum):
    """Categories of errors for better classification."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    PROCESSING = "processing"
    EXTERNAL_SERVICE = "external_service"
    RATE_LIMIT = "rate_limit"
    INTERNAL = "internal"
    CONFIGURATION = "configuration"


class ErrorCode(str, Enum):
    """Standardized error codes."""
    # Validation errors (1xxx)
    INVALID_INPUT = "E1001"
    MISSING_REQUIRED_FIELD = "E1002"
    INVALID_FILE_TYPE = "E1003"
    FILE_TOO_LARGE = "E1004"
    INVALID_FORMAT = "E1005"
    
    # Authentication errors (2xxx)
    INVALID_CREDENTIALS = "E2001"
    TOKEN_EXPIRED = "E2002"
    TOKEN_INVALID = "E2003"
    ACCOUNT_DISABLED = "E2004"
    
    # Authorization errors (3xxx)
    INSUFFICIENT_PERMISSIONS = "E3001"
    PLAN_LIMIT_EXCEEDED = "E3002"
    RATE_LIMIT_EXCEEDED = "E3003"
    
    # Resource errors (4xxx)
    RESOURCE_NOT_FOUND = "E4001"
    MODEL_NOT_FOUND = "E4002"
    USER_NOT_FOUND = "E4003"
    
    # Processing errors (5xxx)
    OCR_FAILED = "E5001"
    IMAGE_PROCESSING_FAILED = "E5002"
    MODEL_LOADING_FAILED = "E5003"
    EXTRACTION_FAILED = "E5004"
    
    # External service errors (6xxx)
    EXTERNAL_SERVICE_UNAVAILABLE = "E6001"
    EXTERNAL_SERVICE_TIMEOUT = "E6002"
    CLOUD_STORAGE_ERROR = "E6003"
    
    # Internal errors (9xxx)
    INTERNAL_ERROR = "E9001"
    DATABASE_ERROR = "E9002"
    CONFIGURATION_ERROR = "E9003"


@dataclass
class ErrorDetails:
    """Structured error details."""
    code: ErrorCode
    message: str
    category: ErrorCategory
    details: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None


class ReceiptExtractorError(Exception):
    """Base exception class for all application errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        http_status: int = 500
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.category = category
        self.details = details or {}
        self.suggestion = suggestion
        self.http_status = http_status
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response."""
        error_dict = {
            'success': False,
            'error': {
                'code': self.code.value,
                'type': self.category.value,
                'message': self.message,
                'timestamp': self.timestamp
            }
        }
        
        if self.details:
            error_dict['error']['details'] = self.details
        
        if self.suggestion:
            error_dict['error']['suggestion'] = self.suggestion
        
        return error_dict
    
    def log_error(self, include_traceback: bool = False):
        """Log the error with appropriate level."""
        log_message = f"[{self.code.value}] {self.message}"
        
        if self.details:
            log_message += f" | Details: {self.details}"
        
        if self.category in (ErrorCategory.INTERNAL, ErrorCategory.PROCESSING):
            if include_traceback:
                logger.error(log_message, exc_info=True)
            else:
                logger.error(log_message)
        elif self.category == ErrorCategory.VALIDATION:
            logger.warning(log_message)
        else:
            logger.info(log_message)


# Specific exception classes
class ValidationError(ReceiptExtractorError):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INVALID_INPUT,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.VALIDATION,
            details=details,
            suggestion=suggestion,
            http_status=400
        )


class AuthenticationError(ReceiptExtractorError):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        code: ErrorCode = ErrorCode.INVALID_CREDENTIALS,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.AUTHENTICATION,
            details=details,
            http_status=401
        )


class AuthorizationError(ReceiptExtractorError):
    """Raised when authorization fails."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        code: ErrorCode = ErrorCode.INSUFFICIENT_PERMISSIONS,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.AUTHORIZATION,
            details=details,
            http_status=403
        )


class NotFoundError(ReceiptExtractorError):
    """Raised when a resource is not found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
        
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.NOT_FOUND,
            details=details if details else None,
            http_status=404
        )


class ProcessingError(ReceiptExtractorError):
    """Raised when processing fails."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.EXTRACTION_FAILED,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.PROCESSING,
            details=details,
            suggestion=suggestion,
            http_status=500
        )


class RateLimitError(ReceiptExtractorError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        remaining: Optional[int] = None
    ):
        details = {}
        if retry_after:
            details['retry_after'] = retry_after
        if limit:
            details['limit'] = limit
        if remaining is not None:
            details['remaining'] = remaining
        
        super().__init__(
            message=message,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            category=ErrorCategory.RATE_LIMIT,
            details=details if details else None,
            http_status=429
        )


class ExternalServiceError(ReceiptExtractorError):
    """Raised when an external service fails."""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE
    ):
        details = {}
        if service_name:
            details['service'] = service_name
        
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.EXTERNAL_SERVICE,
            details=details if details else None,
            suggestion="Please try again later or contact support if the issue persists",
            http_status=503
        )


# =============================================================================
# CIRCUIT BREAKER PATTERN - Added based on CEF Round 5 analysis
# =============================================================================

class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 3          # Successes to close from half-open
    timeout_seconds: float = 30.0       # Time before attempting half-open
    half_open_max_calls: int = 3        # Max calls in half-open state


class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls.
    
    CEF Round 5: Added to improve reliability by preventing cascading failures
    when external services become unavailable.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests rejected immediately  
    - HALF_OPEN: Testing recovery, limited requests allowed
    
    Usage:
        breaker = CircuitBreaker("ocr_service")
        
        @breaker
        def call_ocr_service():
            # External call
            pass
    """
    
    def __init__(self, service_name: str, config: Optional[CircuitBreakerConfig] = None):
        self.service_name = service_name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
    
    def _should_allow_request(self) -> bool:
        """Check if request should be allowed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.config.timeout_seconds:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_calls = 0
                    self.success_count = 0
                    logger.info(f"Circuit breaker for {self.service_name} entering HALF_OPEN state")
                    return True
            return False
        
        # HALF_OPEN: Allow limited requests
        if self.half_open_calls < self.config.half_open_max_calls:
            return True
        return False
    
    def record_success(self):
        """Record a successful call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            self.half_open_calls += 1
            
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit breaker for {self.service_name} CLOSED (service recovered)")
        else:
            # Reset failure count on success in closed state
            self.failure_count = 0
    
    def record_failure(self):
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            # Any failure in half-open goes back to open
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker for {self.service_name} OPEN (failure in half-open)")
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker for {self.service_name} OPEN (threshold reached)")
    
    def __call__(self, func):
        """Decorator to wrap function with circuit breaker."""
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self._should_allow_request():
                raise ExternalServiceError(
                    f"Service {self.service_name} is temporarily unavailable (circuit breaker open)",
                    service_name=self.service_name
                )
            
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise
        
        return wrapper
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            'service': self.service_name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure': self.last_failure_time
        }


# Global circuit breaker registry for service monitoring
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(service_name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker for a service."""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker(service_name, config)
    return _circuit_breakers[service_name]


def get_all_circuit_breaker_states() -> Dict[str, Dict[str, Any]]:
    """Get states of all circuit breakers (for health monitoring)."""
    return {name: breaker.get_state() for name, breaker in _circuit_breakers.items()}


# Error response utilities
def create_error_response(
    error: ReceiptExtractorError
) -> tuple:
    """Create a Flask-compatible error response tuple."""
    error.log_error()
    return error.to_dict(), error.http_status


def create_simple_error_response(
    message: str,
    status_code: int = 500,
    error_type: str = "error"
) -> tuple:
    """Create a simple error response without custom exception."""
    response = {
        'success': False,
        'error': {
            'type': error_type,
            'message': message,
            'timestamp': time.time()
        }
    }
    return response, status_code


def handle_exception(e: Exception) -> tuple:
    """Handle any exception and return appropriate response."""
    if isinstance(e, ReceiptExtractorError):
        return create_error_response(e)
    
    # Log unexpected errors with traceback
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    
    # Return generic error for security (don't expose internal details)
    return create_simple_error_response(
        message="An unexpected error occurred",
        status_code=500,
        error_type="internal_error"
    )


# Flask error handlers
def register_error_handlers(app):
    """Register error handlers with a Flask application."""
    from flask import jsonify
    
    @app.errorhandler(ReceiptExtractorError)
    def handle_receipt_extractor_error(error):
        response, status_code = create_error_response(error)
        return jsonify(response), status_code
    
    @app.errorhandler(413)
    def handle_request_entity_too_large(error):
        return jsonify({
            'success': False,
            'error': {
                'code': ErrorCode.FILE_TOO_LARGE.value,
                'type': ErrorCategory.VALIDATION.value,
                'message': 'File size exceeds maximum limit',
                'timestamp': time.time()
            }
        }), 413
    
    @app.errorhandler(429)
    def handle_rate_limit(error):
        return jsonify({
            'success': False,
            'error': {
                'code': ErrorCode.RATE_LIMIT_EXCEEDED.value,
                'type': ErrorCategory.RATE_LIMIT.value,
                'message': 'Too many requests',
                'timestamp': time.time()
            }
        }), 429
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'error': {
                'code': ErrorCode.INTERNAL_ERROR.value,
                'type': ErrorCategory.INTERNAL.value,
                'message': 'Internal server error',
                'timestamp': time.time()
            }
        }), 500
    
    logger.info("Error handlers registered")
