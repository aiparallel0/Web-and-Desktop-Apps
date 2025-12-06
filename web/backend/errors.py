"""
=============================================================================
COMPREHENSIVE ERROR HANDLING - Enterprise Error Response System
=============================================================================

Implements the error classification system from the enhancement plan:
- Standardized error codes (ERR_OCR_001, ERR_VALIDATION_002, etc.)
- Error types (ValidationError, ProcessingError, AuthenticationError)
- Detailed error context with suggested actions
- Request tracking via request_id

Usage:
    from errors import ErrorResponse, ErrorCode, create_error_response
    
    # Return standardized error
    return create_error_response(
        ErrorCode.OCR_EXTRACTION_FAILED,
        details={'model': 'easyocr', 'image_size': '1024x768'}
    )

=============================================================================
"""

import time
import uuid
import logging
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from flask import jsonify, request

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Error category classification."""
    VALIDATION = "ValidationError"
    PROCESSING = "ProcessingError"
    AUTHENTICATION = "AuthenticationError"
    AUTHORIZATION = "AuthorizationError"
    RATE_LIMIT = "RateLimitError"
    RESOURCE = "ResourceError"
    EXTERNAL = "ExternalServiceError"
    INTERNAL = "InternalServerError"


class ErrorCode(str, Enum):
    """
    Standardized error codes for the receipt extraction platform.
    
    Format: ERR_{CATEGORY}_{NUMBER}
    """
    # Validation Errors (001-099)
    VALIDATION_REQUIRED_FIELD = "ERR_VALIDATION_001"
    VALIDATION_INVALID_FORMAT = "ERR_VALIDATION_002"
    VALIDATION_FILE_TYPE = "ERR_VALIDATION_003"
    VALIDATION_FILE_SIZE = "ERR_VALIDATION_004"
    VALIDATION_FILE_EMPTY = "ERR_VALIDATION_005"
    VALIDATION_MODEL_ID = "ERR_VALIDATION_006"
    VALIDATION_JSON_BODY = "ERR_VALIDATION_007"
    VALIDATION_CREDENTIALS = "ERR_VALIDATION_008"
    
    # OCR Processing Errors (100-199)
    OCR_EXTRACTION_FAILED = "ERR_OCR_100"
    OCR_NO_TEXT_DETECTED = "ERR_OCR_101"
    OCR_LOW_CONFIDENCE = "ERR_OCR_102"
    OCR_IMAGE_QUALITY = "ERR_OCR_103"
    OCR_PREPROCESSING_FAILED = "ERR_OCR_104"
    OCR_MODEL_NOT_LOADED = "ERR_OCR_105"
    OCR_MODEL_NOT_FOUND = "ERR_OCR_106"
    OCR_TIMEOUT = "ERR_OCR_107"
    
    # Receipt Parsing Errors (200-299)
    PARSE_NO_STORE_NAME = "ERR_PARSE_200"
    PARSE_NO_TOTAL = "ERR_PARSE_201"
    PARSE_INVALID_DATE = "ERR_PARSE_202"
    PARSE_MATH_VALIDATION = "ERR_PARSE_203"
    PARSE_NO_ITEMS = "ERR_PARSE_204"
    
    # Authentication Errors (300-399)
    AUTH_TOKEN_MISSING = "ERR_AUTH_300"
    AUTH_TOKEN_INVALID = "ERR_AUTH_301"
    AUTH_TOKEN_EXPIRED = "ERR_AUTH_302"
    AUTH_INVALID_CREDENTIALS = "ERR_AUTH_303"
    AUTH_ACCOUNT_LOCKED = "ERR_AUTH_304"
    AUTH_EMAIL_NOT_VERIFIED = "ERR_AUTH_305"
    
    # Authorization Errors (400-499)
    AUTHZ_INSUFFICIENT_PERMISSIONS = "ERR_AUTHZ_400"
    AUTHZ_RESOURCE_ACCESS_DENIED = "ERR_AUTHZ_401"
    AUTHZ_PLAN_LIMIT_EXCEEDED = "ERR_AUTHZ_402"
    AUTHZ_API_KEY_INVALID = "ERR_AUTHZ_403"
    
    # Rate Limit Errors (500-599)
    RATE_LIMIT_EXCEEDED = "ERR_RATE_500"
    RATE_LIMIT_DAILY = "ERR_RATE_501"
    RATE_LIMIT_MONTHLY = "ERR_RATE_502"
    
    # Resource Errors (600-699)
    RESOURCE_NOT_FOUND = "ERR_RESOURCE_600"
    RESOURCE_ALREADY_EXISTS = "ERR_RESOURCE_601"
    RESOURCE_UNAVAILABLE = "ERR_RESOURCE_602"
    RESOURCE_BUSY = "ERR_RESOURCE_603"
    
    # External Service Errors (700-799)
    EXTERNAL_SERVICE_UNAVAILABLE = "ERR_EXT_700"
    EXTERNAL_API_ERROR = "ERR_EXT_701"
    EXTERNAL_TIMEOUT = "ERR_EXT_702"
    EXTERNAL_RATE_LIMITED = "ERR_EXT_703"
    
    # Internal Errors (800-899)
    INTERNAL_SERVER_ERROR = "ERR_INTERNAL_800"
    INTERNAL_DATABASE_ERROR = "ERR_INTERNAL_801"
    INTERNAL_CONFIG_ERROR = "ERR_INTERNAL_802"
    INTERNAL_RESOURCE_EXHAUSTED = "ERR_INTERNAL_803"


# Error code metadata (message, category, suggested action, HTTP status)
ERROR_METADATA = {
    # Validation Errors
    ErrorCode.VALIDATION_REQUIRED_FIELD: {
        "message": "Required field is missing",
        "category": ErrorCategory.VALIDATION,
        "suggested_action": "Ensure all required fields are provided in your request",
        "http_status": 400
    },
    ErrorCode.VALIDATION_INVALID_FORMAT: {
        "message": "Field has invalid format",
        "category": ErrorCategory.VALIDATION,
        "suggested_action": "Check the field format matches the expected pattern",
        "http_status": 400
    },
    ErrorCode.VALIDATION_FILE_TYPE: {
        "message": "File type not allowed",
        "category": ErrorCategory.VALIDATION,
        "suggested_action": "Upload an image file (PNG, JPG, JPEG, BMP, TIFF)",
        "http_status": 400
    },
    ErrorCode.VALIDATION_FILE_SIZE: {
        "message": "File size exceeds maximum allowed",
        "category": ErrorCategory.VALIDATION,
        "suggested_action": "Reduce file size or compress the image",
        "http_status": 413
    },
    ErrorCode.VALIDATION_FILE_EMPTY: {
        "message": "Uploaded file is empty",
        "category": ErrorCategory.VALIDATION,
        "suggested_action": "Upload a valid non-empty image file",
        "http_status": 400
    },
    ErrorCode.VALIDATION_MODEL_ID: {
        "message": "Invalid model ID specified",
        "category": ErrorCategory.VALIDATION,
        "suggested_action": "Use one of the available model IDs from /api/models",
        "http_status": 400
    },
    ErrorCode.VALIDATION_JSON_BODY: {
        "message": "Request body must be valid JSON",
        "category": ErrorCategory.VALIDATION,
        "suggested_action": "Ensure the request body is properly formatted JSON",
        "http_status": 400
    },
    ErrorCode.VALIDATION_CREDENTIALS: {
        "message": "Invalid or missing credentials",
        "category": ErrorCategory.VALIDATION,
        "suggested_action": "Provide valid authentication credentials",
        "http_status": 400
    },
    
    # OCR Processing Errors
    ErrorCode.OCR_EXTRACTION_FAILED: {
        "message": "OCR extraction failed",
        "category": ErrorCategory.PROCESSING,
        "suggested_action": "Try uploading a clearer image or use a different OCR model",
        "http_status": 500
    },
    ErrorCode.OCR_NO_TEXT_DETECTED: {
        "message": "No readable text detected in the image",
        "category": ErrorCategory.PROCESSING,
        "suggested_action": "Ensure the image contains readable text. Try EasyOCR for better results",
        "http_status": 422
    },
    ErrorCode.OCR_LOW_CONFIDENCE: {
        "message": "Low confidence in extraction results",
        "category": ErrorCategory.PROCESSING,
        "suggested_action": "Review the results carefully or try a different model",
        "http_status": 200  # Still returns results
    },
    ErrorCode.OCR_IMAGE_QUALITY: {
        "message": "Image quality is too low for reliable extraction",
        "category": ErrorCategory.PROCESSING,
        "suggested_action": "Upload a higher quality image with better lighting and focus",
        "http_status": 422
    },
    ErrorCode.OCR_PREPROCESSING_FAILED: {
        "message": "Image preprocessing failed",
        "category": ErrorCategory.PROCESSING,
        "suggested_action": "Try uploading the original image without preprocessing",
        "http_status": 500
    },
    ErrorCode.OCR_MODEL_NOT_LOADED: {
        "message": "OCR model is not loaded",
        "category": ErrorCategory.PROCESSING,
        "suggested_action": "Wait a moment and try again, or select a different model",
        "http_status": 503
    },
    ErrorCode.OCR_MODEL_NOT_FOUND: {
        "message": "Specified OCR model not found",
        "category": ErrorCategory.PROCESSING,
        "suggested_action": "Check available models using /api/models",
        "http_status": 404
    },
    ErrorCode.OCR_TIMEOUT: {
        "message": "OCR processing timed out",
        "category": ErrorCategory.PROCESSING,
        "suggested_action": "Try a smaller image or select a faster model",
        "http_status": 504
    },
    
    # Receipt Parsing Errors
    ErrorCode.PARSE_NO_STORE_NAME: {
        "message": "Could not detect store name",
        "category": ErrorCategory.PROCESSING,
        "suggested_action": "Ensure the store name is visible at the top of the receipt",
        "http_status": 200
    },
    ErrorCode.PARSE_NO_TOTAL: {
        "message": "Could not detect total amount",
        "category": ErrorCategory.PROCESSING,
        "suggested_action": "Ensure the total is visible and clearly printed",
        "http_status": 200
    },
    ErrorCode.PARSE_INVALID_DATE: {
        "message": "Could not parse transaction date",
        "category": ErrorCategory.PROCESSING,
        "suggested_action": "Manually verify the date in the results",
        "http_status": 200
    },
    ErrorCode.PARSE_MATH_VALIDATION: {
        "message": "Receipt totals do not add up correctly",
        "category": ErrorCategory.PROCESSING,
        "suggested_action": "Review extracted values for OCR errors",
        "http_status": 200
    },
    ErrorCode.PARSE_NO_ITEMS: {
        "message": "No line items detected",
        "category": ErrorCategory.PROCESSING,
        "suggested_action": "Ensure line items are clearly visible",
        "http_status": 200
    },
    
    # Authentication Errors
    ErrorCode.AUTH_TOKEN_MISSING: {
        "message": "Authentication token is required",
        "category": ErrorCategory.AUTHENTICATION,
        "suggested_action": "Include Bearer token in Authorization header",
        "http_status": 401
    },
    ErrorCode.AUTH_TOKEN_INVALID: {
        "message": "Authentication token is invalid",
        "category": ErrorCategory.AUTHENTICATION,
        "suggested_action": "Sign in again to get a new token",
        "http_status": 401
    },
    ErrorCode.AUTH_TOKEN_EXPIRED: {
        "message": "Authentication token has expired",
        "category": ErrorCategory.AUTHENTICATION,
        "suggested_action": "Sign in again to get a new token",
        "http_status": 401
    },
    ErrorCode.AUTH_INVALID_CREDENTIALS: {
        "message": "Invalid email or password",
        "category": ErrorCategory.AUTHENTICATION,
        "suggested_action": "Check your credentials and try again",
        "http_status": 401
    },
    ErrorCode.AUTH_ACCOUNT_LOCKED: {
        "message": "Account has been locked",
        "category": ErrorCategory.AUTHENTICATION,
        "suggested_action": "Contact support to unlock your account",
        "http_status": 403
    },
    ErrorCode.AUTH_EMAIL_NOT_VERIFIED: {
        "message": "Email address not verified",
        "category": ErrorCategory.AUTHENTICATION,
        "suggested_action": "Check your email and click the verification link",
        "http_status": 403
    },
    
    # Authorization Errors
    ErrorCode.AUTHZ_INSUFFICIENT_PERMISSIONS: {
        "message": "Insufficient permissions for this action",
        "category": ErrorCategory.AUTHORIZATION,
        "suggested_action": "Contact an administrator for access",
        "http_status": 403
    },
    ErrorCode.AUTHZ_RESOURCE_ACCESS_DENIED: {
        "message": "Access to this resource is denied",
        "category": ErrorCategory.AUTHORIZATION,
        "suggested_action": "You do not have permission to access this resource",
        "http_status": 403
    },
    ErrorCode.AUTHZ_PLAN_LIMIT_EXCEEDED: {
        "message": "You have exceeded your plan limits",
        "category": ErrorCategory.AUTHORIZATION,
        "suggested_action": "Upgrade your plan for more capacity",
        "http_status": 403
    },
    ErrorCode.AUTHZ_API_KEY_INVALID: {
        "message": "API key is invalid or revoked",
        "category": ErrorCategory.AUTHORIZATION,
        "suggested_action": "Generate a new API key from your dashboard",
        "http_status": 401
    },
    
    # Rate Limit Errors
    ErrorCode.RATE_LIMIT_EXCEEDED: {
        "message": "Rate limit exceeded",
        "category": ErrorCategory.RATE_LIMIT,
        "suggested_action": "Wait before making more requests",
        "http_status": 429
    },
    ErrorCode.RATE_LIMIT_DAILY: {
        "message": "Daily extraction limit exceeded",
        "category": ErrorCategory.RATE_LIMIT,
        "suggested_action": "Wait until tomorrow or upgrade your plan",
        "http_status": 429
    },
    ErrorCode.RATE_LIMIT_MONTHLY: {
        "message": "Monthly extraction limit exceeded",
        "category": ErrorCategory.RATE_LIMIT,
        "suggested_action": "Upgrade your plan for more extractions",
        "http_status": 429
    },
    
    # Resource Errors
    ErrorCode.RESOURCE_NOT_FOUND: {
        "message": "Requested resource not found",
        "category": ErrorCategory.RESOURCE,
        "suggested_action": "Verify the resource ID and try again",
        "http_status": 404
    },
    ErrorCode.RESOURCE_ALREADY_EXISTS: {
        "message": "Resource already exists",
        "category": ErrorCategory.RESOURCE,
        "suggested_action": "Use a different identifier or update existing resource",
        "http_status": 409
    },
    ErrorCode.RESOURCE_UNAVAILABLE: {
        "message": "Resource is temporarily unavailable",
        "category": ErrorCategory.RESOURCE,
        "suggested_action": "Try again later",
        "http_status": 503
    },
    ErrorCode.RESOURCE_BUSY: {
        "message": "Resource is currently busy",
        "category": ErrorCategory.RESOURCE,
        "suggested_action": "Wait and try again",
        "http_status": 409
    },
    
    # External Service Errors
    ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE: {
        "message": "External service is unavailable",
        "category": ErrorCategory.EXTERNAL,
        "suggested_action": "Try again later",
        "http_status": 503
    },
    ErrorCode.EXTERNAL_API_ERROR: {
        "message": "External API returned an error",
        "category": ErrorCategory.EXTERNAL,
        "suggested_action": "Check credentials and try again",
        "http_status": 502
    },
    ErrorCode.EXTERNAL_TIMEOUT: {
        "message": "External service request timed out",
        "category": ErrorCategory.EXTERNAL,
        "suggested_action": "Try again later",
        "http_status": 504
    },
    ErrorCode.EXTERNAL_RATE_LIMITED: {
        "message": "External service rate limited",
        "category": ErrorCategory.EXTERNAL,
        "suggested_action": "Wait before retrying",
        "http_status": 429
    },
    
    # Internal Errors
    ErrorCode.INTERNAL_SERVER_ERROR: {
        "message": "An internal server error occurred",
        "category": ErrorCategory.INTERNAL,
        "suggested_action": "Contact support if the problem persists",
        "http_status": 500
    },
    ErrorCode.INTERNAL_DATABASE_ERROR: {
        "message": "Database operation failed",
        "category": ErrorCategory.INTERNAL,
        "suggested_action": "Try again later",
        "http_status": 500
    },
    ErrorCode.INTERNAL_CONFIG_ERROR: {
        "message": "Configuration error",
        "category": ErrorCategory.INTERNAL,
        "suggested_action": "Contact support",
        "http_status": 500
    },
    ErrorCode.INTERNAL_RESOURCE_EXHAUSTED: {
        "message": "Server resources exhausted",
        "category": ErrorCategory.INTERNAL,
        "suggested_action": "Try again later when resources are available",
        "http_status": 503
    },
}


@dataclass
class ErrorResponse:
    """
    Standardized error response structure.
    
    Attributes:
        error_code: Unique error code (e.g., ERR_OCR_001)
        error_type: Error classification (e.g., ProcessingError)
        message: Human-readable error description
        details: Additional context
        timestamp: Unix timestamp when error occurred
        request_id: Unique request identifier for support
        suggested_action: User guidance for resolution
    """
    error_code: str
    error_type: str
    message: str
    timestamp: float = field(default_factory=time.time)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    details: Dict[str, Any] = field(default_factory=dict)
    suggested_action: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'success': False,
            'error': {
                'code': self.error_code,
                'type': self.error_type,
                'message': self.message,
                'timestamp': self.timestamp,
                'request_id': self.request_id,
                'suggested_action': self.suggested_action
            }
        }
        if self.details:
            result['error']['details'] = self.details
        return result


def create_error_response(
    error_code: ErrorCode,
    details: Dict[str, Any] = None,
    custom_message: str = None,
    request_id: str = None
) -> tuple:
    """
    Create a standardized error response.
    
    Args:
        error_code: Error code from ErrorCode enum
        details: Additional error context
        custom_message: Override default message
        request_id: Custom request ID (auto-generated if not provided)
        
    Returns:
        Tuple of (response, status_code)
    """
    metadata = ERROR_METADATA.get(error_code, {
        "message": "An error occurred",
        "category": ErrorCategory.INTERNAL,
        "suggested_action": "Contact support",
        "http_status": 500
    })
    
    # Generate request ID from request context if available
    if request_id is None:
        try:
            # Try to get request ID from headers or generate new
            request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        except RuntimeError:
            request_id = str(uuid.uuid4())[:8]
    
    error = ErrorResponse(
        error_code=error_code.value,
        error_type=metadata["category"].value,
        message=custom_message or metadata["message"],
        suggested_action=metadata["suggested_action"],
        details=details or {},
        request_id=request_id
    )
    
    # Log the error
    logger.error(f"Error [{error.request_id}] {error_code.value}: {error.message}")
    if details:
        logger.error(f"  Details: {details}")
    
    return jsonify(error.to_dict()), metadata["http_status"]


def create_partial_success_response(
    data: Dict[str, Any],
    warnings: list,
    confidence: float = None
) -> Dict[str, Any]:
    """
    Create a response for partial success with warnings.
    
    Used when extraction succeeds but with low confidence or missing fields.
    
    Args:
        data: Extracted data
        warnings: List of warning codes
        confidence: Confidence score (0-1)
        
    Returns:
        Response dictionary
    """
    warning_messages = []
    for warning_code in warnings:
        if isinstance(warning_code, ErrorCode):
            metadata = ERROR_METADATA.get(warning_code, {})
            warning_messages.append({
                'code': warning_code.value,
                'message': metadata.get('message', 'Warning'),
                'suggested_action': metadata.get('suggested_action', '')
            })
    
    return {
        'success': True,
        'partial': bool(warnings),
        'data': data,
        'confidence': confidence,
        'warnings': warning_messages
    }


# =============================================================================
# ERROR HANDLER DECORATORS
# =============================================================================

def handle_validation_errors(f):
    """
    Decorator to handle validation errors consistently.
    
    Usage:
        @app.route('/api/extract')
        @handle_validation_errors
        def extract():
            ...
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return create_error_response(
                ErrorCode.VALIDATION_INVALID_FORMAT,
                details={'error': str(e)}
            )
        except KeyError as e:
            return create_error_response(
                ErrorCode.VALIDATION_REQUIRED_FIELD,
                details={'field': str(e)}
            )
    
    return decorated_function


def handle_processing_errors(f):
    """
    Decorator to handle processing errors consistently.
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except TimeoutError:
            return create_error_response(ErrorCode.OCR_TIMEOUT)
        except MemoryError:
            return create_error_response(ErrorCode.INTERNAL_RESOURCE_EXHAUSTED)
        except Exception as e:
            logger.exception(f"Processing error: {e}")
            return create_error_response(
                ErrorCode.INTERNAL_SERVER_ERROR,
                details={'error': str(e)}
            )
    
    return decorated_function


# =============================================================================
# RECOVERY MECHANISMS
# =============================================================================

class ErrorRecoveryHandler:
    """
    Handles error recovery with fallback strategies.
    
    Implements:
    - Automatic retry with exponential backoff for transient failures
    - Fallback model selection if primary model fails
    - Partial result return if some fields cannot be extracted
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def with_retry(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or raises last exception
        """
        import time
        
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                delay = self.base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
        
        raise last_exception
    
    def with_fallback_models(self, extract_func, image_path: str, models: list):
        """
        Try extraction with fallback models.
        
        Args:
            extract_func: Extraction function taking (image_path, model_id)
            image_path: Path to image
            models: List of model IDs to try
            
        Returns:
            First successful extraction result
        """
        last_error = None
        for model_id in models:
            try:
                result = extract_func(image_path, model_id)
                if result and result.get('success'):
                    return result
            except Exception as e:
                last_error = e
                logger.warning(f"Model {model_id} failed: {e}")
        
        raise last_error or Exception("All models failed")


# Global recovery handler
recovery_handler = ErrorRecoveryHandler()
