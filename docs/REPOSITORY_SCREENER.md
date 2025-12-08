# Repository Screener Tool

## Overview

The Repository Screener is a comprehensive analysis tool that screens the entire codebase to identify potential issues, missing implementations, and areas for improvement. It performs static analysis on both Python and JavaScript files to provide actionable insights.

## Features

The tool analyzes the repository for:

1. **Missing Implementations**: Functions or classes that are imported but not defined in the expected module
2. **Orphaned Imports**: Imports that are never used in their files
3. **Missing Test Coverage**: Files with functions/classes that lack corresponding test files
4. **Missing Files**: Files referenced in imports that don't exist in the repository
5. **Unused Functions**: Functions that are defined but never called (heuristic)
6. **Documentation Mismatches**: References in documentation that don't match actual code

## Installation

The tool is located at `tools/scripts/repo_screener.py` and uses only Python standard library modules, so no additional installation is required.

## Usage

### Basic Usage

Run from the repository root:

```bash
python tools/scripts/repo_screener.py
```

This will:
- Scan all Python and JavaScript files
- Generate a comprehensive analysis
- Save results to:
  - `REPOSITORY_ANALYSIS.md` (human-readable markdown report)
  - `repository_analysis.json` (machine-readable JSON data)

### Specify Custom Repository Path

```bash
python tools/scripts/repo_screener.py /path/to/repository
```

## Output Files

### 1. REPOSITORY_ANALYSIS.md

A comprehensive markdown report containing:

- **Summary Statistics**: Total files, functions, classes
- **Issues Found**: Categorized list of all detected issues
- **Missing Implementations**: Detailed list with import statements
- **Orphaned Imports**: Unused imports by file
- **Files Without Tests**: Python files lacking test coverage
- **Missing Files**: Referenced but non-existent files
- **Unused Functions**: Potentially unused code (heuristic)
- **Documentation Mismatches**: README vs. code inconsistencies
- **File Analysis Details**: 
  - Files by category (backend, frontend, shared, tests)
  - Top 20 files by line count
  - Files with analysis errors

### 2. repository_analysis.json

Machine-readable JSON format containing:

```json
{
  "summary": {
    "total_files": 197,
    "total_python_files": 154,
    "total_javascript_files": 43,
    "total_functions": 2959,
    "total_classes": 612
  },
  "issues": {
    "missing_implementations": [...],
    "orphaned_imports": [...],
    "missing_tests": [...],
    "missing_files": [...],
    "unused_functions": [...],
    "documentation_mismatches": [...]
  },
  "file_analyses": [...]
}
```

This format is ideal for:
- Automated processing
- Integration with CI/CD pipelines
- Custom analysis scripts
- Tracking changes over time

## Understanding the Analysis

### Missing Implementations

These are functions/classes imported from a module but not found in that module:

```python
# Example from report:
File: web/backend/auth.py
Import: from password import hash_password
Missing: hash_password from module password
```

**Common Causes:**
- Relative import path issues
- Third-party libraries (false positive)
- Functions in `__init__.py` not detected
- Dynamic imports

**Action Items:**
- Verify the import path is correct
- Check if the function exists but wasn't detected
- If it's a third-party library, it's a false positive (can be ignored)

### Orphaned Imports

Imports that appear once in the file (only in the import statement):

```python
# Example:
from typing import Optional  # Imported but never used
```

**Common Causes:**
- Leftover from refactoring
- Prepared for future use
- Used in type hints (may not be detected)

**Action Items:**
- Remove if truly unused
- Keep if used in comments or type hints

### Missing Test Coverage

Files with functions/classes but no corresponding test file:

```
File: web/backend/app.py
Functions: 30, Classes: 0
```

**Action Items:**
- Create test file if this is production code
- Skip if it's a script or example file

### Missing Files

Modules imported but files don't exist:

```
Module: shared.models.custom_model
Referenced in: web/backend/app.py
Expected at: shared/models/custom_model.py or shared/models/custom_model/__init__.py
```

**Common Causes:**
- Wrong import path
- File not committed to repository
- Third-party module (false positive)

**Action Items:**
- Fix import path
- Add missing file
- Ignore if third-party

### Unused Functions

Functions defined but apparently never called (heuristic):

```
File: shared/utils/helpers.py
Function: old_helper_function
```

**⚠️ Note**: This is heuristic-based and may have false positives:
- Functions called dynamically
- Functions used in other repositories
- Functions exported for API use

**Action Items:**
- Review each case individually
- Remove if truly unused
- Document if it's part of public API

### Documentation Mismatches

References in README that don't match code:

```
Type: README reference
Name: ocr_tesseract
Issue: Referenced in README but not found in code
```

**Common Causes:**
- Documentation out of date
- String constants (not functions/classes)
- Configuration values

**Action Items:**
- Update documentation
- Ignore if it's a configuration value or string constant

## Exclusion Patterns

The tool automatically excludes:

- `node_modules/`
- `__pycache__/`
- `venv/`, `env/`
- `.git/`
- `migrations/`
- `logs/`
- `.pytest_cache/`
- `htmlcov/`
- `dist/`, `build/`
- `*.min.js`

## Interpreting Results

### High Priority Issues

1. **Missing Implementations in Core Modules**: If backend or shared modules have missing implementations, these should be investigated immediately.

2. **Syntax Errors**: Any files with analysis errors (shown at the end) should be fixed.

3. **Missing Tests for Critical Code**: Backend API routes and shared utilities should have tests.

### Medium Priority Issues

1. **Orphaned Imports**: Clean these up to improve code quality.

2. **Documentation Mismatches**: Keep README in sync with code.

3. **Missing Files**: Verify import paths are correct.

### Low Priority Issues

1. **Unused Functions**: Review but be cautious about removing (may be false positives).

2. **Missing Tests for Scripts**: Scripts and examples don't always need tests.

## Integration with CI/CD

You can integrate this tool into your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run Repository Screener
  run: |
    python tools/scripts/repo_screener.py
    
- name: Upload Analysis Report
  uses: actions/upload-artifact@v3
  with:
    name: repository-analysis
    path: |
      REPOSITORY_ANALYSIS.md
      repository_analysis.json
```

## Limitations

1. **Heuristic Analysis**: Some detections (unused functions, orphaned imports) are heuristic-based and may have false positives.

2. **Standard Library Filtering**: The tool filters common standard library modules, but some third-party imports may be flagged as missing.

3. **Dynamic Code**: Dynamically generated code, `eval()`, `exec()`, or `getattr()` usage may not be detected.

4. **JavaScript Analysis**: JavaScript analysis is regex-based (not AST-based like Python), so it's less robust.

5. **Type Hints**: Some type hint imports may be flagged as unused even though they're used.

## Customization

To customize the tool, edit `tools/scripts/repo_screener.py`:

### Add Exclusion Patterns

```python
self.exclude_patterns = [
    '*/node_modules/*',
    '*/my_custom_dir/*',  # Add your pattern here
    # ...
]
```

### Filter Standard Libraries

Add to the standard library check in `find_missing_implementations()`:

```python
if not module.startswith(('os', 'sys', 'my_lib', ...)):
```

### Adjust Analysis Logic

Modify the analysis methods:
- `find_missing_implementations()`
- `find_orphaned_imports()`
- `find_unused_functions()`
- etc.

## Example Workflow

1. **Initial Scan**:
   ```bash
   python tools/scripts/repo_screener.py
   ```

2. **Review Report**:
   ```bash
   cat REPOSITORY_ANALYSIS.md | less
   ```

3. **Fix High-Priority Issues**:
   - Syntax errors
   - Missing implementations in core modules
   - Critical missing tests

4. **Clean Up Code**:
   - Remove orphaned imports
   - Update documentation

5. **Re-scan to Verify**:
   ```bash
   python tools/scripts/repo_screener.py
   ```

6. **Track Progress**:
   ```bash
   # Compare reports
   diff old_REPOSITORY_ANALYSIS.md REPOSITORY_ANALYSIS.md
   ```

## Troubleshooting

### Tool Runs Slowly

The tool analyzes all files, which can take 30-60 seconds on large repositories. This is normal.

### Too Many False Positives

This is expected for:
- **Missing Implementations**: Many third-party libraries will be flagged
- **Unused Functions**: Dynamic usage won't be detected

Filter the report manually or adjust the filtering logic.

### Syntax Errors Reported

If a file has syntax errors, it will be noted in the "Files with Analysis Errors" section. Fix these first before addressing other issues.

## Best Practices

1. **Run Regularly**: Run the screener after major refactoring or before releases.

2. **Version Control Reports**: Commit `REPOSITORY_ANALYSIS.md` to track progress over time.

3. **Focus on Trends**: Don't try to fix everything at once. Focus on reducing issues over time.

4. **Ignore False Positives**: Document known false positives in comments or separate file.

5. **Combine with Other Tools**: Use alongside linters (pylint, flake8), type checkers (mypy), and test coverage tools.

## Related Tools

This tool complements:
- **pytest**: For running tests
- **coverage**: For measuring test coverage
- **pylint/flake8**: For code quality
- **mypy**: For type checking
- **CEFR Framework**: For auto-tuning and optimization

## Support

For issues or questions:
1. Check the generated report for specific error messages
2. Review the tool's source code: `tools/scripts/repo_screener.py`
3. Open an issue on GitHub

---

*Last Updated: 2025-12-08*
*Tool Version: 1.0.0*
