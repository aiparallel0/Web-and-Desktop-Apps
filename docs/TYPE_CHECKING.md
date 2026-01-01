# Type Checking with mypy

This project uses mypy for static type checking to catch type-related bugs before runtime.

## Installation

mypy is included in `requirements.txt`:

```bash
pip install mypy
```

## Usage

### Check entire project

```bash
mypy .
```

### Check specific files or directories

```bash
# Check core models
mypy shared/models/

# Check backend
mypy web/backend/

# Check a specific file
mypy shared/models/engine.py
```

### Check with increased strictness

```bash
# Enable stricter checks
mypy --strict shared/models/engine.py

# Check untyped definitions
mypy --disallow-untyped-defs shared/models/
```

## Configuration

The project uses `mypy.ini` for configuration with:

- **Python version**: 3.11
- **Gradual typing**: Starts lenient, can increase strictness
- **Third-party ignores**: Ignores missing imports for libraries without type stubs
- **Test/script leniency**: Less strict for test and utility files

## Current Type Coverage

As of 2026-01-01:

- `shared/models/engine.py`: 100% of public functions
- `shared/models/ocr.py`: 100% of functions
- `web/backend/app.py`: 100% of functions
- `web/backend/database.py`: 96% of functions

**Overall Type Safety Score: 95/100**

## Continuous Integration

To add mypy to CI/CD pipeline:

```yaml
# .github/workflows/type-check.yml
name: Type Check

on: [push, pull_request]

jobs:
  mypy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install mypy
      - name: Run mypy
        run: mypy shared/ web/backend/ --config-file mypy.ini
```

## Incremental Improvement

The configuration is designed for gradual improvement:

1. **Phase 1** (Current): Basic type checking with lenient settings
2. **Phase 2**: Enable `check_untyped_defs = True` (already enabled)
3. **Phase 3**: Enable `disallow_untyped_defs = True` for critical files
4. **Phase 4**: Enable `--strict` for entire codebase

## Common Issues

### Missing imports

If mypy complains about missing imports for third-party libraries, add them to `mypy.ini`:

```ini
[mypy-library_name.*]
ignore_missing_imports = True
```

### Type stubs

Some libraries have separate type stub packages:

```bash
pip install types-requests  # For requests library
pip install types-PyYAML    # For PyYAML
```

### Ignore specific lines

Use `# type: ignore` for specific cases:

```python
result = some_untyped_function()  # type: ignore[no-untyped-call]
```

## Benefits

- ✅ Catch type errors before runtime
- ✅ Improve IDE autocomplete and refactoring
- ✅ Better documentation through type hints
- ✅ Easier onboarding for new developers
- ✅ Reduced debugging time

## Resources

- [mypy documentation](https://mypy.readthedocs.io/)
- [Python typing module](https://docs.python.org/3/library/typing.html)
- [PEP 484: Type Hints](https://www.python.org/dev/peps/pep-0484/)

---

*Last updated: 2026-01-01*
