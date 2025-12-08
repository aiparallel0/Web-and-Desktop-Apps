# Telemetry & Security Implementation Guide

**Date:** 2025-12-07  
**Status:** In Progress (Phase 1: 50% Complete)  
**Purpose:** Step-by-step guide for implementing missing telemetry and security features

---

## Quick Reference: What's Already Done

### ✅ Fully Instrumented Files (3)
1. **web/backend/billing/routes.py** - All 6 endpoints with telemetry and rate limiting
2. **web/backend/api/websocket.py** - All 5 WebSocket handlers with telemetry
3. **web/backend/api/quick_extract.py** - Already instrumented (baseline)

### ⚡ Partially Instrumented Files (2)
1. **web/backend/app.py** - 2/11 endpoints complete (extract, extract/batch)
2. **shared/models/engine.py** - Telemetry imports added, needs implementation

---

## Implementation Pattern

### Standard Pattern for Adding Telemetry

Every endpoint should follow this pattern:

```python
# 1. Add imports at top of file
from shared.utils.telemetry import get_tracer, set_span_attributes
from web.backend.security.rate_limiting import rate_limit
from shared.utils.validation import validate_file_upload, validate_json_body

# 2. Add decorators to endpoint
@app.route('/api/endpoint', methods=['POST'])
@rate_limit(requests=100, window=3600)  # Adjust based on operation cost
@validate_file_upload(param_name='file', max_size=100*1024*1024)  # If file upload
def endpoint():
    """
    Endpoint description.
    
    Rate Limited: X requests per hour
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("api.endpoint_name") as span:
        try:
            # Set operation attributes
            set_span_attributes(span, {
                "operation.type": "operation_name",
                "user.id": g.user_id if hasattr(g, 'user_id') else None
            })
            
            # Your existing logic here
            result = process_data()
            
            # Set result attributes
            set_span_attributes(span, {
                "operation.success": True,
                "operation.items_count": len(result)
            })
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            span.record_exception(e)
            
            try:
                from opentelemetry.trace import Status, StatusCode
                span.set_status(Status(StatusCode.ERROR, str(e)))
            except ImportError:
                pass
            
            return jsonify({'success': False, 'error': str(e)}), 500
```

---

## Phase 1 Remaining Work

### 1. web/backend/app.py - Remaining 9 Endpoints

#### A. /api/extract/batch-multi (Line ~542)
**Current:** No telemetry, rate limiting, or validation  
**Required:**
- Rate limit: 5 requests/hour (expensive multi-model operation)
- Telemetry: Track batch count, model count, success/failure rates
- Validation: Validate batch size limits

```python
@app.route('/api/extract/batch-multi', methods=['POST'])
@rate_limit(requests=5, window=3600)
@validate_file_upload(param_name='image', max_size=100*1024*1024)
def extract_batch_multi():
    """
    Extract with multiple models in parallel.
    Rate Limited: 5 requests per hour
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("api.extract.batch_multi") as span:
        # Implementation here
        set_span_attributes(span, {
            "operation.type": "batch_multi_extract",
            "batch.models_requested": len(model_ids),
            "batch.concurrent": True
        })
```

#### B. /api/extract-stream (Line ~586)
**Current:** No telemetry or rate limiting  
**Required:**
- Rate limit: 20 requests/hour (streaming is resource-intensive)
- Telemetry: Track stream duration, chunks sent, disconnect reasons
- Monitor backpressure and client disconnects

```python
@app.route('/api/extract-stream', methods=['POST'])
@rate_limit(requests=20, window=3600)
def extract_receipt_stream():
    """
    Stream extraction progress via SSE.
    Rate Limited: 20 requests per hour
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("api.extract.stream") as span:
        set_span_attributes(span, {
            "operation.type": "stream_extract",
            "stream.format": "SSE"
        })
        # Streaming implementation
```

#### C. /api/finetune/prepare (Line ~701)
**Current:** No telemetry, rate limiting  
**Required:**
- Rate limit: 3 requests/hour (preparation is expensive)
- Telemetry: Track dataset size, preparation time
- Validate dataset format and size

```python
@app.route('/api/finetune/prepare', methods=['POST'])
@rate_limit(requests=3, window=3600)
def prepare_finetune():
    """
    Prepare dataset for finetuning.
    Rate Limited: 3 requests per hour
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("api.finetune.prepare") as span:
        set_span_attributes(span, {
            "operation.type": "finetune_prepare",
            "dataset.size": dataset_size
        })
```

#### D. /api/finetune/<job_id>/add-data (Line ~714)
**Current:** No telemetry, validation  
**Required:**
- Telemetry: Track data additions, file sizes
- Validation: File upload validation, job ownership check

#### E. /api/finetune/<job_id>/start (Line ~735)
**Current:** No telemetry, rate limiting  
**Required:**
- Rate limit: 2 requests/hour per user (very expensive)
- Telemetry: Track training parameters, estimated cost
- Validation: Training parameter validation

#### F. /api/finetune/<job_id>/status (Line ~840)
**Current:** No telemetry  
**Required:**
- Telemetry: Track status check frequency
- Validation: Job ownership

#### G-I. /api/cloud/* (3 endpoints, Lines 867-945)
**Current:** No telemetry, rate limiting, credential sanitization  
**Required:**
- Rate limiting on expensive operations
- Credential sanitization in logs
- Cloud provider validation

---

### 2. shared/models/engine.py - 4 AI Processors

**Challenge:** Code is heavily compressed on single lines  
**Approach:** Add telemetry wrapper at method entry/exit

#### Pattern for Model Processors:

```python
def extract(self, image_path: str) -> ExtractionResult:
    tracer = get_tracer()
    with tracer.start_as_current_span(f"model.{self.__class__.__name__}.extract") as span:
        start_time = time.time()
        try:
            set_span_attributes(span, {
                "model.type": self.__class__.__name__,
                "model.id": self.model_id,
                "image.path": os.path.basename(image_path)
            })
            
            # Existing extraction logic here
            result = # ... existing code ...
            
            set_span_attributes(span, {
                "extraction.success": result.success,
                "extraction.processing_time": time.time() - start_time,
                "extraction.confidence": getattr(result.data, 'confidence_score', 0)
            })
            
            return result
            
        except Exception as e:
            span.record_exception(e)
            raise
```

#### Processors to Instrument:

1. **DonutProcessor.extract()** (Line ~140)
   - Track: Inference time, token generation, confidence
   - Monitor: GPU utilization, memory usage

2. **FlorenceProcessor.extract()** (Line ~425)
   - Track: Vision-language processing time, confidence
   - Monitor: Model loading time, preprocessing steps

3. **EasyOCRProcessor.extract()** (Line ~1370)
   - Track: Language detection, OCR confidence, text regions
   - Monitor: Language-specific performance

4. **PaddleProcessor.extract()** (Line ~1591)
   - Track: Detection boxes, recognition accuracy
   - Monitor: Angle classification, preprocessing time

---

## Phase 2: Model Processors & Observability

### 1. shared/models/spatial_ocr.py (6 methods)

**File Size:** 1092 lines  
**Priority:** High (ensemble processing has no visibility)

#### Methods to Instrument:

1. **extract_with_tesseract()** (Line ~571)
   ```python
   tracer = get_tracer()
   with tracer.start_as_current_span("spatial_ocr.tesseract") as span:
       set_span_attributes(span, {
           "ocr.engine": "tesseract",
           "ocr.psm_mode": psm_mode
       })
   ```

2. **extract_with_easyocr()** (Line ~628)
3. **extract_with_paddleocr()** (Line ~685)
4. **SpatialOCRProcessor.extract()** (Line ~788)
   - Track ensemble consensus
   - Method comparison metrics
   - Fallback tracking

5. **EasyOCRSpatialProcessor.extract()** (Line ~938)
6. **PaddleOCRSpatialProcessor.extract()** (Line ~1025)

---

### 2. shared/models/craft_detector.py

**Priority:** Medium  
**Focus:** Text region detection metrics

Add telemetry to track:
- Text regions detected
- Detection confidence scores
- Preprocessing time
- Region merging operations

---

### 3. web/backend/billing/stripe_handler.py

**Priority:** High (payment operations)  
**Methods to Instrument:**

```python
def create_customer(self, email, name):
    tracer = get_tracer()
    with tracer.start_as_current_span("stripe.create_customer") as span:
        set_span_attributes(span, {
            "stripe.operation": "create_customer",
            "customer.email_domain": email.split('@')[1]  # Sanitize
        })
        # Existing code
```

Methods needing telemetry:
- `create_customer()`
- `create_checkout_session()`
- `create_portal_session()`
- `cancel_subscription()`
- `construct_webhook_event()`

---

### 4. web/backend/billing/middleware.py

**Priority:** High (subscription enforcement)  
**Functions to Instrument:**

```python
from shared.utils.telemetry import get_tracer, set_span_attributes

def check_subscription(user_id, required_plan):
    tracer = get_tracer()
    with tracer.start_as_current_span("billing.check_subscription") as span:
        set_span_attributes(span, {
            "user.id": user_id,
            "subscription.required_plan": required_plan
        })
        # Check logic
```

---

## Phase 3: Storage & Training Services

### 1. web/backend/storage/gdrive_handler.py

**File Size:** 527 lines  
**Priority:** Medium

#### Methods to Instrument:

1. **get_authorization_url()** (Line ~140)
   - Track OAuth initiation
   - Monitor redirect URLs

2. **handle_oauth_callback()** (Line ~175)
   - Track token exchange success/failure
   - Monitor callback errors

3. **upload_file()** (Line ~235)
   - Track upload sizes, times
   - Monitor rate limits, quotas

4. **download_file()** (Line ~324)
   - Track download sizes, times
   - Monitor errors by type

---

### 2. web/backend/storage/dropbox_handler.py

**File Size:** 535 lines  
**Priority:** Medium  
**Pattern:** Mirror gdrive_handler.py implementation

---

### 3. Training Services (3 files)

#### web/backend/training/hf_trainer.py
```python
def start_training(self, dataset, config):
    tracer = get_tracer()
    with tracer.start_as_current_span("training.huggingface.start") as span:
        set_span_attributes(span, {
            "training.platform": "huggingface",
            "training.dataset_size": len(dataset),
            "training.epochs": config.get('epochs')
        })
```

Methods to instrument:
- `start_training()`
- `get_training_status()`
- `download_model()`
- Track costs, training time, success rate

#### web/backend/training/replicate_trainer.py
- Similar pattern to HF trainer
- Track Replicate-specific metrics

#### web/backend/training/runpod_trainer.py
- Track GPU allocation
- Monitor pod lifecycle
- Track GPU costs

---

## Phase 4: Authentication & Database

### 1. web/backend/routes.py (Login/Refresh)

**Already Done:** Registration endpoint  
**Remaining:**

```python
@app.route('/api/auth/login', methods=['POST'])
@rate_limit(requests=5, window=60)  # 5 attempts per minute
def login():
    tracer = get_tracer()
    with tracer.start_as_current_span("api.auth.login") as span:
        set_span_attributes(span, {
            "operation.type": "login",
            "auth.method": "password"
        })
        # Track failed attempts
        # Monitor suspicious patterns
```

---

### 2. web/backend/database.py

**Priority:** Low  
**Focus:** Query performance monitoring

```python
from shared.utils.telemetry import get_tracer, set_span_attributes

def execute_query(query, params):
    tracer = get_tracer()
    with tracer.start_as_current_span("database.query") as span:
        set_span_attributes(span, {
            "db.operation": query.split()[0],  # SELECT, INSERT, etc.
            "db.table": extract_table_name(query)
        })
        start = time.time()
        result = db.execute(query, params)
        set_span_attributes(span, {
            "db.duration_ms": (time.time() - start) * 1000
        })
        return result
```

---

## Testing Requirements

### 1. Telemetry Span Tests

```python
def test_endpoint_creates_span():
    """Verify telemetry span is created for endpoint"""
    from unittest.mock import patch
    
    with patch('shared.utils.telemetry.get_tracer') as mock_tracer:
        mock_span = MagicMock()
        mock_tracer.return_value.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        # Call endpoint
        response = client.post('/api/extract', data={'image': test_image})
        
        # Verify span was created
        mock_tracer.return_value.start_as_current_span.assert_called_once()
        assert mock_span.set_attribute.called
```

### 2. Rate Limiting Tests

```python
def test_rate_limit_enforcement():
    """Verify rate limit is enforced"""
    for i in range(6):  # One over limit
        response = client.post('/api/extract', data={'image': test_image})
        if i < 5:
            assert response.status_code == 200
        else:
            assert response.status_code == 429  # Rate limited
```

### 3. Input Validation Tests

```python
def test_file_upload_validation():
    """Verify file upload validation"""
    # Test invalid file type
    response = client.post('/api/extract', data={
        'image': ('test.txt', b'not an image', 'text/plain')
    })
    assert response.status_code == 400
    assert 'not allowed' in response.json['error']
```

---

## Rate Limiting Guidelines

| Operation Type | Rate Limit | Window | Justification |
|---------------|-----------|--------|---------------|
| **Free Tier Extract** | 10 | 1 hour | Prevent abuse |
| **Single Extract** | 100 | 1 hour | Normal usage |
| **Batch Extract** | 10 | 1 hour | Resource intensive |
| **Batch Multi** | 5 | 1 hour | Very resource intensive |
| **Stream Extract** | 20 | 1 hour | Connection-intensive |
| **Finetune Prepare** | 3 | 1 hour | CPU/disk intensive |
| **Finetune Start** | 2 | 1 hour | Very expensive |
| **Checkout Create** | 5 | 1 hour | Prevent spam |
| **Auth Login** | 5 | 1 minute | Brute force protection |
| **Cloud Download** | 30 | 1 hour | API quota limits |

---

## Span Attribute Standards

### Common Attributes

```python
{
    "operation.type": "extract|batch|finetune|auth|billing",
    "user.id": user_id,  # When authenticated
    "client.ip": request.remote_addr
}
```

### File Operations

```python
{
    "file.name": sanitized_filename,
    "file.size": file_size_bytes,
    "file.type": file_extension
}
```

### Model Operations

```python
{
    "model.id": model_identifier,
    "model.type": "donut|florence|easyocr|paddle",
    "extraction.processing_time": seconds,
    "extraction.confidence": 0-100,
    "extraction.items_count": count
}
```

### Billing Operations

```python
{
    "billing.plan": "free|pro|business",
    "billing.operation": "checkout|cancel|webhook",
    "stripe.customer_id": customer_id[:8] + "...",  # Truncated
    "stripe.session_id": session_id[:8] + "..."     # Truncated
}
```

### Error Attributes

```python
{
    "error.type": exception_class_name,
    "error.message": sanitize_error_message(str(e))
}
```

---

## Success Metrics

### Phase 1 Complete When:
- ✅ All app.py endpoints instrumented (11 endpoints)
- ✅ All billing endpoints instrumented (7 endpoints) - DONE
- ✅ WebSocket handlers instrumented (5 handlers) - DONE
- ⏳ Core model processors instrumented (4 processors)

### Phase 2 Complete When:
- ✅ All spatial OCR methods instrumented (6 methods)
- ✅ CRAFT detector instrumented
- ✅ Billing handlers instrumented (stripe_handler, middleware)

### Phase 3 Complete When:
- ✅ Storage handlers instrumented (gdrive, dropbox)
- ✅ Training services instrumented (3 trainers)

### Phase 4 Complete When:
- ✅ Auth endpoints instrumented
- ✅ Database queries monitored

### Overall Success:
- 📊 **100% endpoint coverage** (all public endpoints)
- 🔒 **100% rate limiting** (all user-facing endpoints)
- 🔍 **100% model visibility** (all extraction methods)
- 💳 **100% billing visibility** (all payment flows)

---

## Troubleshooting

### Issue: Import Error - OpenTelemetry Not Available

**Solution:** Code is designed to work without OpenTelemetry. No-op tracer is returned.

```python
# No action needed - telemetry is optional
# Verify with:
from shared.utils.telemetry import get_tracer
tracer = get_tracer()  # Returns no-op if OTel not available
```

### Issue: Rate Limiter Not Working

**Check:**
1. Is rate limiter initialized? `from web.backend.security.rate_limiting import create_limiter`
2. Backend configured? Check `RATE_LIMIT_BACKEND` env var
3. Redis available? Falls back to memory if Redis not available

### Issue: Span Attributes Not Appearing

**Check:**
1. Are you setting attributes correctly? Use `set_span_attributes(span, {...})`
2. Are values JSON-serializable? Strings, numbers, booleans only
3. Are you sanitizing PII? Use `sanitize_attributes()` for sensitive data

---

## Next Steps

1. **Immediate:** Complete remaining app.py endpoints (finetune, cloud, batch-multi, stream)
2. **Next:** Instrument model processors in engine.py
3. **Then:** Add telemetry to spatial_ocr.py
4. **Finally:** Complete storage handlers and training services

---

**Last Updated:** 2025-12-07  
**Progress:** 35% Complete (3 files fully done, 2 partially done, 17 remaining)  
**Target Date:** Phase 1 complete within 2-3 days
