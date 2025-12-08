# Testing Strategy and Quality Standards

**Last Updated**: 2025-12-08  
**Status**: 🟢 Active Development  
**Coverage Target**: 70% minimum for new code

---

## Overview

This document outlines the testing strategy for the Receipt Extractor project, including test organization, quality standards, and CI/CD integration.

---

## Test Organization

### Directory Structure

```
tools/tests/
├── conftest.py                    # Pytest configuration and fixtures
├── __init__.py
├── shared/                        # Shared module tests
│   ├── test_utils.py
│   ├── test_models.py
│   └── test_circular_exchange.py
├── backend/                       # Backend tests
│   ├── test_api_routes.py
│   ├── test_auth.py
│   └── test_billing.py
├── integration/                   # Integration tests (end-to-end)
│   ├── test_extraction_workflow.py
│   ├── test_auth_flow.py
│   └── test_payment_flow.py
├── test_backend_routes.py         # Legacy backend route tests
├── test_billing.py                # Billing integration tests
└── test_integration.py            # Cross-module integration
```

### Test Categories

Tests are organized using pytest markers:

```python
@pytest.mark.unit           # Fast, isolated unit tests
@pytest.mark.integration    # Multi-component integration tests
@pytest.mark.model          # ML model tests (may require GPU)
@pytest.mark.slow           # Tests taking >5 seconds
@pytest.mark.web            # Web application tests
@pytest.mark.skip_ci        # Skip in CI (require external services)
```

---

## Quality Standards

### 1. Code Coverage

**Minimum Requirements**:
- New code: **70%+ coverage**
- Critical modules: **80%+ coverage**
- Legacy code: **No decrease** in coverage

**Measured By**:
```bash
pytest --cov=shared --cov=web/backend --cov-report=term-missing
```

**Critical Modules** (80%+ required):
- `shared/models/` - Model processors
- `web/backend/auth.py` - Authentication
- `web/backend/billing/` - Payment processing
- `shared/circular_exchange/` - CEFR framework

### 2. Test Quality Principles

#### ✅ DO:

1. **Test Real Behavior**
   ```python
   # Good: Tests actual extraction
   def test_ocr_extracts_total():
       result = process_receipt("receipt.jpg")
       assert "total" in result.metadata
       assert result.metadata["total"] > 0
   ```

2. **Use Descriptive Names**
   ```python
   def test_authentication_fails_with_invalid_token():
       # Clear what's being tested
   ```

3. **Isolate Tests**
   ```python
   # Each test is independent
   def test_upload_success(tmp_path):
       file_path = tmp_path / "test.jpg"
       # ... test logic
   ```

4. **Mock External Services**
   ```python
   @patch('requests.post')
   def test_stripe_payment(mock_post):
       mock_post.return_value.status_code = 200
       # ... test logic
   ```

#### ❌ DON'T:

1. **Skip for Missing Functions**
   ```python
   # BAD: Delete this test instead
   def test_removed_function():
       pytest.skip("Function was removed")
   ```

2. **Test Implementation Details**
   ```python
   # BAD: Tests internal variable name
   def test_internal_variable():
       obj = MyClass()
       assert obj._internal_var == "value"
   ```

3. **Ignore Test Failures**
   ```python
   # BAD: Hiding failures
   try:
       dangerous_operation()
   except:
       pass  # Never do this in tests
   ```

4. **Depend on Test Order**
   ```python
   # BAD: Test B depends on Test A running first
   global_state = None
   def test_a():
       global global_state
       global_state = "set"
   def test_b():
       assert global_state == "set"  # Fragile!
   ```

---

## Critical Testing Rules

### 🔴 MANDATORY: Fix Syntax Before Testing

**Rule**: All Python files must compile before tests run.

**Validation**:
```bash
# Run before any testing
python tools/scripts/validate_imports.py
```

**Why**: Syntax errors prevent test discovery and give false confidence.

### 🔴 MANDATORY: No Skip for Missing Functions

**Rule**: If a function is removed, DELETE or UPDATE the test. Never skip.

**Bad**:
```python
def test_function_that_no_longer_exists():
    pytest.skip("Function removed")  # ❌ DELETE THIS TEST
```

**Good**:
```python
# Test deleted entirely when function removed
# OR updated to test the replacement function
def test_new_replacement_function():
    result = new_function()
    assert result.success
```

**Enforcement**: CI checks for skipped tests with "removed" or "missing" in skip reason.

### 🔴 MANDATORY: Update Tests on Rename

**Rule**: When renaming functions, update ALL test imports and calls.

**Process**:
```bash
# 1. Find all test references
grep -r "old_function_name" tools/tests/

# 2. Update each file
sed -i 's/old_function_name/new_function_name/g' tools/tests/*.py

# 3. Verify tests still pass
pytest tools/tests/ -v
```

---

## Test Execution

### Local Development

```bash
# Quick validation (syntax + critical imports)
python tools/scripts/validate_imports.py

# Run all tests with coverage
pytest tools/tests/ --cov=shared --cov=web/backend

# Run specific test category
pytest -m unit                    # Only unit tests (fast)
pytest -m integration             # Integration tests
pytest -m "not slow"              # Skip slow tests

# Run specific file
pytest tools/tests/test_billing.py -v
```

### CI/CD Pipeline

Tests run automatically on:
- **Pull Requests** to main/develop
- **Pushes** to main/develop

**Pipeline Stages** (`.github/workflows/quality-gates.yml`):

1. **Syntax Check** (BLOCKING)
   ```bash
   python -m py_compile **/*.py
   ```

2. **Import Validation** (BLOCKING)
   ```bash
   python tools/scripts/validate_imports.py
   ```

3. **Linting** (WARNING)
   ```bash
   flake8 . --max-line-length=100
   ```

4. **Test Suite** (IMPROVING)
   ```bash
   pytest --cov=shared --cov=web/backend --cov-report=xml
   ```

5. **Security Scan** (WARNING)
   ```bash
   bandit -r shared/ web/
   ```

---

## Integration Tests

### Purpose

Integration tests validate **end-to-end workflows** that cross module boundaries.

### Location

`tools/tests/integration/` - To be created

### Required Integration Tests

1. **Extraction Workflow**
   ```python
   def test_full_extraction_workflow():
       # Upload image → Process → Return structured data
       image = load_test_image()
       result = api.post('/extract', files={'image': image})
       assert result.status_code == 200
       assert 'total' in result.json()['data']
   ```

2. **Authentication Flow**
   ```python
   def test_auth_flow():
       # Register → Login → Access protected endpoint
       register_response = api.post('/auth/register', json=user_data)
       login_response = api.post('/auth/login', json=credentials)
       token = login_response.json()['access_token']
       
       protected = api.get('/receipts', headers={'Authorization': f'Bearer {token}'})
       assert protected.status_code == 200
   ```

3. **Payment Flow** (if Stripe configured)
   ```python
   @pytest.mark.skipif(not STRIPE_CONFIGURED, reason="Stripe not configured")
   def test_subscription_upgrade():
       # Login → View plans → Subscribe → Verify access
       # Uses Stripe test mode
   ```

---

## Mocking Strategy

### When to Mock

✅ **Mock external services**:
- HTTP APIs (Stripe, HuggingFace, etc.)
- Cloud storage (S3, Google Drive, Dropbox)
- Email sending
- External databases

✅ **Mock slow operations**:
- Model inference (use cached results)
- Large file uploads
- Network requests

❌ **Don't mock**:
- Internal functions (test real behavior)
- Simple utilities
- Database operations (use test DB instead)

### Mock Examples

**HTTP Requests**:
```python
@patch('requests.post')
def test_api_call(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"success": True}
    
    result = make_api_call()
    assert result["success"]
    mock_post.assert_called_once()
```

**File System**:
```python
def test_file_upload(tmp_path):
    # Use pytest's tmp_path fixture for real files
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    result = upload_file(str(test_file))
    assert result.success
```

---

## Coverage Reporting

### Generate Coverage Report

```bash
# HTML report (detailed, per-file)
pytest --cov=shared --cov=web/backend --cov-report=html
open htmlcov/index.html

# Terminal report (quick summary)
pytest --cov=shared --cov=web/backend --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=shared --cov=web/backend --cov-report=xml
```

### CI Integration

Coverage reports are:
- Generated on every PR
- Uploaded to Codecov (optional)
- Displayed in PR comments (if Codecov configured)
- **Blocking** if coverage decreases

---

## Test Fixtures

### Shared Fixtures (`conftest.py`)

```python
@pytest.fixture
def test_image():
    """Load a standard test receipt image."""
    return Image.open("examples/receipts/0.jpg")

@pytest.fixture
def mock_database():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    # ... setup
    yield session
    # ... teardown

@pytest.fixture
def authenticated_client():
    """Flask test client with valid JWT token."""
    client = app.test_client()
    token = create_test_token()
    client.set_cookie('access_token', token)
    return client
```

---

## Debugging Failed Tests

### 1. Increase Verbosity

```bash
pytest -vv --tb=long
```

### 2. Run Single Test

```bash
pytest tools/tests/test_file.py::test_specific_function -vv
```

### 3. Print Debug Info

```python
def test_something():
    result = function_under_test()
    print(f"Result: {result}")  # Will show if test fails
    assert result.success
```

### 4. Use Debugger

```bash
pytest --pdb  # Drop into debugger on failure
```

---

## Continuous Improvement

### Test Metrics to Track

1. **Coverage Trend**: Should increase over time
2. **Test Count**: ~1,055 tests (growing)
3. **Flaky Tests**: Identify and fix tests that randomly fail
4. **Test Duration**: Keep total runtime under 5 minutes

### Review Process

**Before Merging PR**:
- [ ] All tests pass
- [ ] Coverage not decreased
- [ ] New code has tests (70%+ coverage)
- [ ] No new syntax errors
- [ ] No skipped tests for "missing" functions

---

## Quick Reference

### Common Commands

```bash
# Validate before testing
python tools/scripts/validate_imports.py

# Fast test run (unit tests only)
pytest -m unit

# Full test suite with coverage
pytest --cov=shared --cov=web/backend --cov-report=term-missing

# Test specific module
pytest tools/tests/shared/

# Update snapshots (if using snapshot testing)
pytest --snapshot-update

# Run in parallel (faster)
pytest -n auto
```

### Useful Markers

```python
@pytest.mark.unit          # Fast unit test
@pytest.mark.integration   # Integration test
@pytest.mark.slow          # >5 second test
@pytest.mark.skip_ci       # Skip in CI
@pytest.mark.parametrize   # Run with multiple inputs
```

---

## Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **Coverage.py**: https://coverage.readthedocs.io/
- **Test Organization**: See `tools/tests/TEST_ORGANIZATION.md`
- **CI Pipeline**: `.github/workflows/quality-gates.yml`

---

**Questions?** See existing tests in `tools/tests/` for examples or ask the team.
