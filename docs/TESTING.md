# Testing Guidelines

## 🎯 Core Principle: Tests Must Match Code

**Tests that skip or fail due to missing functions are WORTHLESS.** They provide no value and indicate a broken test suite.

## ✅ Test Maintenance Rules

### 1. Never Use `pytest.skip()` for Missing Functions

❌ **WRONG:**
```python
def test_some_function():
    try:
        from module import function_that_doesnt_exist
        # ...
    except ImportError:
        pytest.skip("function not available")  # <- NEVER DO THIS
```

✅ **RIGHT:**
```python
def test_some_function():
    from module import function_that_exists  # Import what EXISTS
    result = function_that_exists()
    assert result is not None
```

### 2. Delete Tests When Functions Are Removed

If `my_function` was removed from the codebase:
1. **Find all tests** that use it: `grep -r "my_function" tools/tests/`
2. **Delete or update** those tests immediately
3. **Run tests** to verify: `pytest tools/tests/ -v`

### 3. Update Tests When Functions Are Renamed

If `old_function` is renamed to `new_function`:
```bash
# Find all references
grep -r "old_function" tools/tests/

# Update each file
sed -i 's/old_function/new_function/g' tools/tests/test_*.py

# Verify
pytest tools/tests/ -v
```

### 4. Test Actual Exports Only

Check what a module actually exports before writing tests:

```python
# Check exports
import shared.utils.helpers as h
print([x for x in dir(h) if not x.startswith('_')])
```

## 📁 Test File Organization

| File | Purpose | Module Coverage |
|------|---------|-----------------|
| `test_backend.py` | Flask API endpoint tests | `web.backend.app` |
| `test_backend_routes.py` | JWT, Password, Billing | `web.backend.*` |
| `test_shared_helpers.py` | Data models, caching, logging | `shared.utils.*` |
| `test_coverage_boost.py` | Additional coverage tests | Various low-coverage modules |
| `test_analysis.py` | CEFR analysis modules | `shared.circular_exchange.analysis.*` |
| `backend/test_backend.py` | Detailed backend tests | `web.backend.*` |

## 🔄 After Every AI Prompt / Code Change

1. **Run quick tests:**
   ```bash
   pytest tools/tests/test_backend_routes.py tools/tests/test_shared_helpers.py -v
   ```

2. **Check for skips (should be 0 for core tests):**
   ```bash
   pytest tools/tests/test_backend_routes.py -v 2>&1 | grep SKIPPED | wc -l
   ```

3. **If tests fail due to missing functions:**
   - STOP and fix the test
   - Either update the import or delete the test
   - Never leave broken tests

4. **Add tests for new functions:**
   ```python
   def test_new_function():
       from module import new_function
       result = new_function("input")
       assert result == expected_output
   ```

## 📊 Coverage Goals

| Module | Target | Current |
|--------|--------|---------|
| `shared.utils.data` | 90%+ | ~88% |
| `shared.utils.helpers` | 80%+ | ~69% |
| `shared.utils.decorators` | 90%+ | ~84% |
| `web.backend.jwt_handler` | 90%+ | ~60% |
| `web.backend.password` | 95%+ | ~50% |
| `web.backend.billing.plans` | 100% | ~89% |

## 🚨 Common Mistakes to Avoid

### 1. Testing Hypothetical Functions
```python
# WRONG: Testing function that doesn't exist
def test_generate_token():
    from module import generate_token  # Doesn't exist!
```

### 2. Over-Using Try/Except/Skip
```python
# WRONG: Hiding broken tests
try:
    from module import thing
except:
    pytest.skip()  # Masks real issues
```

### 3. Not Running Tests After Changes
```python
# After renaming function_a to function_b
# MUST run: pytest -v
```

### 4. Leaving Dead Tests
```python
# WRONG: Test for removed feature still in codebase
def test_removed_feature():
    pytest.skip("Feature was removed")  # DELETE THIS ENTIRE TEST
```

## ✨ Best Practices

1. **One test file per module** (when practical)
2. **Clear test names**: `test_<function>_<scenario>`
3. **Minimal setup**: Use fixtures for complex setup
4. **Fast tests**: Avoid network calls unless integration testing
5. **Independent tests**: Each test should run in isolation

## 🛠️ Useful Commands

```bash
# Run all tests
pytest tools/tests/ -v

# Run with coverage
pytest --cov=shared --cov=web/backend --cov-report=html

# Run specific test file
pytest tools/tests/test_backend_routes.py -v

# Run specific test class
pytest tools/tests/test_shared_helpers.py::TestHelpersModule -v

# Run specific test
pytest tools/tests/test_backend_routes.py::TestJWTHandler::test_create_access_token -v

# Find skipped tests (should be minimal for core)
pytest tools/tests/ -v 2>&1 | grep SKIPPED

# Find failed tests
pytest tools/tests/ -v 2>&1 | grep FAILED
```

## 📋 Checklist Before Committing

- [ ] All tests pass: `pytest tools/tests/ -v`
- [ ] No new skipped tests added for missing functions
- [ ] New functions have tests
- [ ] Renamed functions have updated tests
- [ ] Removed functions have tests deleted
- [ ] Coverage didn't decrease significantly

---

*Remember: A passing test suite with high coverage is infinitely more valuable than a large test suite with many skips and failures.*
