# Code Quality Standards

**Last Updated**: 2025-12-08  
**Status**: 🟢 Active Enforcement  
**CI Pipeline**: `.github/workflows/quality-gates.yml`

---

## Overview

This document defines code quality standards for the Receipt Extractor project. All code must meet these standards before merging to main.

---

## Quality Gates (CI/CD)

### Blocking Checks (Must Pass)

1. ✅ **Python Syntax Validation**
   - All `.py` files must compile
   - Run: `python -m py_compile file.py`
   - Enforced: CI pipeline

2. ✅ **Import Validation**
   - Critical module imports must work
   - Run: `python tools/scripts/validate_imports.py`
   - Enforced: CI pipeline

### Warning Checks (Non-Blocking)

3. ⚠️ **Code Linting** (Flake8)
   - Style guidelines (currently warnings)
   - Will become blocking after cleanup phase
   - Run: `flake8 . --max-line-length=100`

4. ⚠️ **Test Suite**
   - Currently improving (some tests failing)
   - Coverage tracked but not blocking
   - Run: `pytest --cov=shared --cov=web/backend`

5. ⚠️ **Security Scanning**
   - Bandit for vulnerability detection
   - pip-audit for dependency issues
   - Run: `bandit -r shared/ web/`

6. ⚠️ **File Size Checks**
   - Prevent binary files >10MB in root
   - Currently warning (cleanup in progress)

---

## Python Style Guide

### Line Length

**Maximum**: 100 characters (configurable in `.pre-commit-config.yaml`)

**Why**: Balance readability vs screen real estate

```python
# Good
result = some_function(
    param1=value1,
    param2=value2
)

# Bad (>100 chars)
result = some_function(param1=value1, param2=value2, param3=value3, param4=value4, param5=value5)
```

### Imports

**Order** (enforced by `isort`):
1. Standard library
2. Third-party packages
3. Local modules

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import numpy as np
from flask import Flask, request

# Local
from shared.models.schemas import DetectionResult
from shared.utils.helpers import sanitize_filename
```

**Style**:
```python
# Good: Absolute imports from project root
from shared.models.engine import EasyOCRProcessor

# Avoid: Relative imports
from ..models.engine import EasyOCRProcessor  # Harder to refactor
```

### Formatting

**Tool**: Black (automated via pre-commit hooks)

**Key Rules**:
- 4-space indentation
- Double quotes for strings
- Trailing commas in multi-line structures
- Consistent spacing around operators

```python
# Good (Black-formatted)
def process_receipt(
    image_path: str,
    model_id: str = "ocr_tesseract",
) -> DetectionResult:
    """Process receipt with specified model."""
    result = {
        "success": True,
        "data": extracted_data,
    }
    return result

# Bad (inconsistent formatting)
def process_receipt(image_path:str,model_id:str="ocr_tesseract")->DetectionResult:
    result={"success":True,"data":extracted_data}
    return result
```

---

## Type Hints

### Required For

- **Public API functions**
- **Class methods** (especially constructors)
- **Complex return types**

### Not Required For

- **Private/internal functions** (use judgment)
- **Simple utilities** (obvious from name)
- **Test functions**

### Examples

```python
# Good: Clear type hints
from typing import Dict, List, Optional

def extract_total(
    text: str,
    patterns: List[str]
) -> Optional[float]:
    """Extract total amount from text."""
    # ...
    return total

# Acceptable: Simple case without hints
def is_valid(value):
    """Check if value is valid."""
    return value is not None and value > 0

# Good: Complex types
from dataclasses import dataclass
from typing import Union

@dataclass
class ProcessingResult:
    success: bool
    data: Dict[str, Union[str, float, List[str]]]
    error: Optional[str] = None
```

---

## Documentation

### Docstrings (Required)

**Module-level**:
```python
"""
Module Name - Brief Description

Longer description of module purpose.
Common use cases and examples.
"""
```

**Function-level** (for public functions):
```python
def process_image(image_path: str, model_id: str) -> DetectionResult:
    """
    Process receipt image with specified model.
    
    Args:
        image_path: Path to receipt image file
        model_id: Model identifier (e.g., 'ocr_tesseract')
        
    Returns:
        DetectionResult with extracted text and metadata
        
    Raises:
        ValueError: If image_path doesn't exist
        ProcessingError: If model processing fails
        
    Example:
        >>> result = process_image("receipt.jpg", "ocr_tesseract")
        >>> print(result.texts)
        [DetectedText(text="Total: $42.99", confidence=0.95)]
    """
```

**Class-level**:
```python
class ReceiptProcessor:
    """
    Main processor for receipt extraction.
    
    This class manages model selection, preprocessing, and
    extraction workflows for receipt images.
    
    Attributes:
        model_id: Active model identifier
        config: Processing configuration
        
    Example:
        >>> processor = ReceiptProcessor(model_id="ocr_easyocr")
        >>> result = processor.process("receipt.jpg")
    """
```

---

## Error Handling

### Principles

1. **Be Specific**: Catch specific exceptions, not bare `except:`
2. **Log Errors**: Always log before re-raising or returning error state
3. **Return Structured Errors**: Use schemas (DetectionResult, etc.)
4. **Clean Up Resources**: Use context managers or try/finally

### Examples

```python
# Good: Specific exception handling
try:
    result = process_receipt(image_path)
except FileNotFoundError:
    logger.error(f"Image not found: {image_path}")
    return DetectionResult(
        success=False,
        error_code=ErrorCode.FILE_NOT_FOUND,
        error_message=f"Image not found: {image_path}"
    )
except ProcessingError as e:
    logger.error(f"Processing failed: {e}")
    return DetectionResult(
        success=False,
        error_code=ErrorCode.PROCESSING_FAILED,
        error_message=str(e)
    )

# Bad: Catch-all exception
try:
    result = process_receipt(image_path)
except:  # ❌ Too broad, hides bugs
    return None
```

### Resource Management

```python
# Good: Context manager
with open(file_path, 'r') as f:
    data = f.read()

# Good: Try/finally for cleanup
resource = None
try:
    resource = acquire_resource()
    use_resource(resource)
finally:
    if resource:
        resource.cleanup()
```

---

## Logging

### Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning about potential issues
- **ERROR**: Error occurred but app continues
- **CRITICAL**: Critical error, app may crash

### Format

```python
import logging

logger = logging.getLogger(__name__)

# Good: Structured logging
logger.info(
    f"Processing receipt: user_id={user_id}, model={model_id}, size={file_size}"
)

logger.error(
    f"Extraction failed: {error_msg}",
    exc_info=True  # Include stack trace
)

# Bad: Unclear logging
logger.info("Processing")  # ❌ Not helpful
logger.error(e)  # ❌ Just exception object
```

### What to Log

✅ **Do log**:
- Function entry/exit (DEBUG level)
- Configuration loaded (INFO)
- Processing milestones (INFO)
- Errors with context (ERROR)
- Performance metrics (INFO/DEBUG)

❌ **Don't log**:
- Sensitive data (passwords, tokens)
- Full file contents
- Every loop iteration
- Redundant information

---

## CEFR Integration (Optional)

### Current Status

CEFR integration is **OPTIONAL** (see `docs/architecture/CEFR_STATUS.md`)

### When to Add CEFR

**Add CEFR integration if**:
- Module has tunable parameters
- Auto-optimization would add value
- Team is familiar with CEFR patterns

**Skip CEFR integration if**:
- Module has fixed constants
- Configuration rarely changes
- Minimizing complexity is priority

### Integration Pattern (If Using CEFR)

```python
"""
Module with optional CEFR integration
"""
import logging

# Optional CEFR import
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Register module (optional)
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="module.name",
            file_path=__file__,
            exports=["ClassName"]
        ))
    except Exception as e:
        logger.debug(f"CEFR registration skipped: {e}")

# Module code continues normally
```

---

## Security Standards

### Input Validation

**Always validate**:
- File uploads (type, size, content)
- User input (SQL injection, XSS)
- API parameters (type, range)

```python
# Good: Validate file upload
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_upload(file):
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid file type: {ext}")
    
    # Check size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {size} bytes")
    
    return True
```

### Secrets Management

**Never commit**:
- API keys
- Passwords
- JWT secrets
- Database credentials

**Use**:
- Environment variables (`.env` file)
- Secret management services (AWS Secrets Manager, etc.)
- Minimum 32 characters for secrets

```python
# Good: Environment variables
import os

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY must be set and at least 32 characters")

# Bad: Hardcoded secret
SECRET_KEY = "my-secret-123"  # ❌ Never do this
```

### SQL Injection Prevention

**Always use**:
- SQLAlchemy ORM (parameterized queries)
- Never build raw SQL with string concatenation

```python
# Good: ORM query
user = User.query.filter_by(email=user_email).first()

# Good: Parameterized query
result = db.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": user_email}
)

# Bad: String concatenation
query = f"SELECT * FROM users WHERE email = '{user_email}'"  # ❌ SQL injection!
```

---

## Pre-commit Hooks

### Installation

```bash
pip install pre-commit
pre-commit install
```

### What Runs

On every commit:
1. Python syntax check
2. Trailing whitespace removal
3. End-of-file fixer
4. Import sorting (isort)
5. Code formatting (Black)
6. Linting (Flake8)
7. Large file check
8. Merge conflict marker check

### Manual Run

```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

### Skip (When Necessary)

```bash
# Skip all hooks for emergency fix
git commit --no-verify -m "Emergency fix"

# Better: Fix issues then commit normally
pre-commit run --all-files
git add .
git commit -m "Fixed formatting"
```

---

## Code Review Checklist

Before approving PR, verify:

### Functionality
- [ ] Code does what it claims
- [ ] Edge cases handled
- [ ] Error handling appropriate
- [ ] No obvious bugs

### Quality
- [ ] Follows style guide
- [ ] Type hints for public API
- [ ] Docstrings for public functions
- [ ] Logging appropriate
- [ ] Tests included (70%+ coverage)

### Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection prevented
- [ ] XSS protection (if web)

### CI/CD
- [ ] All syntax checks pass
- [ ] Import validation passes
- [ ] Linting warnings addressed
- [ ] Tests pass
- [ ] Coverage not decreased

### Documentation
- [ ] README updated (if needed)
- [ ] API docs updated (if API changed)
- [ ] Comments explain complex logic
- [ ] Breaking changes documented

---

## Tools Reference

### Local Commands

```bash
# Validate before committing
python tools/scripts/validate_imports.py
python tools/scripts/validate_env.py

# Format code
black . --line-length 100

# Sort imports
isort . --profile black --line-length 100

# Lint
flake8 . --max-line-length=100 --extend-ignore=E203,E501,W503

# Security scan
bandit -r shared/ web/ -ll

# Dependency audit
pip-audit
```

### CI/CD

Pipeline runs automatically on PR. See `.github/workflows/quality-gates.yml`

**Force re-run**: Push empty commit
```bash
git commit --allow-empty -m "Trigger CI"
git push
```

---

## Gradual Improvement Plan

### Current State (Phase 1 Complete)
- ✅ Syntax validation (blocking)
- ✅ Import validation (blocking)
- ⚠️ Linting (warnings)
- ⚠️ Tests (improving)
- ⚠️ Security (warnings)

### Phase 2 (In Progress)
- [ ] Fix existing linting warnings
- [ ] Make linting blocking
- [ ] Fix failing tests
- [ ] Make test coverage blocking (70%)

### Phase 3 (Future)
- [ ] Make security scans blocking
- [ ] Enforce 80% coverage for critical modules
- [ ] Add performance benchmarks
- [ ] Add type checking (mypy)

---

## Questions?

- **Style questions**: Check existing code for examples
- **Tool issues**: See tool documentation or ask team
- **CI failures**: Check `.github/workflows/quality-gates.yml` logs

**Remember**: Quality standards help us ship better code faster. When in doubt, ask for review!
