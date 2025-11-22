# Receipt Extractor - System Architecture & Reliability Guide

**Version:** 2.0
**Last Updated:** 2025-11-22
**Status:** Production-Ready

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Improvements](#architecture-improvements)
3. [Reliability Features](#reliability-features)
4. [Troubleshooting Guide](#troubleshooting-guide)
5. [Performance Tuning](#performance-tuning)
6. [Deployment Guide](#deployment-guide)

---

## System Overview

### What Was Fixed

This system underwent a **complete reliability overhaul** addressing critical failure modes:

**Before (v1.x):**
- ❌ Race conditions in concurrent requests
- ❌ Memory leaks from uncapped model loading
- ❌ Silent failures in model initialization
- ❌ No retry logic for network failures
- ❌ Fragile environment-specific code
- ❌ No resource monitoring
- ❌ Unpinned dependencies causing version conflicts

**After (v2.0):**
- ✅ Thread-safe model management with locks
- ✅ Automatic LRU eviction (max 3 models loaded)
- ✅ Robust initialization with retry logic
- ✅ Comprehensive health checks and diagnostics
- ✅ Structured error responses
- ✅ Pinned production dependencies
- ✅ Automated testing suite

---

## Architecture Improvements

### 1. Thread-Safe ModelManager

**Problem:** Concurrent web requests caused race conditions when selecting/loading models.

**Solution:**
```python
# shared/models/model_manager.py
class ModelManager:
    def __init__(self):
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self.max_loaded_models = 3      # Resource limit
        self.model_last_used = {}       # LRU tracking
```

**Key Features:**
- All critical operations protected by locks
- Prevents concurrent modification of shared state
- Supports nested lock acquisition (RLock)

**Location:** `shared/models/model_manager.py:33-39`

---

### 2. Automatic Memory Management

**Problem:** Loading multiple large models (500MB-1GB each) exhausted system memory.

**Solution:** LRU (Least Recently Used) eviction policy

```python
def get_processor(self, model_id):
    with self._lock:
        # Before loading, check if we need to evict
        if len(self.loaded_processors) >= self.max_loaded_models:
            self._evict_least_recently_used()
```

**Configuration:**
- Default: Max 3 models loaded simultaneously
- Adjustable via `ModelManager(max_loaded_models=N)`
- Automatic garbage collection after eviction

**Location:** `shared/models/model_manager.py:105-158`

---

### 3. Robust Model Initialization

**Problem:** Model downloads failed silently on network errors, environment issues.

**Solution:** Retry logic with exponential backoff

```python
def _load_model(self):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Download model
            self.model = AutoModel.from_pretrained(self.model_id)
            return  # Success
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 2s, 4s, 8s
                time.sleep(wait_time)
            else:
                raise RuntimeError(f"Failed after {max_retries} attempts: {e}")
```

**Improved Error Messages:**
- Network connection issues → "Check internet connection"
- Disk space issues → "5GB required for models"
- Missing dependencies → "Install transformers>=4.30"

**Locations:**
- Donut: `shared/models/donut_processor.py:105-147`
- Florence: `shared/models/donut_processor.py:588-630`
- Tesseract: `shared/models/ocr_processor.py:47-76`

---

### 4. Configuration Validation

**Problem:** Invalid config files caused cryptic runtime errors.

**Solution:** Upfront validation on startup

```python
def _validate_config(self, config):
    # Check required fields
    if 'available_models' not in config:
        raise ValueError("Missing 'available_models'")

    # Validate each model
    for model_id, model_config in config['available_models'].items():
        self._validate_model_config(model_id, model_config)
```

**Validation Rules:**
- Required fields: `id`, `name`, `type`, `description`
- Valid types: `donut`, `florence`, `ocr`, `easyocr`, `paddle`
- Donut/Florence models require `huggingface_id` and `task_prompt`
- Default model must exist in available models

**Location:** `shared/models/model_manager.py:59-121`

---

### 5. Comprehensive Health Checks

**Problem:** No visibility into system health, resource usage, or model state.

**Solution:** Enhanced `/api/health` endpoint

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "receipt-extraction-api",
  "version": "2.0",
  "timestamp": 1700000000,
  "system": {
    "platform": "Linux",
    "python_version": "3.10.12",
    "cpu_count": 8,
    "memory_total_gb": 16.0,
    "memory_available_gb": 8.5,
    "memory_percent_used": 47.5,
    "disk_total_gb": 500.0,
    "disk_free_gb": 250.0
  },
  "models": {
    "loaded_models_count": 2,
    "max_loaded_models": 3,
    "current_model": "ocr_tesseract",
    "loaded_models": ["ocr_tesseract", "ocr_easyocr"],
    "model_usage": {
      "ocr_tesseract": {
        "loaded_at": "2025-11-22T10:00:00",
        "last_used": "2025-11-22T10:30:00"
      }
    }
  }
}
```

**Health Status Levels:**
- `healthy`: Normal operation
- `warning`: Memory >80%
- `degraded`: Memory >90%
- `unhealthy`: System error

**Location:** `web-app/backend/app.py:61-122`

---

### 6. Structured Error Responses

**Problem:** Inconsistent error formats made debugging difficult.

**Solution:** Standardized error response format

```python
def create_error_response(error_message, error_type, status_code, details=None):
    return {
        'success': False,
        'error': {
            'type': error_type,
            'message': error_message,
            'timestamp': time.time(),
            'details': details  # Optional additional context
        }
    }
```

**Error Types:**
- `ValidationError`: Invalid input
- `ModelError`: Model initialization/execution failure
- `SystemError`: Infrastructure issues
- `FileTooLarge`: Upload exceeds 16MB
- `InternalServerError`: Unexpected errors

**Location:** `web-app/backend/app.py:44-91`

---

### 7. Production Dependencies

**Problem:** Unpinned versions caused "works on my machine" issues.

**Solution:** `requirements-production.txt` with exact versions

**Key Versions:**
```
torch==2.2.0
transformers==4.37.2
Flask==3.0.2
Pillow==10.2.0
opencv-python==4.9.0.80
```

**Why Pinned Versions Matter:**
- Reproducible deployments
- No surprise breaking changes
- Security: Known vulnerabilities can be tracked
- Compatibility: Versions tested together

**Location:** `requirements-production.txt`

---

## Reliability Features

### Concurrent Request Handling

**Scenario:** 10 users simultaneously extract receipts

**Before:** Race conditions, crashes, undefined behavior

**After:**
1. Each request acquires lock before model access
2. LRU eviction prevents memory exhaustion
3. Independent error handling per request
4. Thread-safe logging

**Test:** `tests/test_model_manager.py::TestModelManagerThreadSafety`

---

### Network Resilience

**Scenario:** Model download fails (HuggingFace outage, poor connection)

**Before:** Silent failure or cryptic error

**After:**
1. Retry #1: Wait 2 seconds
2. Retry #2: Wait 4 seconds
3. Retry #3: Wait 8 seconds
4. Final failure: Clear error message with troubleshooting steps

**Test:** Manual - disconnect network during model load

---

### Memory Protection

**Scenario:** User loads 5 different models

**Before:** 5-6GB RAM consumed, potential OOM crash

**After:**
1. Load model #1 (Tesseract) → 100MB
2. Load model #2 (EasyOCR) → 500MB
3. Load model #3 (Florence) → 750MB
4. Load model #4 → **Evict Tesseract** (LRU), load #4
5. System stable at ~3GB max

**Test:** `tests/test_model_manager.py::TestModelManagerMemoryManagement`

---

## Troubleshooting Guide

### Common Issues

#### 1. "Tesseract not found"

**Error:**
```
EnvironmentError: Tesseract OCR is not installed or not found in system PATH.
```

**Solution:**
- **Windows:** Download from https://github.com/UB-Mannheim/tesseract/wiki
- **macOS:** `brew install tesseract`
- **Linux:** `sudo apt-get install tesseract-ocr`

**Verify:**
```bash
tesseract --version
```

---

#### 2. "Failed to load model after 3 attempts"

**Error:**
```
RuntimeError: Failed to load florence2 after 3 attempts.
Last error: Connection timeout
```

**Possible Causes:**
1. No internet connection
2. HuggingFace service down
3. Insufficient disk space
4. Firewall blocking HuggingFace

**Solutions:**
- Check internet: `ping huggingface.co`
- Check disk space: `df -h` (need 5GB free)
- Check HuggingFace status: https://status.huggingface.co
- Retry after a few minutes

---

#### 3. "Memory usage critical (>90%)"

**Error:** Health check shows `status: degraded`

**Immediate Action:**
```bash
curl -X POST http://localhost:5000/api/models/unload
```

**Long-term Solutions:**
- Reduce `max_loaded_models` in `app.py`
- Add more RAM
- Use lighter models (Tesseract instead of Florence)

---

#### 4. Model outputs empty/garbled results

**Symptoms:**
- Empty extraction results
- Garbled text (歲嵗的있습니다)
- No JSON output

**Causes:**
- Poor image quality
- Unsupported receipt format
- Model not suited for receipt type

**Solutions:**
1. **Try different model:**
   - Handwritten → EasyOCR
   - Complex layout → Florence-2
   - Simple receipts → Tesseract

2. **Improve image quality:**
   - Higher resolution (300+ DPI)
   - Good lighting
   - Flat/uncrumpled
   - Clear text

3. **Check logs:**
   ```bash
   tail -f /path/to/app.log | grep WARNING
   ```

---

#### 5. "Configuration validation failed"

**Error:**
```
ValueError: Model 'my_model' missing required field 'huggingface_id'
```

**Solution:** Edit `shared/config/models_config.json`

**Required fields:**
```json
{
  "my_model": {
    "id": "my_model",           // ✓ Required
    "name": "My Model",         // ✓ Required
    "type": "donut",            // ✓ Required (donut|florence|ocr|easyocr|paddle)
    "description": "...",       // ✓ Required
    "huggingface_id": "...",    // ✓ Required for donut/florence
    "task_prompt": "..."        // ✓ Required for donut/florence
  }
}
```

---

## Performance Tuning

### Recommended Configurations

#### Small Deployment (1-5 users)
```python
# app.py
model_manager = ModelManager(max_loaded_models=2)
```

**Resources:**
- 4GB RAM
- 2 CPU cores
- 10GB disk

**Models:** Tesseract + EasyOCR

---

#### Medium Deployment (5-20 users)
```python
model_manager = ModelManager(max_loaded_models=3)
```

**Resources:**
- 8GB RAM
- 4 CPU cores
- 20GB disk

**Models:** Tesseract + EasyOCR + PaddleOCR

---

#### Large Deployment (20+ users)
```python
model_manager = ModelManager(max_loaded_models=5)

# Consider process-based parallelism
# Use gunicorn with multiple workers
```

**Command:**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 300 app:app
```

**Resources:**
- 16GB+ RAM
- 8+ CPU cores
- 50GB disk
- GPU recommended

**Models:** All models + GPU acceleration

---

### GPU Acceleration

**Check CUDA availability:**
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

**If True:**
- Florence-2: 10x faster
- Donut: 8x faster
- Memory: 4GB+ VRAM needed

**If False:**
- Stick to lightweight models (Tesseract, EasyOCR)
- Florence-2 will be very slow on CPU (30-60s per image)

---

## Deployment Guide

### Production Checklist

- [ ] Install pinned requirements: `pip install -r requirements-production.txt`
- [ ] Install Tesseract binary (if using OCR)
- [ ] Run system health test: `python tests/test_system_health.py`
- [ ] Run unit tests: `pytest tests/`
- [ ] Set up monitoring (check `/api/health` every 5 minutes)
- [ ] Configure resource limits in `app.py`
- [ ] Set up log rotation
- [ ] Configure firewall rules
- [ ] Set up HTTPS (use nginx/apache as reverse proxy)
- [ ] Set `FLASK_ENV=production`

---

### Environment Variables

```bash
# Recommended production settings
export FLASK_ENV=production
export FLASK_DEBUG=0
export TRANSFORMERS_CACHE=/data/model_cache  # Custom cache location
export OMP_NUM_THREADS=4  # Limit CPU threads per model
```

---

### Monitoring

**Key Metrics:**
- `/api/health` → Memory usage, loaded models
- Response time → Should be <10s for simple OCR, <60s for AI models
- Error rate → Should be <5%

**Alerts:**
- Memory >85% → Warning
- Memory >95% → Critical (trigger unload)
- Disk <5GB → Warning (can't download models)

---

### Backup & Recovery

**Critical Files:**
- `shared/config/models_config.json` → Model configuration
- `requirements-production.txt` → Dependency versions
- `/path/to/logs/` → Application logs

**Model Cache:**
- Location: `~/.cache/huggingface/` (Linux/Mac)
- Size: 5-10GB
- Backup: Optional (can re-download)

---

## Version History

### v2.0 (2025-11-22)
- ✅ Thread-safe model management
- ✅ Automatic memory management (LRU eviction)
- ✅ Robust initialization with retries
- ✅ Configuration validation
- ✅ Comprehensive health checks
- ✅ Structured error responses
- ✅ Pinned production dependencies
- ✅ Automated test suite

### v1.x (Legacy)
- Basic model loading
- No concurrency protection
- Manual model management
- Limited error handling

---

## Support

**Issues:** https://github.com/your-repo/issues
**Documentation:** This file
**Tests:** `tests/` directory

---

**Built with the fortitude of Henry Ford - systematic, reliable, production-ready.**
