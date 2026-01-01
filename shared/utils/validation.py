"""
=============================================================================
INPUT VALIDATION UTILITIES - Comprehensive Input Validation
=============================================================================

Provides validation decorators and functions for input validation across
the application.

Usage:
    from shared.utils.validation import validate_file_upload, validate_params
    
    @validate_params({
        'email': {'type': str, 'required': True, 'format': 'email'},
        'age': {'type': int, 'min': 0, 'max': 150}
    })
    def register_user(email: str, age: int):
        ...

=============================================================================
"""

import re
import logging
import functools
import mimetypes
from typing import Callable, Dict, Any, Optional, List, Union
from flask import request, jsonify

logger = logging.getLogger(__name__)

# =============================================================================
# VALIDATION PATTERNS
# =============================================================================

EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)

# Allowed image MIME types
ALLOWED_IMAGE_MIMES = {
    'image/jpeg',
    'image/png',
    'image/bmp',
    'image/tiff',
    'image/webp'
}

# Allowed image extensions
ALLOWED_IMAGE_EXTENSIONS = {
    'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'webp'
}

# Maximum file sizes (in bytes)
MAX_FILE_SIZES = {
    'image': 100 * 1024 * 1024,  # 100 MB
    'document': 50 * 1024 * 1024,  # 50 MB
    'default': 10 * 1024 * 1024   # 10 MB
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    return EMAIL_PATTERN.match(email.strip()) is not None

def validate_uuid(uuid_str: str) -> bool:
    """
    Validate UUID format.
    
    Args:
        uuid_str: UUID string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not uuid_str or not isinstance(uuid_str, str):
        return False
    
    return UUID_PATTERN.match(uuid_str.strip()) is not None

def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    
    Args:
        filename: Original filename
        max_length: Maximum allowed length
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"
    
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Limit length
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:max_length - len(ext) - 1]
        filename = f"{name}.{ext}" if ext else name
    
    return filename or "unnamed"

def check_file_size(file_size: int, file_type: str = 'default') -> tuple:
    """
    Check if file size is within allowed limits.
    
    Args:
        file_size: File size in bytes
        file_type: Type of file ('image', 'document', or 'default')
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    max_size = MAX_FILE_SIZES.get(file_type, MAX_FILE_SIZES['default'])
    
    if file_size > max_size:
        return False, f"File size ({file_size} bytes) exceeds maximum allowed ({max_size} bytes)"
    
    return True, None

def check_file_extension(filename: str, allowed_extensions: set = None) -> tuple:
    """
    Check if file extension is allowed.
    
    Args:
        filename: Filename to check
        allowed_extensions: Set of allowed extensions (defaults to images)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS
    
    if '.' not in filename:
        return False, "File has no extension"
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext not in allowed_extensions:
        return False, f"File extension '.{ext}' not allowed. Allowed: {', '.join(allowed_extensions)}"
    
    return True, None

def check_mime_type(mime_type: str, allowed_mimes: set = None) -> tuple:
    """
    Check if MIME type is allowed.
    
    Args:
        mime_type: MIME type to check
        allowed_mimes: Set of allowed MIME types (defaults to images)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if allowed_mimes is None:
        allowed_mimes = ALLOWED_IMAGE_MIMES
    
    if not mime_type:
        return False, "No MIME type provided"
    
    if mime_type not in allowed_mimes:
        return False, f"MIME type '{mime_type}' not allowed. Allowed: {', '.join(allowed_mimes)}"
    
    return True, None

# =============================================================================
# VALIDATION DECORATORS
# =============================================================================

def validate_params(schema: Dict[str, Dict[str, Any]]):
    """
    Decorator to validate function parameters against a schema.
    
    Args:
        schema: Dictionary mapping parameter names to validation rules
                Rules can include: type, required, min, max, format, choices
    
    Example:
        @validate_params({
            'email': {'type': str, 'required': True, 'format': 'email'},
            'age': {'type': int, 'min': 0, 'max': 150},
            'plan': {'type': str, 'choices': ['free', 'pro', 'business']}
        })
        def register(email, age, plan='free'):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function arguments
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            params = bound_args.arguments
            
            errors = []
            
            for param_name, rules in schema.items():
                value = params.get(param_name)
                
                # Check required
                if rules.get('required') and value is None:
                    errors.append(f"Parameter '{param_name}' is required")
                    continue
                
                # Skip validation if value is None and not required
                if value is None:
                    continue
                
                # Check type
                expected_type = rules.get('type')
                if expected_type and not isinstance(value, expected_type):
                    errors.append(
                        f"Parameter '{param_name}' must be of type {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
                    continue
                
                # Check format
                format_type = rules.get('format')
                if format_type == 'email' and not validate_email(value):
                    errors.append(f"Parameter '{param_name}' is not a valid email")
                elif format_type == 'uuid' and not validate_uuid(value):
                    errors.append(f"Parameter '{param_name}' is not a valid UUID")
                
                # Check min/max for numbers
                if isinstance(value, (int, float)):
                    min_val = rules.get('min')
                    max_val = rules.get('max')
                    if min_val is not None and value < min_val:
                        errors.append(f"Parameter '{param_name}' must be >= {min_val}")
                    if max_val is not None and value > max_val:
                        errors.append(f"Parameter '{param_name}' must be <= {max_val}")
                
                # Check min/max length for strings
                if isinstance(value, str):
                    min_len = rules.get('min_length')
                    max_len = rules.get('max_length')
                    if min_len is not None and len(value) < min_len:
                        errors.append(f"Parameter '{param_name}' must be at least {min_len} characters")
                    if max_len is not None and len(value) > max_len:
                        errors.append(f"Parameter '{param_name}' must be at most {max_len} characters")
                
                # Check choices
                choices = rules.get('choices')
                if choices and value not in choices:
                    errors.append(
                        f"Parameter '{param_name}' must be one of {choices}, got '{value}'"
                    )
            
            if errors:
                # If this is a Flask request, return JSON error
                try:
                    from flask import request as flask_request
                    if flask_request:
                        return jsonify({
                            'success': False,
                            'error': 'Validation failed',
                            'details': errors
                        }), 400
                except (ImportError, RuntimeError):
                    pass
                
                # Otherwise raise ValueError
                raise ValueError(f"Validation failed: {'; '.join(errors)}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def validate_file_upload(
    param_name: str = 'file',
    allowed_extensions: set = None,
    allowed_mimes: set = None,
    max_size: int = None,
    required: bool = True
):
    """
    Decorator to validate file uploads in Flask routes.
    
    Args:
        param_name: Name of the file parameter in request.files
        allowed_extensions: Set of allowed file extensions
        allowed_mimes: Set of allowed MIME types
        max_size: Maximum file size in bytes
        required: Whether file is required
    
    Example:
        @app.route('/upload', methods=['POST'])
        @validate_file_upload(param_name='image', max_size=10*1024*1024)
        def upload_image():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get file from request
            if param_name not in request.files:
                if required:
                    return jsonify({
                        'success': False,
                        'error': f"No file provided with parameter '{param_name}'"
                    }), 400
                else:
                    return func(*args, **kwargs)
            
            file = request.files[param_name]
            
            # Check if file is empty
            if not file or file.filename == '':
                if required:
                    return jsonify({
                        'success': False,
                        'error': 'Empty file provided'
                    }), 400
                else:
                    return func(*args, **kwargs)
            
            # Validate filename
            filename = sanitize_filename(file.filename)
            
            # Validate extension
            is_valid, error = check_file_extension(filename, allowed_extensions)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': error
                }), 400
            
            # Validate MIME type
            if allowed_mimes:
                mime_type = file.content_type or mimetypes.guess_type(filename)[0]
                is_valid, error = check_mime_type(mime_type, allowed_mimes)
                if not is_valid:
                    return jsonify({
                        'success': False,
                        'error': error
                    }), 400
            
            # Validate file size
            if max_size:
                # Read file to check size
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size > max_size:
                    return jsonify({
                        'success': False,
                        'error': f"File size ({file_size} bytes) exceeds maximum allowed ({max_size} bytes)"
                    }), 400
            
            # File is valid, proceed
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def validate_json_body(schema: Dict[str, Dict[str, Any]]):
    """
    Decorator to validate JSON request body against a schema.
    
    Args:
        schema: Dictionary mapping field names to validation rules
    
    Example:
        @app.route('/api/register', methods=['POST'])
        @validate_json_body({
            'email': {'type': str, 'required': True, 'format': 'email'},
            'password': {'type': str, 'required': True, 'min_length': 8}
        })
        def register():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get JSON body
            try:
                data = request.get_json()
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid JSON: {str(e)}'
                }), 400
            
            if data is None:
                return jsonify({
                    'success': False,
                    'error': 'Request body must be JSON'
                }), 400
            
            errors = []
            
            for field_name, rules in schema.items():
                value = data.get(field_name)
                
                # Check required
                if rules.get('required') and value is None:
                    errors.append(f"Field '{field_name}' is required")
                    continue
                
                # Skip validation if value is None and not required
                if value is None:
                    continue
                
                # Check type
                expected_type = rules.get('type')
                if expected_type and not isinstance(value, expected_type):
                    errors.append(
                        f"Field '{field_name}' must be of type {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
                    continue
                
                # Check format
                format_type = rules.get('format')
                if format_type == 'email' and not validate_email(value):
                    errors.append(f"Field '{field_name}' is not a valid email")
                elif format_type == 'uuid' and not validate_uuid(value):
                    errors.append(f"Field '{field_name}' is not a valid UUID")
                
                # Check min/max for numbers
                if isinstance(value, (int, float)):
                    min_val = rules.get('min')
                    max_val = rules.get('max')
                    if min_val is not None and value < min_val:
                        errors.append(f"Field '{field_name}' must be >= {min_val}")
                    if max_val is not None and value > max_val:
                        errors.append(f"Field '{field_name}' must be <= {max_val}")
                
                # Check min/max length for strings
                if isinstance(value, str):
                    min_len = rules.get('min_length')
                    max_len = rules.get('max_length')
                    if min_len is not None and len(value) < min_len:
                        errors.append(f"Field '{field_name}' must be at least {min_len} characters")
                    if max_len is not None and len(value) > max_len:
                        errors.append(f"Field '{field_name}' must be at most {max_len} characters")
                
                # Check choices
                choices = rules.get('choices')
                if choices and value not in choices:
                    errors.append(
                        f"Field '{field_name}' must be one of {choices}, got '{value}'"
                    )
            
            if errors:
                return jsonify({
                    'success': False,
                    'error': 'Validation failed',
                    'details': errors
                }), 400
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

__all__ = [
    'validate_params',
    'validate_file_upload',
    'validate_json_body',
    'validate_email',
    'validate_uuid',
    'sanitize_filename',
    'check_file_size',
    'check_file_extension',
    'check_mime_type'
]
