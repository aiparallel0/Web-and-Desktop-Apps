# Changelog

All notable changes to the Receipt Extractor system.

## [2.0.0] - 2025-11-22 - STABILITY & RELIABILITY OVERHAUL

### 🎯 Summary
Complete systematic overhaul addressing all critical failure modes. Production-ready with thread safety, memory management, and comprehensive error handling.

### ✅ Added

#### Thread Safety & Concurrency
- **Thread-safe ModelManager** with RLock protection (`model_manager.py:33-39`)
- Concurrent request handling without race conditions
- Thread-safe model selection and loading
- LRU tracking with concurrent access protection

#### Memory Management
- **Automatic LRU eviction** - max 3 models loaded simultaneously
- Resource tracking: `model_last_used`, `model_load_times`
- Manual model unloading via `/api/models/unload`
- Forced garbage collection after model eviction
- Configurable `max_loaded_models` limit

#### Robust Initialization
- **Retry logic** for model downloads (3 attempts with exponential backoff)
- Donut model retry: 2s, 4s, 8s delays (`donut_processor.py:105-147`)
- Florence-2 model retry with same pattern (`donut_processor.py:588-630`)
- Tesseract validation with clear installation instructions (`ocr_processor.py:47-76`)
- Comprehensive error messages with troubleshooting steps

#### Configuration Validation
- **JSON schema validation** for `models_config.json`
- Upfront validation on ModelManager initialization
- Type checking for model configurations
- Required field validation (id, name, type, description)
- Type-specific validation (huggingface_id for donut/florence)
- Schema file: `shared/config/models_config_schema.json`

#### Health Checks & Monitoring
- **Enhanced `/api/health` endpoint** with system diagnostics
  - System info (platform, Python version, CPU count)
  - Memory metrics (total, available, percent used)
  - Disk space monitoring
  - Model resource statistics
  - Health status levels (healthy/warning/degraded/unhealthy)
- Resource stats API: `ModelManager.get_resource_stats()`
- Automatic health degradation warnings (>80% memory)

#### Error Handling
- **Structured error responses** with standardized format
  - Error type classification
  - Timestamp tracking
  - Optional detail fields
- Error types: ValidationError, ModelError, SystemError, FileTooLarge
- Global Flask error handlers (413, 500)
- Helper function: `create_error_response()`

#### Dependencies & Stability
- **Pinned production requirements** (`requirements-production.txt`)
  - All versions explicitly pinned for reproducibility
  - Core: torch==2.2.0, transformers==4.37.2, Flask==3.0.2
  - 60+ dependencies with exact versions
  - System requirements documented

#### Testing
- **Automated test suite** for ModelManager
  - Thread safety tests (concurrent operations)
  - Memory management tests (LRU eviction)
  - Configuration validation tests
  - Error handling tests
- **System health check script** (`tests/test_system_health.py`)
  - Python version check
  - Dependency verification
  - Tesseract installation check
  - Config file validation
  - Memory and disk space warnings
  - CUDA availability detection

#### Documentation
- **Comprehensive architecture guide** (`SYSTEM_ARCHITECTURE.md`)
  - Complete troubleshooting section
  - Performance tuning recommendations
  - Deployment checklist
  - Monitoring guidelines
- **Changelog** (this file)

### 🔧 Changed

#### ModelManager
- Added resource limits and LRU eviction
- Made all critical operations thread-safe
- Enhanced error messages during initialization
- Added statistics tracking for monitoring
- Configuration now validated on load

#### Web App (Flask Backend)
- Increased max_loaded_models limit from unlimited to 3
- Added comprehensive health check endpoint
- Standardized all error responses
- Added request timeout configuration (300s)
- Import time module for health checks

#### Model Processors
- Added retry logic to Donut processor
- Added retry logic to Florence-2 processor
- Tesseract now fails fast with clear errors
- Better validation of Tesseract installation
- Improved error messages across all processors

### 🐛 Fixed

#### Critical Fixes
- **Race conditions** in concurrent model selection
- **Memory leaks** from unbounded model loading
- **Silent failures** in model initialization
- **Network timeout failures** during model downloads
- **Invalid config** causing cryptic runtime errors
- **Tesseract path detection** failures

#### Reliability Fixes
- Model download failures now retry automatically
- Tesseract missing now detected at startup
- Invalid model configs rejected at load time
- Memory exhaustion prevented by LRU eviction
- Concurrent requests no longer interfere

### 📊 Performance

#### Resource Usage (Before vs After)
- **Memory:** Unbounded → Capped at ~3-4GB (3 models)
- **Disk:** Same (~5GB for model cache)
- **CPU:** Same (depends on model)
- **Concurrency:** Unsafe → Thread-safe

#### Response Times
- No change to individual request times
- Concurrent requests now safe (previously undefined behavior)

### 🔒 Security

- Dependencies pinned to known versions
- File upload size limited to 16MB
- Request timeout prevents DoS (300s)
- Memory limits prevent exhaustion attacks

### ⚠️ Breaking Changes

**None** - All changes are backward compatible with v1.x

### 📋 Migration Guide

#### From v1.x to v2.0

1. **Install new dependencies:**
   ```bash
   pip install -r requirements-production.txt
   ```

2. **No code changes required** - v2.0 is drop-in compatible

3. **Optional:** Configure resource limits
   ```python
   # In app.py, change from:
   model_manager = ModelManager()

   # To:
   model_manager = ModelManager(max_loaded_models=3)
   ```

4. **Run health check:**
   ```bash
   python tests/test_system_health.py
   ```

5. **Run tests:**
   ```bash
   pytest tests/
   ```

### 📝 Notes

#### Design Philosophy
This release applies **Henry Ford's systematic approach**:
- Identify every failure mode
- Fix root causes, not symptoms
- Test everything
- Document clearly
- Make it reproducible

#### What's NOT Changed
- Model architectures (same models)
- API endpoints (backward compatible)
- Frontend (no changes needed)
- Desktop app (benefits from shared improvements)

### 🚀 Deployment

**Production Ready:** Yes

**Recommended System:**
- Python 3.8+
- 8GB RAM
- 4 CPU cores
- 20GB disk space

**Quick Start:**
```bash
# Install dependencies
pip install -r requirements-production.txt

# Run health check
python tests/test_system_health.py

# Run tests
pytest tests/ -v

# Start server
python web-app/backend/app.py
```

### 📈 Metrics

- **Files Changed:** 8
- **Files Added:** 6
- **Lines Added:** ~2000
- **Tests Added:** 20+
- **Documentation:** 500+ lines

### 👥 Credits

Overhauled with systematic engineering approach, addressing:
- Thread safety issues
- Memory management
- Error handling
- Configuration validation
- Testing infrastructure
- Comprehensive documentation

---

## [1.x] - Legacy

Previous versions with basic functionality but reliability issues.

### Known Issues (Fixed in v2.0)
- Race conditions in model selection
- Memory leaks from unlimited model loading
- Silent initialization failures
- No retry logic for downloads
- Fragile environment detection
- Poor error messages
- Unpinned dependencies

---

**For detailed architecture and troubleshooting, see `SYSTEM_ARCHITECTURE.md`**
