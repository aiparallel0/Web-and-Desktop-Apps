# Telemetry and Security Hardening Guide

## Overview

This document describes the telemetry and security enhancements implemented in the Receipt Extractor application.

## Table of Contents

1. [OpenTelemetry Integration](#opentelemetry-integration)
2. [Security Hardening](#security-hardening)
3. [Usage Examples](#usage-examples)
4. [Testing](#testing)
5. [Monitoring and Debugging](#monitoring-and-debugging)

---

## OpenTelemetry Integration

### Overview

OpenTelemetry provides distributed tracing and metrics collection for monitoring application performance and debugging issues.

### Components Added

#### 1. Telemetry Utilities (`shared/utils/telemetry.py`)

Provides helper functions for adding telemetry to any part of the application:

```python
from shared.utils.telemetry import get_tracer, trace_function, set_span_attributes

# Get tracer
tracer = get_tracer()

# Use as decorator
@trace_function("my_operation", attributes={"operation.type": "processing"})
def my_function():
    # Function automatically traced
    pass

# Manual span creation
with tracer.start_as_current_span("my_operation") as span:
    set_span_attributes(span, {
        "user.id": user_id,
        "operation.type": "extraction"
    })
    # Do work
```

**Key Features:**
- No-op fallback when OpenTelemetry is not available
- Automatic exception recording
- PII sanitization with `sanitize_attributes()`
- Easy-to-use decorators

#### 2. Instrumented Components

The following components now include OpenTelemetry tracing:

**Model Processing:**
- `shared/models/ocr_processor.py` - OCR text extraction
- `shared/models/manager.py` - Model loading and caching

**API Endpoints:**
- `web/backend/api/quick_extract.py` - Free tier receipt extraction
- `web/backend/routes.py` - User registration

**External Services:**
- `web/backend/storage/s3_handler.py` - S3 file uploads

### Span Attributes

Standardized attributes are used across the application:

| Attribute | Description | Example |
|-----------|-------------|---------|
| `operation.type` | Type of operation | `"ocr_processing"`, `"storage_upload"` |
| `model.id` | Model identifier | `"tesseract"`, `"donut_cord"` |
| `model.name` | Friendly model name | `"Tesseract OCR"` |
| `extraction.success` | Whether extraction succeeded | `true`, `false` |
| `extraction.confidence` | Confidence score | `0.92` |
| `extraction.items_count` | Number of items extracted | `15` |
| `extraction.processing_time` | Processing duration (seconds) | `0.45` |
| `user.id` | User ID (when authenticated) | `"uuid-string"` |
| `client.ip` | Client IP address | `"192.168.1.1"` |
| `cache.hit` | Whether cache was hit | `true`, `false` |

### Adding Telemetry to New Code

#### Method 1: Using Decorator

```python
from shared.utils.telemetry import trace_function

@trace_function("my_module.my_function")
def process_data(data):
    # Automatically traced
    return result
```

#### Method 2: Manual Spans

```python
from shared.utils.telemetry import get_tracer, set_span_attributes

def complex_operation():
    tracer = get_tracer()
    with tracer.start_as_current_span("complex_operation") as span:
        # Set attributes
        set_span_attributes(span, {
            "operation.type": "complex",
            "input.size": len(data)
        })
        
        try:
            # Do work
            result = do_work()
            
            # Set success attributes
            set_span_attributes(span, {
                "success": True,
                "result.size": len(result)
            })
            
            return result
        except Exception as e:
            # Exception automatically recorded
            span.record_exception(e)
            raise
```

---

## Security Hardening

### Overview

Multiple layers of security have been added to protect against common vulnerabilities and attacks.

### Components Added

#### 1. Input Validation (`shared/utils/validation.py`)

Comprehensive input validation decorators and functions:

```python
from shared.utils.validation import validate_json_body, validate_file_upload, validate_params

# Validate JSON request body
@validate_json_body({
    'email': {'type': str, 'required': True, 'format': 'email'},
    'password': {'type': str, 'required': True, 'min_length': 8}
})
def register():
    # Request body automatically validated
    pass

# Validate file uploads
@validate_file_upload(param_name='image', max_size=10*1024*1024)
def upload_image():
    # File automatically validated (type, size, extension)
    pass

# Validate function parameters
@validate_params({
    'user_id': {'type': str, 'required': True, 'format': 'uuid'},
    'count': {'type': int, 'min': 1, 'max': 100}
})
def get_receipts(user_id, count=10):
    # Parameters automatically validated
    pass
```

**Validation Types:**
- Type checking (`type: str`, `type: int`, etc.)
- Format validation (`format: 'email'`, `format: 'uuid'`)
- Range validation (`min: 0`, `max: 100`)
- Length validation (`min_length: 8`, `max_length: 255`)
- Choices validation (`choices: ['free', 'pro', 'business']`)
- File validation (extension, MIME type, size)

#### 2. Rate Limiting

Applied to endpoints to prevent abuse:

```python
from web.backend.security.rate_limiting import rate_limit

@rate_limit(requests=10, window=3600)  # 10 requests per hour
def quick_extract():
    pass

@rate_limit(requests=5, window=3600, error_message="Custom error")
def register():
    pass
```

**Rate Limits:**
- Quick extract: 10 requests/hour (free tier)
- Registration: 5 requests/hour
- Login: 5 requests/minute
- API calls: 1000 requests/hour (authenticated)

Rate limit headers are automatically added to responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: When limit resets (Unix timestamp)

#### 3. Security Headers

Already implemented in `web/backend/security/headers.py`:

```python
from web.backend.security.headers import init_security_headers

app = Flask(__name__)
init_security_headers(app)
```

**Headers Added:**
- `Content-Security-Policy`: Prevents XSS attacks
- `X-Content-Type-Options: nosniff`: Prevents MIME type sniffing
- `X-Frame-Options: DENY`: Prevents clickjacking
- `X-XSS-Protection: 1; mode=block`: XSS protection
- `Strict-Transport-Security`: Forces HTTPS (production only)
- `Referrer-Policy`: Controls referrer information

#### 4. PII Protection

Sensitive data is never exposed in logs or telemetry:

```python
from shared.utils.telemetry import sanitize_attributes

attributes = {
    'user_id': '123',
    'email': 'user@example.com',  # Will be redacted
    'password': 'secret',  # Will be redacted
    'token': 'abc123'  # Will be redacted
}

safe_attributes = sanitize_attributes(attributes)
# {'user_id': '123', 'email': '***REDACTED***', ...}
```

**Sensitive Keys (auto-redacted):**
- `password`
- `token`
- `secret`
- `api_key`
- `access_key`
- `authorization`
- `credit_card`
- `ssn`
- `email`

#### 5. Filename Sanitization

Prevents path traversal attacks:

```python
from shared.utils.validation import sanitize_filename

# Dangerous input
filename = "../../etc/passwd"
safe_filename = sanitize_filename(filename)
# Result: "etcpasswd"

# Dangerous characters removed
filename = "file<>?.txt"
safe_filename = sanitize_filename(filename)
# Result: "file.txt"
```

### Security Checklist for New Code

When adding new endpoints or functionality:

- [ ] Add rate limiting decorator (`@rate_limit()`)
- [ ] Add input validation (`@validate_json_body()` or `@validate_file_upload()`)
- [ ] Sanitize filenames if accepting file uploads
- [ ] Use parameterized queries for database operations (SQLAlchemy ORM)
- [ ] Never log sensitive data (passwords, tokens, PII)
- [ ] Use generic error messages (don't expose internal details)
- [ ] Add authentication decorator (`@require_auth`) if endpoint should be protected
- [ ] Add authorization checks (verify user can access resource)
- [ ] Add telemetry spans for monitoring

---

## Usage Examples

### Example 1: Protected API Endpoint with Telemetry

```python
from flask import Blueprint, request, jsonify, g
from shared.utils.telemetry import get_tracer, set_span_attributes
from shared.utils.validation import validate_json_body
from web.backend.security.rate_limiting import rate_limit
from web.backend.auth import require_auth

bp = Blueprint('receipts', __name__)

@bp.route('/api/receipts', methods=['POST'])
@require_auth
@rate_limit(requests=100, window=3600)
@validate_json_body({
    'image_url': {'type': str, 'required': True},
    'model_id': {'type': str, 'required': False}
})
def process_receipt():
    """Process a receipt with full security and telemetry."""
    tracer = get_tracer()
    with tracer.start_as_current_span("api.process_receipt") as span:
        try:
            data = request.get_json()
            
            # Set span attributes
            set_span_attributes(span, {
                "operation.type": "receipt_processing",
                "user.id": g.user_id,
                "model.id": data.get('model_id', 'default')
            })
            
            # Process receipt
            result = process_image(data['image_url'], data.get('model_id'))
            
            # Set success attributes
            set_span_attributes(span, {
                "success": True,
                "items_count": len(result.items)
            })
            
            return jsonify(result.to_dict())
            
        except Exception as e:
            logger.error(f"Receipt processing failed: {e}")
            span.record_exception(e)
            return jsonify({
                'success': False,
                'error': 'Processing failed. Please try again.'
            }), 500
```

### Example 2: Model Processing with Telemetry

```python
from shared.utils.telemetry import trace_function, set_span_attributes, get_tracer

class MyModelProcessor:
    @trace_function("my_model.extract", attributes={"model.type": "custom"})
    def extract(self, image_path: str):
        """Extract receipt data with telemetry."""
        tracer = get_tracer()
        
        # Get current span (created by decorator)
        from opentelemetry import trace
        span = trace.get_current_span()
        
        # Add more attributes
        set_span_attributes(span, {
            "file.path": image_path
        })
        
        # Process
        result = self._do_extraction(image_path)
        
        # Add result attributes
        set_span_attributes(span, {
            "extraction.confidence": result.confidence,
            "extraction.items_count": len(result.items)
        })
        
        return result
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tools/tests/ -v

# Run specific test files
pytest tools/tests/test_telemetry.py -v
pytest tools/tests/test_validation.py -v
pytest tools/tests/test_security_integration.py -v

# Run with coverage
pytest tools/tests/ --cov=shared --cov=web/backend --cov-report=html
```

### Test Coverage

- Telemetry tests: 71 test cases
- Validation tests: 177 test cases
- Security integration tests: 100+ test cases

### Writing Tests

When adding new security or telemetry features:

```python
def test_my_feature_with_telemetry():
    """Test that my feature creates telemetry spans."""
    from unittest.mock import Mock, patch
    
    with patch('shared.utils.telemetry.get_tracer') as mock_tracer:
        mock_span = Mock()
        mock_tracer.return_value.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        # Call function
        my_function()
        
        # Verify span was created
        mock_tracer.return_value.start_as_current_span.assert_called()
        
        # Verify attributes were set
        mock_span.set_attribute.assert_called()
```

---

## Monitoring and Debugging

### Viewing Traces

If OpenTelemetry is configured with an OTLP endpoint (e.g., Jaeger, Tempo):

1. **Start your OTLP collector** (e.g., Jaeger)
2. **Configure environment variables**:
   ```bash
   export OTEL_ENABLED=true
   export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
   export OTEL_SERVICE_NAME=receipt-extractor
   ```
3. **Run the application**
4. **View traces** in your collector's UI (e.g., http://localhost:16686 for Jaeger)

### Debugging Failed Requests

When a request fails, look for:

1. **Span status**: Should be `ERROR` for failed operations
2. **Exception details**: Captured via `span.record_exception()`
3. **Attributes**: Check operation-specific attributes (model_id, user_id, etc.)
4. **Timing**: Use span duration to identify bottlenecks

### Common Issues

#### Issue: Spans not appearing in collector

**Solution:**
- Verify `OTEL_ENABLED=true`
- Check OTLP endpoint is reachable
- Check logs for OpenTelemetry errors

#### Issue: Rate limiting too strict

**Solution:**
- Adjust rate limit decorator parameters
- Use Redis backend for distributed rate limiting
- Implement rate limit bypass for admin users

#### Issue: Validation rejecting valid input

**Solution:**
- Check validation rules in decorator
- Verify input format matches schema
- Add logging to validation decorator for debugging

---

## Best Practices

### Telemetry

1. **Always add spans to critical operations** (model processing, API calls, database queries)
2. **Use meaningful span names** (e.g., `"ocr_processor.extract"` not `"process"`)
3. **Add relevant attributes** to help with debugging
4. **Never log sensitive data** in span attributes
5. **Record exceptions** with `span.record_exception()`
6. **Set span status** on errors

### Security

1. **Validate all user input** (even from authenticated users)
2. **Use parameterized queries** for database operations
3. **Sanitize all file names** before saving
4. **Apply rate limiting** to prevent abuse
5. **Use generic error messages** (don't expose internal details)
6. **Log security events** (failed auth, rate limits, validation failures)
7. **Regularly audit** logs for suspicious activity

---

## Configuration

### Environment Variables

```bash
# OpenTelemetry
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=receipt-extractor
FLASK_ENV=production

# Rate Limiting
RATE_LIMIT_BACKEND=redis  # or 'memory'
REDIS_URL=redis://localhost:6379

# Security
CORS_ORIGINS=https://example.com,https://app.example.com
JWT_SECRET=<long-random-string>
```

### Customizing Rate Limits

Edit `web/backend/security/rate_limiting.py`:

```python
RATE_LIMITS = {
    'default': {'requests': 100, 'window': 60},
    'auth': {'requests': 5, 'window': 60},
    'extract': {'requests': 30, 'window': 60},
    'batch': {'requests': 10, 'window': 60},
    'api_key': {'requests': 1000, 'window': 3600},
}
```

---

## Troubleshooting

### OpenTelemetry Issues

**Problem: No traces appearing**
- Check `OTEL_ENABLED` is set to `true`
- Verify OTLP endpoint is accessible
- Check application logs for errors

**Problem: High overhead**
- Reduce sampling rate
- Use asynchronous exporters
- Disable debug logging

### Rate Limiting Issues

**Problem: Legitimate users being blocked**
- Increase rate limits
- Implement user-specific limits based on subscription tier
- Add rate limit bypass for admin users

**Problem: Rate limits not working across instances**
- Switch from memory to Redis backend
- Ensure all instances share same Redis

### Validation Issues

**Problem: Valid input being rejected**
- Check validation schema
- Add logging to validation decorator
- Test with curl or Postman

---

## Future Enhancements

- [ ] Add custom metrics (processing time histograms, error rates)
- [ ] Implement distributed tracing across microservices
- [ ] Add alerting based on telemetry data
- [ ] Implement security event logging and SIEM integration
- [ ] Add honeypot endpoints to detect attackers
- [ ] Implement advanced rate limiting (token bucket, leaky bucket)
- [ ] Add request signing for API authentication
- [ ] Implement IP-based geoblocking

---

## References

- [OpenTelemetry Python Documentation](https://opentelemetry-python.readthedocs.io/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
