"""
=============================================================================
UNIFIED ERROR HANDLING - Consolidated Error System
=============================================================================

Consolidates error handling from:
- shared/utils/helpers.py (ErrorCategory, ErrorCode, custom exceptions)
- web/backend/errors.py (ErrorResponse, ERROR_METADATA)

Provides:
- Standardized error codes and categories
- Custom exception classes
- Error response formatting for Flask
- Error metadata and suggested actions

Integrated with Circular Exchange Framework for dynamic error configuration.

Usage:
    from shared.utils.errors import (
        ErrorCode, ErrorCategory, ReceiptExtractorError,
        ValidationError, ProcessingError, create_error_response
    )
    
    # Raise custom exception
    raise ValidationError("Invalid input", code=ErrorCode.INVALID_INPUT)
    
    # Create Flask error response
    return create_error_response(ErrorCode.OCR_EXTRACTION_FAILED)

=============================================================================
"""

import logging
import time
import uuid
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

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
    """
    Standardized error codes.
    
    Format: E{category}{number} (e.g., E1001, E2001)
    Legacy format: ERR_{CATEGORY}_{NUMBER} also supported
    """
    # Validation errors (1xxx)
    INVALID_INPUT = "E1001"
    MISSING_REQUIRED_FIELD = "E1002"
    INVALID_FILE_TYPE = "E1003"
    FILE_TOO_LARGE = "E1004"
    INVALID_FORMAT = "E1005"
    FILE_EMPTY = "E1006"
    INVALID_MODEL_ID = "E1007"
    INVALID_JSON = "E1008"
    
    # Authentication errors (2xxx)
    INVALID_CREDENTIALS = "E2001"
    TOKEN_EXPIRED = "E2002"
    TOKEN_INVALID = "E2003"
    ACCOUNT_DISABLED = "E2004"
    TOKEN_MISSING = "E2005"
    EMAIL_NOT_VERIFIED = "E2006"
    ACCOUNT_LOCKED = "E2007"
    
    # Authorization errors (3xxx)
    INSUFFICIENT_PERMISSIONS = "E3001"
    PLAN_LIMIT_EXCEEDED = "E3002"
    RATE_LIMIT_EXCEEDED = "E3003"
    RESOURCE_ACCESS_DENIED = "E3004"
    API_KEY_INVALID = "E3005"
    
    # Resource errors (4xxx)
    RESOURCE_NOT_FOUND = "E4001"
    MODEL_NOT_FOUND = "E4002"
    USER_NOT_FOUND = "E4003"
    RESOURCE_ALREADY_EXISTS = "E4004"
    RESOURCE_UNAVAILABLE = "E4005"
    RESOURCE_BUSY = "E4006"
    
    # Processing errors (5xxx)
    OCR_FAILED = "E5001"
    IMAGE_PROCESSING_FAILED = "E5002"
    MODEL_LOADING_FAILED = "E5003"
    EXTRACTION_FAILED = "E5004"
    OCR_NO_TEXT_DETECTED = "E5005"
    OCR_LOW_CONFIDENCE = "E5006"
    OCR_IMAGE_QUALITY = "E5007"
    OCR_PREPROCESSING_FAILED = "E5008"
    OCR_MODEL_NOT_LOADED = "E5009"
    OCR_TIMEOUT = "E5010"
    PARSE_NO_STORE_NAME = "E5011"
    PARSE_NO_TOTAL = "E5012"
    PARSE_INVALID_DATE = "E5013"
    PARSE_MATH_VALIDATION = "E5014"
    PARSE_NO_ITEMS = "E5015"
    
    # External service errors (6xxx)
    EXTERNAL_SERVICE_UNAVAILABLE = "E6001"
    EXTERNAL_SERVICE_TIMEOUT = "E6002"
    CLOUD_STORAGE_ERROR = "E6003"
    EXTERNAL_API_ERROR = "E6004"
    EXTERNAL_RATE_LIMITED = "E6005"
    
    # Internal errors (9xxx)
    INTERNAL_ERROR = "E9001"
    DATABASE_ERROR = "E9002"
    CONFIGURATION_ERROR = "E9003"
    RESOURCE_EXHAUSTED = "E9004"

# Error metadata - message, HTTP status, suggested action
ERROR_METADATA = {
    # Validation Errors
    ErrorCode.INVALID_INPUT: {
        "message": "Invalid input provided",
        "http_status": 400,
        "suggested_action": "Check your input data and try again"
    },
    ErrorCode.MISSING_REQUIRED_FIELD: {
        "message": "Required field is missing",
        "http_status": 400,
        "suggested_action": "Ensure all required fields are provided in your request"
    },
    ErrorCode.INVALID_FILE_TYPE: {
        "message": "File type not allowed",
        "http_status": 400,
        "suggested_action": "Upload an image file (PNG, JPG, JPEG, BMP, TIFF)"
    },
    ErrorCode.FILE_TOO_LARGE: {
        "message": "File size exceeds maximum allowed",
        "http_status": 413,
        "suggested_action": "Reduce file size or compress the image"
    },
    ErrorCode.INVALID_FORMAT: {
        "message": "Field has invalid format",
        "http_status": 400,
        "suggested_action": "Check the field format matches the expected pattern"
    },
    ErrorCode.FILE_EMPTY: {
        "message": "Uploaded file is empty",
        "http_status": 400,
        "suggested_action": "Upload a valid non-empty image file"
    },
    ErrorCode.INVALID_MODEL_ID: {
        "message": "Invalid model ID specified",
        "http_status": 400,
        "suggested_action": "Use one of the available model IDs from /api/models"
    },
    ErrorCode.INVALID_JSON: {
        "message": "Request body must be valid JSON",
        "http_status": 400,
        "suggested_action": "Ensure the request body is properly formatted JSON"
    },
    
    # Authentication Errors
    ErrorCode.INVALID_CREDENTIALS: {
        "message": "Invalid email or password",
        "http_status": 401,
        "suggested_action": "Check your credentials and try again"
    },
    ErrorCode.TOKEN_EXPIRED: {
        "message": "Authentication token has expired",
        "http_status": 401,
        "suggested_action": "Sign in again to get a new token"
    },
    ErrorCode.TOKEN_INVALID: {
        "message": "Authentication token is invalid",
        "http_status": 401,
        "suggested_action": "Sign in again to get a new token"
    },
    ErrorCode.ACCOUNT_DISABLED: {
        "message": "Account has been disabled",
        "http_status": 403,
        "suggested_action": "Contact support to reactivate your account"
    },
    ErrorCode.TOKEN_MISSING: {
        "message": "Authentication token is required",
        "http_status": 401,
        "suggested_action": "Include Bearer token in Authorization header"
    },
    ErrorCode.EMAIL_NOT_VERIFIED: {
        "message": "Email address not verified",
        "http_status": 403,
        "suggested_action": "Check your email and click the verification link"
    },
    ErrorCode.ACCOUNT_LOCKED: {
        "message": "Account has been locked",
        "http_status": 403,
        "suggested_action": "Contact support to unlock your account"
    },
    
    # Authorization Errors
    ErrorCode.INSUFFICIENT_PERMISSIONS: {
        "message": "Insufficient permissions for this action",
        "http_status": 403,
        "suggested_action": "Contact an administrator for access"
    },
    ErrorCode.PLAN_LIMIT_EXCEEDED: {
        "message": "You have exceeded your plan limits",
        "http_status": 403,
        "suggested_action": "Upgrade your plan for more capacity"
    },
    ErrorCode.RATE_LIMIT_EXCEEDED: {
        "message": "Rate limit exceeded",
        "http_status": 429,
        "suggested_action": "Wait before making more requests"
    },
    ErrorCode.RESOURCE_ACCESS_DENIED: {
        "message": "Access to this resource is denied",
        "http_status": 403,
        "suggested_action": "You do not have permission to access this resource"
    },
    ErrorCode.API_KEY_INVALID: {
        "message": "API key is invalid or revoked",
        "http_status": 401,
        "suggested_action": "Generate a new API key from your dashboard"
    },
    
    # Resource Errors
    ErrorCode.RESOURCE_NOT_FOUND: {
        "message": "Requested resource not found",
        "http_status": 404,
        "suggested_action": "Verify the resource ID and try again"
    },
    ErrorCode.MODEL_NOT_FOUND: {
        "message": "Specified model not found",
        "http_status": 404,
        "suggested_action": "Check available models using /api/models"
    },
    ErrorCode.USER_NOT_FOUND: {
        "message": "User not found",
        "http_status": 404,
        "suggested_action": "Verify the user ID"
    },
    ErrorCode.RESOURCE_ALREADY_EXISTS: {
        "message": "Resource already exists",
        "http_status": 409,
        "suggested_action": "Use a different identifier or update existing resource"
    },
    ErrorCode.RESOURCE_UNAVAILABLE: {
        "message": "Resource is temporarily unavailable",
        "http_status": 503,
        "suggested_action": "Try again later"
    },
    ErrorCode.RESOURCE_BUSY: {
        "message": "Resource is currently busy",
        "http_status": 409,
        "suggested_action": "Wait and try again"
    },
    
    # Processing Errors
    ErrorCode.OCR_FAILED: {
        "message": "OCR extraction failed",
        "http_status": 500,
        "suggested_action": "Try uploading a clearer image or use a different OCR model"
    },
    ErrorCode.IMAGE_PROCESSING_FAILED: {
        "message": "Image processing failed",
        "http_status": 500,
        "suggested_action": "Ensure the image is valid and not corrupted"
    },
    ErrorCode.MODEL_LOADING_FAILED: {
        "message": "Failed to load model",
        "http_status": 503,
        "suggested_action": "Wait a moment and try again, or select a different model"
    },
    ErrorCode.EXTRACTION_FAILED: {
        "message": "Extraction failed",
        "http_status": 500,
        "suggested_action": "Try again or contact support if the problem persists"
    },
    ErrorCode.OCR_NO_TEXT_DETECTED: {
        "message": "No readable text detected in the image",
        "http_status": 422,
        "suggested_action": "Ensure the image contains readable text"
    },
    ErrorCode.OCR_LOW_CONFIDENCE: {
        "message": "Low confidence in extraction results",
        "http_status": 200,
        "suggested_action": "Review the results carefully or try a different model"
    },
    ErrorCode.OCR_IMAGE_QUALITY: {
        "message": "Image quality is too low for reliable extraction",
        "http_status": 422,
        "suggested_action": "Upload a higher quality image with better lighting and focus"
    },
    ErrorCode.OCR_PREPROCESSING_FAILED: {
        "message": "Image preprocessing failed",
        "http_status": 500,
        "suggested_action": "Try uploading the original image without preprocessing"
    },
    ErrorCode.OCR_MODEL_NOT_LOADED: {
        "message": "OCR model is not loaded",
        "http_status": 503,
        "suggested_action": "Wait a moment and try again, or select a different model"
    },
    ErrorCode.OCR_TIMEOUT: {
        "message": "OCR processing timed out",
        "http_status": 504,
        "suggested_action": "Try a smaller image or select a faster model"
    },
    
    # External Service Errors
    ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE: {
        "message": "External service is unavailable",
        "http_status": 503,
        "suggested_action": "Try again later"
    },
    ErrorCode.EXTERNAL_SERVICE_TIMEOUT: {
        "message": "External service request timed out",
        "http_status": 504,
        "suggested_action": "Try again later"
    },
    ErrorCode.CLOUD_STORAGE_ERROR: {
        "message": "Cloud storage operation failed",
        "http_status": 502,
        "suggested_action": "Try again or contact support"
    },
    ErrorCode.EXTERNAL_API_ERROR: {
        "message": "External API returned an error",
        "http_status": 502,
        "suggested_action": "Check credentials and try again"
    },
    ErrorCode.EXTERNAL_RATE_LIMITED: {
        "message": "External service rate limited",
        "http_status": 429,
        "suggested_action": "Wait before retrying"
    },
    
    # Internal Errors
    ErrorCode.INTERNAL_ERROR: {
        "message": "An internal server error occurred",
        "http_status": 500,
        "suggested_action": "Contact support if the problem persists"
    },
    ErrorCode.DATABASE_ERROR: {
        "message": "Database operation failed",
        "http_status": 500,
        "suggested_action": "Try again later"
    },
    ErrorCode.CONFIGURATION_ERROR: {
        "message": "Configuration error",
        "http_status": 500,
        "suggested_action": "Contact support"
    },
    ErrorCode.RESOURCE_EXHAUSTED: {
        "message": "Server resources exhausted",
        "http_status": 503,
        "suggested_action": "Try again later when resources are available"
    },
}

@dataclass
class ErrorResponse:
    """
    Standardized error response structure.
    
    Attributes:
        error_code: Unique error code (e.g., E1001)
        error_type: Error classification (e.g., validation)
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
        code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        if service_name:
            details['service'] = service_name
        
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.EXTERNAL_SERVICE,
            details=details,
            http_status=503
        )

def create_error_response(
    error_code: ErrorCode,
    details: Dict[str, Any] = None,
    custom_message: str = None,
    request_id: str = None
) -> tuple:
    """
    Create a standardized error response for Flask.
    
    Args:
        error_code: Error code from ErrorCode enum
        details: Additional error context
        custom_message: Override default message
        request_id: Custom request ID (auto-generated if not provided)
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    metadata = ERROR_METADATA.get(error_code, {
        "message": "An error occurred",
        "http_status": 500,
        "suggested_action": "Contact support"
    })
    
    # Generate request ID
    if request_id is None:
        try:
            # Try to get request ID from Flask request context
            from flask import request as flask_request
            request_id = flask_request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        except (ImportError, RuntimeError):
            request_id = str(uuid.uuid4())[:8]
    
    # Get category from error code
    code_value = int(error_code.value[1:5])  # Extract number from E1001
    if 1000 <= code_value < 2000:
        category = ErrorCategory.VALIDATION
    elif 2000 <= code_value < 3000:
        category = ErrorCategory.AUTHENTICATION
    elif 3000 <= code_value < 4000:
        category = ErrorCategory.AUTHORIZATION
    elif 4000 <= code_value < 5000:
        category = ErrorCategory.NOT_FOUND
    elif 5000 <= code_value < 6000:
        category = ErrorCategory.PROCESSING
    elif 6000 <= code_value < 7000:
        category = ErrorCategory.EXTERNAL_SERVICE
    else:
        category = ErrorCategory.INTERNAL
    
    error = ErrorResponse(
        error_code=error_code.value,
        error_type=category.value,
        message=custom_message or metadata["message"],
        suggested_action=metadata.get("suggested_action", ""),
        details=details or {},
        request_id=request_id
    )
    
    # Log the error
    logger.error(f"Error [{error.request_id}] {error_code.value}: {error.message}")
    if details:
        logger.error(f"  Details: {details}")
    
    return error.to_dict(), metadata["http_status"]
