# Receipt Extractor Test Suite

Comprehensive test suite for the Receipt Extractor application using pytest.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures and configuration
├── shared/               # Tests for shared modules
│   ├── test_model_manager.py
│   ├── test_image_processing.py
│   └── test_ocr_processor.py
├── web/                  # Tests for web application
│   └── test_api.py
├── desktop/              # Tests for desktop application
│   └── (future tests)
└── README.md            # This file
```

## Installation

Install testing dependencies:

```bash
pip install -r requirements.txt
```

Or install just testing packages:

```bash
pip install pytest pytest-cov pytest-mock requests-mock pytest-flask
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# Web app tests
pytest -m web

# Model tests (requires models)
pytest -m model
```

### Run Tests by Directory

```bash
# Shared module tests
pytest tests/shared/

# Web app tests
pytest tests/web/

# Desktop app tests
pytest tests/desktop/
```

### Run Specific Test File

```bash
pytest tests/shared/test_model_manager.py
```

### Run with Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=shared --cov=web-app/backend --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Run Tests in Verbose Mode

```bash
pytest -v
```

### Run Tests and Show Print Statements

```bash
pytest -s
```

## Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests (slower, require dependencies)
- `@pytest.mark.model` - Tests requiring AI models
- `@pytest.mark.slow` - Slow tests (may take minutes)
- `@pytest.mark.web` - Web application tests
- `@pytest.mark.desktop` - Desktop application tests

### Running Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run everything except slow tests
pytest -m "not slow"

# Run web and unit tests
pytest -m "web or unit"
```

## Writing Tests

### Test File Naming

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test

```python
import pytest

@pytest.mark.unit
def test_example():
    """Test description."""
    result = my_function(input_data)
    assert result == expected_output

@pytest.mark.integration
def test_receipt_extraction(sample_receipt_data):
    """Test with fixture."""
    receipt = extract_receipt(sample_receipt_data)
    assert receipt['store']['name'] == "Sample Store"
```

### Using Fixtures

Shared fixtures are defined in `conftest.py`:

```python
def test_with_sample_data(sample_receipt_data):
    """Use predefined sample receipt data."""
    assert sample_receipt_data['store']['name'] == "Sample Store"

def test_with_test_dir(test_data_dir):
    """Use test data directory path."""
    receipts = list(test_data_dir.glob('*.jpg'))
    assert len(receipts) > 0
```

## Coverage Goals

Target coverage levels:

- **Critical modules:** 90%+ coverage
- **Shared modules:** 80%+ coverage
- **API endpoints:** 85%+ coverage
- **Overall project:** 75%+ coverage

Check current coverage:

```bash
pytest --cov=shared --cov=web-app/backend --cov-report=term-missing
```

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          pytest -v --cov=shared --cov=web-app/backend
```

## Common Issues

### Import Errors

If you get import errors, ensure the project root is in your Python path:

```python
# In conftest.py or test file
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Model Tests Failing

Model tests require AI models to be downloaded. Skip them with:

```bash
pytest -m "not model"
```

### Slow Tests

Skip slow tests during development:

```bash
pytest -m "not slow"
```

## Test Data

Sample receipt images and expected outputs are in `test_data/`:

- `test_data/receipts/` - Sample receipt images
- `test_data/expected_outputs/` - Expected extraction results

See [test_data/README.md](../test_data/README.md) for details.

## Current Test Status

- ✅ Test infrastructure set up
- ✅ Basic configuration tests
- ⬜ Model manager tests (placeholder)
- ⬜ Image processing tests (placeholder)
- ⬜ OCR processor tests (placeholder)
- ⬜ API endpoint tests (placeholder)
- ⬜ Desktop app tests (placeholder)

## Next Steps

1. ✅ Set up pytest infrastructure
2. ⬜ Implement model manager tests
3. ⬜ Implement image processing tests
4. ⬜ Implement OCR processor tests
5. ⬜ Implement API tests
6. ⬜ Add integration tests with sample data
7. ⬜ Set up CI/CD pipeline
8. ⬜ Achieve 75%+ code coverage

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Coverage Plugin](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
