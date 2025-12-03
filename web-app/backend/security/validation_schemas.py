"""
=============================================================================
VALIDATION SCHEMAS - Input Validation and Sanitization
=============================================================================

Provides input validation and sanitization functions for security.

Usage:
    from security.validation_schemas import validate_request, sanitize_input
    
    @validate_request(schema=LoginSchema)
    def login():
        ...
    
    clean_input = sanitize_input(user_input)

=============================================================================
"""

import re
import logging
import html
from typing import Dict, Any, List, Optional, Type, Callable
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised when validation fails."""
    
    def __init__(self, message: str, field: str = None, errors: List[str] = None):
        self.message = message
        self.field = field
        self.errors = errors or []
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result = {'error': self.message}
        if self.field:
            result['field'] = self.field
        if self.errors:
            result['errors'] = self.errors
        return result


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid
    """
    if not email:
        return False
    
    # RFC 5322 compliant regex (simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if len(password) > 128:
        errors.append("Password must be at most 128 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        errors.append("Password must contain at least one special character")
    
    return (len(errors) == 0, errors)


def validate_model_id(model_id: str) -> bool:
    """
    Validate model ID format.
    
    Args:
        model_id: Model ID to validate
        
    Returns:
        True if valid
    """
    if not model_id:
        return False
    
    # Allow alphanumeric, underscores, hyphens, and slashes (for HuggingFace)
    pattern = r'^[a-zA-Z0-9_/-]+$'
    return bool(re.match(pattern, model_id)) and len(model_id) <= 200


def validate_uuid(uuid_str: str) -> bool:
    """
    Validate UUID format.
    
    Args:
        uuid_str: UUID string to validate
        
    Returns:
        True if valid
    """
    if not uuid_str:
        return False
    
    pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    return bool(re.match(pattern, uuid_str.lower()))


def validate_filename(filename: str) -> bool:
    """
    Validate filename for safety.
    
    Args:
        filename: Filename to validate
        
    Returns:
        True if valid
    """
    if not filename:
        return False
    
    # Check for path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check length
    if len(filename) > 255:
        return False
    
    # Check for allowed extensions
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'pdf'}
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    return ext in allowed_extensions


# =============================================================================
# SANITIZATION FUNCTIONS
# =============================================================================

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize text input by escaping HTML and limiting length.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Escape HTML characters
    text = html.escape(text)
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe storage.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"
    
    # Remove path components
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove potentially dangerous characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_len = 255 - len(ext) - 1
        filename = f"{name[:max_name_len]}.{ext}" if ext else name[:255]
    
    return filename or "unnamed"


def sanitize_dict(data: Dict[str, Any], max_depth: int = 5) -> Dict[str, Any]:
    """
    Recursively sanitize a dictionary.
    
    Args:
        data: Dictionary to sanitize
        max_depth: Maximum recursion depth
        
    Returns:
        Sanitized dictionary
    """
    if max_depth <= 0:
        return {}
    
    result = {}
    for key, value in data.items():
        # Sanitize key
        clean_key = sanitize_input(str(key), max_length=100)
        
        # Sanitize value based on type
        if isinstance(value, str):
            result[clean_key] = sanitize_input(value)
        elif isinstance(value, dict):
            result[clean_key] = sanitize_dict(value, max_depth - 1)
        elif isinstance(value, list):
            result[clean_key] = [
                sanitize_input(str(v)) if isinstance(v, str) else v
                for v in value[:100]  # Limit list size
            ]
        else:
            result[clean_key] = value
    
    return result


# =============================================================================
# VALIDATION DECORATOR
# =============================================================================

def validate_request(
    required_fields: List[str] = None,
    optional_fields: List[str] = None,
    validators: Dict[str, Callable] = None
):
    """
    Decorator to validate request JSON body.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
        validators: Dict mapping field names to validation functions
    
    Usage:
        @validate_request(
            required_fields=['email', 'password'],
            validators={'email': validate_email}
        )
        def register():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get JSON body
            data = request.get_json()
            
            if data is None:
                return jsonify({
                    'success': False,
                    'error': 'Request body must be valid JSON'
                }), 400
            
            errors = []
            
            # Check required fields
            if required_fields:
                for field in required_fields:
                    if field not in data or data[field] is None:
                        errors.append(f"Field '{field}' is required")
                    elif isinstance(data[field], str) and not data[field].strip():
                        errors.append(f"Field '{field}' cannot be empty")
            
            # Run custom validators
            if validators:
                for field, validator in validators.items():
                    if field in data and data[field] is not None:
                        try:
                            if not validator(data[field]):
                                errors.append(f"Field '{field}' is invalid")
                        except Exception as e:
                            errors.append(f"Validation error for '{field}': {str(e)}")
            
            if errors:
                return jsonify({
                    'success': False,
                    'error': 'Validation failed',
                    'errors': errors
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def validate_query_params(
    allowed_params: List[str] = None,
    validators: Dict[str, Callable] = None
):
    """
    Decorator to validate query parameters.
    
    Args:
        allowed_params: List of allowed parameter names
        validators: Dict mapping param names to validation functions
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            errors = []
            
            # Check for unknown parameters
            if allowed_params:
                for param in request.args:
                    if param not in allowed_params:
                        errors.append(f"Unknown parameter: {param}")
            
            # Run validators
            if validators:
                for param, validator in validators.items():
                    value = request.args.get(param)
                    if value is not None:
                        try:
                            if not validator(value):
                                errors.append(f"Invalid value for parameter '{param}'")
                        except Exception as e:
                            errors.append(f"Validation error for '{param}': {str(e)}")
            
            if errors:
                return jsonify({
                    'success': False,
                    'error': 'Invalid query parameters',
                    'errors': errors
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


# =============================================================================
# COMMON VALIDATION SCHEMAS
# =============================================================================

COMMON_VALIDATORS = {
    'email': validate_email,
    'model_id': validate_model_id,
    'uuid': validate_uuid,
    'filename': validate_filename,
}


def get_validator(name: str) -> Optional[Callable]:
    """Get a common validator by name."""
    return COMMON_VALIDATORS.get(name)
