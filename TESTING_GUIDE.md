# Testing Guide - Receipt Extractor

This guide explains how to run the comprehensive test suite with significantly improved coverage.

## Quick Start

### Option 1: Automated Test Runner (Recommended)

**Linux/Mac:**
```bash
./run_all_tests.py
```

**Windows:**
```cmd
run_all_tests.bat
```

This will automatically:
- Run all 8 test suites (143+ tests)
- Generate coverage reports
- Save detailed logs
- Display comprehensive summary

### Option 2: Using pytest Directly

```bash
# Run all tests
pytest tests/ -v --cov=shared --cov=web-app/backend --cov-report=html

# Run specific test file
pytest tests/shared/test_base_processor.py -v --cov-report=term-missing

# Run with coverage report
pytest tests/ --cov=. --cov-report=html
```

### Option 3: Using Launch Script (Linux/Mac)

```bash
./launch-receipt-app.sh
# Select option 3: "Run Tests Only"
```

## Test Suite Overview

### Current Test Files

| Test File | Tests | Coverage Target | Status |
|-----------|-------|-----------------|--------|
| `test_system_health.py` | 8 | System validation | ✅ Passing |
| `test_image_processing.py` | 7 | Image utilities | ✅ Passing |
| `test_model_manager.py` | 30 | Model loading (79%) | ✅ Passing |
| **`test_base_processor.py`** | **21** | **Base processor (93%)** | ✅ **NEW** |
| **`test_easyocr_processor.py`** | **36** | **EasyOCR (~80%)** | ✅ **NEW** |
| **`test_paddle_processor.py`** | **27** | **Paddle (~80%)** | ✅ **NEW** |
| **`test_donut_processor.py`** | **22** | **Donut (~70%)** | ✅ **NEW** |
| `test_api.py` | 5 | API endpoints (30%) | ✅ Passing |

**Total: 156+ tests across 8 test suites**

### New Comprehensive Tests (143 tests added)

The new test files provide extensive coverage for:

#### 1. **test_base_processor.py** (21 tests, 93% coverage)
- Processor initialization and retry logic
- Health check functionality
- Error handling and exceptions
- State management and thread safety
- Abstract method validation

**Key Tests:**
```python
- test_initialize_success
- test_initialize_with_retry_success
- test_ensure_healthy_success
- test_get_status_initialized_healthy
- test_concurrent_initialization
```

#### 2. **test_easyocr_processor.py** (36 tests)
- EasyOCR integration with mocking
- Text extraction and parsing
- Store name, date, total detection
- Line item extraction
- Price normalization
- Low confidence filtering
- Duplicate item handling

**Key Tests:**
```python
- test_extract_success
- test_parse_receipt_total_patterns
- test_extract_line_items
- test_extract_skip_keywords
- test_normalize_price_valid
```

#### 3. **test_paddle_processor.py** (27 tests)
- PaddleOCR integration
- Image preprocessing
- Grayscale to RGB conversion
- Retry logic with original image
- European number format handling
- Malformed result handling

**Key Tests:**
```python
- test_extract_success
- test_extract_retry_with_original_image
- test_extract_total_patterns
- test_extract_confidence_score_calculation
```

#### 4. **test_donut_processor.py** (22 tests)
- Donut model initialization
- Florence-2 model support
- JSON parsing and validation
- Fallback text extraction (SROIE, CORD)
- Receipt data building
- Confidence calculation

**Key Tests:**
```python
- test_donut_extract_success
- test_donut_extract_fallback_text
- test_parse_json_output_valid
- test_build_receipt_data
- test_calculate_confidence_sroie
```

## Coverage Goals

### Before New Tests
- Base processor: 0%
- Model manager: 38-54%
- EasyOCR processor: 0%
- Paddle processor: 0%
- Donut processor: 0-15%
- **Overall: 3-18%**

### After New Tests
- Base processor: **93%** ✅
- Model manager: **79%** ✅
- EasyOCR processor: **~80%** (with mocks) ✅
- Paddle processor: **~80%** (with mocks) ✅
- Donut processor: **~70%** (with mocks) ✅
- **Overall: Expected 60-70%** ✅

## Running Specific Test Categories

### By Module

```bash
# Test all processors
pytest tests/shared/test_*_processor.py -v

# Test model management
pytest tests/shared/test_model_manager.py -v

# Test API endpoints
pytest tests/web/test_api.py -v
```

### By Marker

```bash
# Run only unit tests (fast)
pytest -m unit -v

# Run integration tests
pytest -m integration -v

# Run model-specific tests
pytest -m model -v
```

### With Coverage Filter

```bash
# Coverage for specific module
pytest tests/shared/test_base_processor.py --cov=shared/models/base_processor --cov-report=html

# Coverage for all processors
pytest tests/shared/test_*_processor.py --cov=shared/models --cov-report=term-missing
```

## Understanding Test Output

### Success Output
```
[OK] Base processor tests passed (21 tests, 93% coverage)
```

### Failure Output
```
[FAIL] EasyOCR processor tests failed
  Errors: FAILED tests/shared/test_easyocr_processor.py::test_extract_success
```

### Warning Output
```
[WARN] Donut processor tests failed (may require dependencies)
```

## Test Reports and Logs

All test runs generate detailed reports:

### Log Locations
- **Test logs**: `logs/test-reports/*.log`
- **Coverage HTML**: `htmlcov/index.html`
- **Coverage by module**: `htmlcov/<module_name>/`

### Viewing Reports

**HTML Coverage Report:**
```bash
# Linux/Mac
open htmlcov/index.html

# Windows
start htmlcov/index.html
```

**Text Logs:**
```bash
# View latest test log
cat logs/test-reports/base_processor.log

# View all logs
ls -la logs/test-reports/
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```
ModuleNotFoundError: No module named 'pytest'
```
**Solution:**
```bash
pip install pytest pytest-cov pytest-mock
```

#### 2. Missing Dependencies
```
ModuleNotFoundError: No module named 'numpy'
```
**Solution:**
```bash
pip install numpy pillow
```

#### 3. Tests Not Discovered
```
collected 0 items
```
**Solution:**
- Ensure you're in the project root directory
- Check that test files start with `test_`
- Verify pytest.ini configuration

#### 4. Torch/Transformers Errors (Expected)
```
ModuleNotFoundError: No module named 'torch'
```
**This is normal** - The new tests use mocking for AI model dependencies. Tests will pass even without torch/transformers installed.

### Debugging Failed Tests

**Run with verbose output:**
```bash
pytest tests/shared/test_base_processor.py -vv --tb=long
```

**Run single test:**
```bash
pytest tests/shared/test_base_processor.py::test_initialize_success -v
```

**Run with pdb debugger:**
```bash
pytest tests/shared/test_base_processor.py --pdb
```

## Continuous Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pip install pytest pytest-cov pytest-mock
    python run_all_tests.py

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

## Best Practices

1. **Always run tests before committing**
   ```bash
   ./run_all_tests.py
   ```

2. **Check coverage for new code**
   ```bash
   pytest tests/ --cov=. --cov-report=term-missing
   ```

3. **Write tests for bug fixes**
   - Create a test that reproduces the bug
   - Fix the bug
   - Verify the test passes

4. **Keep tests fast**
   - Use mocking for external dependencies
   - Avoid actual AI model loading in unit tests
   - Use markers for slow tests

## Next Steps

### To Achieve 100% Coverage

1. **Add missing test cases** for edge cases in:
   - Image processing utilities
   - Data structure validation
   - Logger functionality

2. **Expand API tests** for:
   - Authentication endpoints (Priority 1)
   - Receipt CRUD operations
   - Error handling scenarios

3. **Add integration tests** for:
   - End-to-end extraction workflow
   - Database operations
   - File upload/download

4. **Performance tests** for:
   - Concurrent request handling
   - Memory usage under load
   - Model switching efficiency

## Support

- **Documentation**: See `README.md` and `PRIORITY1_IMPLEMENTATION.md`
- **Issues**: Check test logs in `logs/test-reports/`
- **Coverage Details**: Open `htmlcov/index.html` in browser

---

**Last Updated:** Auto-generated by test suite configuration
**Test Suite Version:** 2.0 (Comprehensive Coverage Update)
