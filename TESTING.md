# Testing Guide

## Automated Test Runners

This project includes automated test runners that handle cache clearing and environment verification automatically.

### ✨ Features

- **Automatic cache cleanup** - Clears Python bytecode and pytest cache before running tests
- **Environment verification** - Checks that pytest and dependencies are installed
- **Detailed reporting** - Shows test results, coverage, and error details
- **Windows & Linux support** - Works on both platforms

---

## Quick Start

### Windows

**Run all tests:**
```cmd
run_tests.bat
```

**Run DonutProcessor tests only:**
```cmd
run_donut_tests.bat
```

### Linux/Mac

**Run all tests:**
```bash
python run_all_tests.py
```

**Run DonutProcessor tests only:**
```bash
python run_donut_tests.py
```

---

## Test Suites

### 1. Full Test Suite (`run_all_tests.py`)

Runs all test suites with comprehensive reporting:
- System health checks
- Image processing tests
- Model manager tests
- Base processor tests
- EasyOCR processor tests
- PaddleOCR processor tests
- **DonutProcessor tests** ✨ (Fixed)
- API tests

**Output includes:**
- Pass/fail status for each suite
- Test coverage percentages
- Detailed error messages
- Test logs saved to `logs/test-reports/`
- HTML coverage reports saved to `htmlcov/`

### 2. Quick DonutProcessor Test (`run_donut_tests.py`)

Fast runner for DonutProcessor tests specifically:
- Clears cache automatically
- Shows detailed test output
- Perfect for quick validation after code changes

---

## What Gets Cleaned Automatically

Before each test run, the following are automatically cleared:

1. **`__pycache__` directories** - Python bytecode cache
2. **`*.pyc` files** - Compiled Python files
3. **`.pytest_cache`** - Pytest cache directory
4. **`.coverage`** - Coverage data file

This ensures tests always run with fresh code and aren't affected by stale cache.

---

## Manual Testing

If you prefer manual control:

```bash
# Clear cache manually
rm -rf .pytest_cache __pycache__ tests/__pycache__ tests/shared/__pycache__
find . -type f -name "*.pyc" -delete

# Run specific test file
python -m pytest tests/shared/test_donut_processor.py -v

# Run specific test function
python -m pytest tests/shared/test_donut_processor.py::test_donut_processor_initialization -v

# Run with coverage
python -m pytest tests/shared/test_donut_processor.py -v --cov=shared --cov-report=html
```

---

## Understanding Test Results

### Exit Codes

- `0` - All tests passed ✅
- `1` - Some tests failed ❌
- `130` - Tests interrupted by user

### Test Status

- ✅ **PASS** - Test passed successfully
- ❌ **FAIL** - Test failed
- **[CRITICAL]** - Critical test (must pass for production)

### Coverage Reports

After running tests, view coverage reports:

```bash
# Open HTML coverage report
open htmlcov/index.html  # Mac
start htmlcov/index.html # Windows
xdg-open htmlcov/index.html # Linux
```

---

## Recent Fixes Applied ✨

### DonutProcessor Tests (Fixed)

The following issues were resolved:

1. **Mock tokenizer `len()` support** - Added `__len__` to mock tokenizers
2. **Method reference fixes** - Corrected `_safe_extract_string` references
3. **Method binding** - Fixed instance method binding in tests
4. **Retry logic** - Fixed mock side effects for retry tests

**All 20 DonutProcessor tests now pass!**

### GPU Check Script (Fixed)

Fixed encoding error on Windows:
- Replaced Unicode box-drawing characters with ASCII
- Added UTF-8 encoding handler for Windows
- No more `UnicodeEncodeError`

---

## Troubleshooting

### Tests show old errors

If you see old test failures after pulling new code:
```bash
# Use the automated test runner - it clears cache automatically
python run_donut_tests.py
```

### "pytest not found"

Install test dependencies:
```bash
pip install pytest pytest-cov pytest-flask pytest-mock
```

### "Tests timed out"

Some tests may take longer on CPU-only systems:
- DonutProcessor tests: ~30 seconds
- Full test suite: ~2-3 minutes

---

## CI/CD Integration

For continuous integration, use:

```bash
python run_all_tests.py
```

The script will:
1. Verify environment
2. Clear caches
3. Run all tests
4. Generate reports
5. Exit with appropriate code (0=success, 1=failure)

---

## Test Coverage Goals

Current coverage by module:
- EasyOCR Processor: **95%** ✅
- Base Processor: **93%** ✅
- Paddle Processor: **89%** ✅
- Model Manager: **79%** ✅
- DonutProcessor: **60%** 🎯
- API: **30%** 🎯

Target: **80%+ coverage** for all modules

---

## Contributing

When adding new tests:

1. Follow existing test patterns
2. Use descriptive test names
3. Add docstrings explaining what's tested
4. Update `run_all_tests.py` if adding new test files
5. Run full test suite before committing

---

## Need Help?

- Check test logs in `logs/test-reports/`
- View coverage reports in `htmlcov/`
- Review error messages in console output
- Check this guide for common issues

**Happy Testing! 🧪**
