# CEFR Developer Tools

Static analysis tools for import management and code quality.

## Overview

These tools transform the Circular Exchange Framework from a runtime system into practical static analysis tools for developers.

## Tools

### dependency_analyzer.py
Analyzes actual Python imports and detects issues.

**Usage:**
```bash
python tools/cefr/dependency_analyzer.py
```

**Features:**
- ✅ Circular dependency detection
- ✅ Import depth analysis
- ✅ Bottleneck identification (heavily imported modules)
- ✅ Isolated module detection
- ✅ Report saved to `docs/DEPENDENCY_ANALYSIS.md`

**Exit Codes:**
- `0` - No circular dependencies found
- `1` - Circular dependencies detected (requires refactoring)

**Example Output:**
```
================================================================================
DEPENDENCY ANALYSIS REPORT
================================================================================

Total Python modules: 148
Total import relationships: 523

✅ No circular dependencies detected

Import Depth Analysis:
  Max depth: 5
  Avg depth: 2.3
  Deepest modules:
    web.backend.app: depth 5
    shared.models.engine: depth 4

Import Bottlenecks (imported by 10+ modules):
  shared.utils.data: 23 imports
  shared.utils.helpers: 18 imports
```

---

### import_validator.py
Validates critical imports before deployment.

**Usage:**
```bash
python tools/cefr/import_validator.py
```

**Features:**
- ✅ Validates critical imports (shared, models, backend)
- ✅ Checks optional imports (OCR engines, ML frameworks)
- ✅ Clear pass/fail reporting

**Exit Codes:**
- `0` - All critical imports validated
- `1` - One or more critical imports failed

**Example Output:**
```
================================================================================
IMPORT VALIDATION
================================================================================

Validating critical imports...
============================================================
✅ shared.utils.data
✅ shared.models.manager
✅ web.backend.app
✅ web.backend.database

Validating optional imports...
============================================================
✅ EasyOCR (easyocr)
⚠️  PyTorch (torch): Not installed

============================================================
SUMMARY
============================================================
✅ All critical imports validated
⚠️  1 optional import(s) not available:
   - PyTorch

✅ Import validation complete
```

---

## Integration with CI/CD

### GitHub Actions

Add to `.github/workflows/ci.yml`:

```yaml
- name: Validate Imports
  run: python tools/cefr/import_validator.py

- name: Check Dependencies
  run: python tools/cefr/dependency_analyzer.py
```

### Pre-Commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python tools/cefr/dependency_analyzer.py
if [ $? -ne 0 ]; then
    echo "❌ Circular dependencies detected"
    exit 1
fi
```

---

## Development Workflow

### Before Making Changes
```bash
# Understand current dependency structure
python tools/cefr/dependency_analyzer.py
```

### After Making Changes
```bash
# Validate imports still work
python tools/cefr/import_validator.py

# Check for new circular dependencies
python tools/cefr/dependency_analyzer.py
```

### Before Committing
```bash
# Final validation
python tools/cefr/import_validator.py && \
python tools/cefr/dependency_analyzer.py
```

---

## Troubleshooting

### "Circular dependencies detected"
**Problem:** Module A imports Module B, and Module B imports Module A (directly or indirectly).

**Solution:**
1. Review the dependency chain in the report
2. Extract common code into a new module
3. Use dependency injection or lazy imports
4. Re-run analyzer to verify fix

**Example Fix:**
```python
# Before (circular)
# module_a.py
from module_b import function_b

# module_b.py
from module_a import function_a

# After (fixed)
# module_common.py
def shared_function():
    pass

# module_a.py
from module_common import shared_function

# module_b.py
from module_common import shared_function
```

### "Import failed" errors
**Problem:** A critical module cannot be imported.

**Common Causes:**
1. Missing dependency in requirements.txt
2. Syntax error in the module
3. Circular import at runtime

**Solution:**
```bash
# Check for syntax errors
python -m py_compile path/to/module.py

# Try importing directly
python -c "import module.name"

# Check dependencies
pip install -r requirements.txt
```

---

## Architecture Notes

### Why These Tools?

The original CEFR runtime registration system added significant boilerplate (~700+ lines) without runtime benefits. These tools salvage the valuable concept (dependency tracking) into practical static analysis.

**Before (Runtime Overhead):**
- 54 files with CEFR boilerplate
- 184 try/except blocks
- 68 registration calls
- Zero runtime usage

**After (Static Analysis):**
- Clean codebase (no boilerplate)
- Practical developer tools
- Actionable insights
- CI/CD integration ready

### Design Principles

1. **Static Analysis Only** - No runtime overhead
2. **Fast Execution** - Complete scans in seconds
3. **Actionable Reports** - Clear problems and solutions
4. **CI/CD Ready** - Proper exit codes and formatting
5. **Zero Dependencies** - Uses only Python stdlib

---

## Future Enhancements

Potential additions to the toolset:

- **Import Graph Visualizer** - Generate dependency graphs with graphviz
- **Dead Code Detector** - Find unused functions/classes
- **API Usage Analyzer** - Track internal API usage patterns
- **Migration Helper** - Assist with refactoring tasks

---

## Contributing

When adding new analysis tools:

1. Follow the existing pattern (simple CLI, clear output)
2. Use only Python standard library
3. Provide actionable insights
4. Include proper exit codes
5. Document in this README

---

## License

Same as parent project (Receipt Extractor).
