# Test Organization and Guidelines

## Overview

This document describes the test organization, guidelines, and best practices for the Receipt Extractor project.

## Test Statistics

- **Total Tests**: ~1,239 tests
- **Pass Rate**: >94% (1,170+ passing)
- **Code Coverage**: ~55% (target: >70%)
- **Test Lines of Code**: ~20,000 lines

## Test Structure

### Directory Organization (Updated 2025-12-31)

```
tools/tests/
├── conftest.py                 # Shared fixtures and configuration
├── unit/                       # ✨ NEW: Unit tests (fast, isolated)
│   ├── models/
│   │   └── test_schemas.py     # Schema validation tests
│   ├── utils/
│   │   ├── test_helpers.py     # Helper function tests (was test_shared_helpers.py)
│   │   ├── test_validation.py  # Validation tests
│   │   ├── test_nms.py         # NMS algorithm tests
│   │   ├── test_optional_imports.py  # Optional dependency tests
│   │   └── test_coverage_boost.py   # Additional coverage tests
│   └── services/
│       ├── test_telemetry.py   # Telemetry tests
│       └── test_system_health.py  # System health tests
├── api/                        # ✨ NEW: API endpoint tests
│   ├── test_backend_routes.py  # Backend route tests
│   ├── test_billing.py         # Billing and Stripe tests
│   ├── test_analytics.py       # 🔀 MERGED: Analytics tests (was test_analytics.py + test_analytics_routes.py)
│   ├── test_marketing.py       # Marketing API tests
│   ├── test_plan_enhancements.py  # Plan and pricing tests
│   └── test_revenue_features.py   # Revenue feature tests
├── integration/                # Integration tests (enhanced)
│   ├── test_integration.py     # Main integration tests
│   ├── test_auth_workflow.py
│   ├── test_rate_limiting.py
│   ├── test_receipt_workflow.py
│   ├── test_security.py        # Security integration tests (was test_security_integration.py)
│   ├── test_feature_flags.py   # Feature flag tests
│   └── test_spatial_ocr_integration.py
├── backend/                    # Backend-specific tests (keep as-is)
│   └── test_backend.py
├── circular_exchange/          # Circular Exchange Framework tests (keep as-is)
│   ├── test_core.py           # Core variable package tests
│   ├── test_analysis.py       # Analysis and metrics tests
│   ├── test_refactor.py       # Refactoring utilities tests
│   └── test_persist.py        # Persistence tests
├── shared/                     # Shared utilities tests (keep as-is)
│   ├── test_infra.py          # Infrastructure tests
│   ├── test_models.py         # Model tests (largest: 2,415 lines)
│   ├── test_ocr.py            # OCR functionality tests
│   ├── test_spatial_ocr.py    # Spatial OCR tests
│   └── test_utils.py          # Utility tests
└── web/                        # Web-specific tests (keep as-is)
    └── test_api.py
```

### Key Improvements

✅ **Better Organization**: Tests now grouped by type (unit, api, integration)  
✅ **Reduced Duplication**: Merged `test_analytics.py` + `test_analytics_routes.py` → `api/test_analytics.py`  
✅ **Clearer Structure**: Easier to find tests and run specific categories  
✅ **Consistent Naming**: All test files follow `test_*.py` convention  

## Test Categories (Markers)

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, multiple components)
- `@pytest.mark.model` - Model/ML tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.web` - Web application tests
- `@pytest.mark.cosmetic` - Cosmetic/UI enhancement tests

## Test Quality Guidelines

### What Makes a Good Test

✅ **DO:**
- Test actual behavior and functionality
- Use meaningful test names that describe what's being tested
- Test edge cases and error conditions
- Keep tests focused on a single concept
- Use fixtures for shared setup
- Mock external dependencies appropriately

❌ **DON'T:**
- Write tests that only check if imports work
- Test trivial getters/setters without logic
- Test framework functionality (e.g., testing that pytest works)
- Duplicate tests across multiple files
- Write tests that are implementation-dependent

### Examples

**Bad Test (Trivial Import):**
```python
def test_module_imports():
    """Test that module can be imported."""
    from shared.utils import helpers
    assert helpers is not None  # Adds no value
```

**Good Test (Functional):**
```python
def test_normalize_price_handles_european_format():
    """Test price normalization with European comma format."""
    from shared.utils.helpers import normalize_price
    assert normalize_price('12,50') == Decimal('12.50')
    assert normalize_price('1.234,56') == Decimal('1234.56')
```

## Recent Improvements

### 2025-12-31 Test Reorganization (Issue #4)

1. **Reorganized Test Structure**
   - Created `unit/`, `api/` subdirectories for better organization
   - Moved 22 test files from root to appropriate subdirectories
   - Reduced root directory clutter (22 files → infrastructure files only)

2. **Merged Duplicate Tests**
   - Merged `test_analytics.py` + `test_analytics_routes.py` → `api/test_analytics.py`
   - Eliminated redundancy in analytics test coverage

3. **Improved Discoverability**
   - Tests now organized by type: unit, api, integration
   - Easier to run specific test categories
   - Better alignment with project structure

### 2024-12 Test Quality Improvements

1. **Fixed Failing Tests (8 → 0)**
   - Updated spatial OCR model references
   - Fixed confidence score test with realistic data
   - Updated processor type validation
   - Improved skip handling for optional dependencies

2. **Removed Trivial Tests**
   - Removed import-only tests from test_coverage_boost.py (15 → 7 tests)
   - Total tests reduced from 1,246 to 1,239 (more focused)

3. **Better Skip Handling**
   - 76 tests properly skip when dependencies unavailable
   - Tests fail gracefully with informative messages

## Running Tests

### By Directory Category
```bash
# Run all unit tests
pytest tools/tests/unit/ -v

# Run all API tests
pytest tools/tests/api/ -v

# Run all integration tests
pytest tools/tests/integration/ -v

# Run specific module tests
pytest tools/tests/unit/utils/ -v
pytest tools/tests/api/test_billing.py -v
```

### Quick Tests
```bash
pytest -v -m "not slow"
```

### Full Test Suite
```bash
pytest -v
```

### Specific Test Category
```bash
pytest -v -m integration
pytest -v -m unit
```

### With Coverage
```bash
pytest --cov=shared --cov=web/backend --cov-report=html
```

### Test a Specific File
```bash
pytest tools/tests/shared/test_models.py -v
```

## Test Coverage Goals

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| shared.utils | 40% | 70% | High |
| shared.models | 65% | 80% | Medium |
| web.backend | 16% | 60% | High |
| circular_exchange | 95% | 95% | ✓ Done |

## Future Improvements

1. **Increase Backend Coverage** - Currently at 16%, target 60%
2. **Consolidate Large Test Files** - test_models.py (2,415 lines) should be split
3. **Add Missing Critical Path Tests** - Focus on error handling and edge cases
4. **Performance Testing** - Add benchmarks for OCR operations
5. **End-to-End Tests** - Add more full workflow tests

## Contributing

When adding new tests:

1. Follow the structure above
2. Use appropriate markers
3. Add to existing test classes when possible
4. Ensure tests are independent and can run in any order
5. Update this document if adding new test categories
