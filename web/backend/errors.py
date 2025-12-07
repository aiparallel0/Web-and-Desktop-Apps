"""
DEPRECATED: Use shared.utils.errors instead.
Legacy wrapper for backward compatibility with tests.
"""

# Re-export everything from the consolidated errors module
from shared.utils.errors import (
    ErrorCategory,
    ErrorCode,
    ErrorResponse,
    ERROR_METADATA,
    create_error_response,
    ReceiptExtractorError,
    ValidationError,
    ProcessingError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ExternalServiceError
)

from shared.utils.base_handler import RetryMixin


class ErrorRecoveryHandler(RetryMixin):
    """Legacy error recovery handler - use RetryMixin instead."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def with_fallback_models(self, extract_func, image_path: str, models: list):
        """Try extraction with fallback models."""
        import logging
        logger = logging.getLogger(__name__)
        
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


recovery_handler = ErrorRecoveryHandler()


def create_partial_success_response(data, warnings, confidence=None):
    """Create partial success response."""
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


__all__ = [
    'ErrorCategory', 'ErrorCode', 'ErrorResponse', 'ERROR_METADATA',
    'create_error_response', 'create_partial_success_response',
    'ErrorRecoveryHandler', 'recovery_handler',
    'ReceiptExtractorError', 'ValidationError', 'ProcessingError',
    'AuthenticationError', 'AuthorizationError', 'NotFoundError',
    'RateLimitError', 'ExternalServiceError'
]
