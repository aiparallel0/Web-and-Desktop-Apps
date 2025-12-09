# Repository Screener - Quick Reference

## Quick Start

```bash
# Run the screener from repository root
python tools/scripts/repo_screener.py

# View the markdown report
cat REPOSITORY_ANALYSIS.md | less

# Or open in your browser/editor
code REPOSITORY_ANALYSIS.md
```

## What Gets Generated

1. **REPOSITORY_ANALYSIS.md** (31 KB)
   - Human-readable analysis report
   - Summary statistics
   - Detailed issue listings
   - File-by-file breakdown

2. **repository_analysis.json** (950 KB)
   - Machine-readable JSON
   - Complete file analysis data
   - Programmatic access to all findings

## Key Findings (Current Repository)

| Metric | Count |
|--------|-------|
| Total Files | 197 |
| Python Files | 154 |
| JavaScript Files | 43 |
| Total Functions | 2,959 |
| Total Classes | 612 |

## Issues Detected

| Issue Type | Count | Priority |
|------------|-------|----------|
| Missing Implementations | 512 | Medium* |
| Orphaned Imports | 218 | Low |
| Files Without Tests | 79 | Medium |
| Missing Files | 85 | Medium* |
| Unused Functions | 2,698 | Low* |
| Documentation Mismatches | 14 | Low |

*Note: Many are false positives from third-party libraries. Review individually.

## Most Useful Sections

### 1. Files Without Tests (High Value)
Shows production code lacking test coverage:
```bash
grep -A 50 "## 🧪 Files Without Tests" REPOSITORY_ANALYSIS.md
```

### 2. Missing Files (Action Required)
Files imported but don't exist (fix import paths):
```bash
grep -A 50 "## 📁 Missing Files" REPOSITORY_ANALYSIS.md
```

### 3. Top Files by Line Count
Identify complex files needing refactoring:
```bash
grep -A 25 "### Top 20 Files by Line Count" REPOSITORY_ANALYSIS.md
```

### 4. Files with Errors
Critical - syntax errors to fix immediately:
```bash
grep -A 20 "## ❗ Files with Analysis Errors" REPOSITORY_ANALYSIS.md
```

## Common Tasks

### Find Files Without Tests in Backend
```bash
grep "web/backend" REPOSITORY_ANALYSIS.md | grep "Functions:" | head -20
```

### Check Orphaned Imports in Specific File
```bash
grep -A 2 "your_file.py" REPOSITORY_ANALYSIS.md | grep "Unused"
```

### Export Issue Count to CSV
```bash
python -c "
import json
with open('repository_analysis.json') as f:
    data = json.load(f)
    issues = data['issues']
    for category, items in issues.items():
        print(f'{category},{len(items)}')
" > issue_counts.csv
```

## Interpreting Results

### ✅ True Positives (Take Action)
- Files in `web/backend/` or `shared/` without tests
- Import errors in your own modules
- Syntax errors in any file
- Orphaned imports in files you maintain

### ⚠️ False Positives (Can Ignore)
- Third-party library "missing implementations" (e.g., Flask, SQLAlchemy)
- Standard library modules flagged as missing
- Type hint imports flagged as orphaned
- Functions used dynamically flagged as unused

## Integration Examples

### CI/CD Pipeline
```yaml
# .github/workflows/analysis.yml
- name: Run Repository Analysis
  run: python tools/scripts/repo_screener.py
  
- name: Upload Report
  uses: actions/upload-artifact@v3
  with:
    name: analysis-report
    path: REPOSITORY_ANALYSIS.md
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
python tools/scripts/repo_screener.py
git add REPOSITORY_ANALYSIS.md
```

### Weekly Cron Job
```bash
# Run every Monday at 9 AM
0 9 * * 1 cd /path/to/repo && python tools/scripts/repo_screener.py && git commit -am "Update analysis report" && git push
```

## Troubleshooting

**Problem**: Too many false positives
**Solution**: Focus on specific sections (Files Without Tests, Missing Files in your modules)

**Problem**: Report is too large
**Solution**: The markdown report limits each section to 50 items. Use JSON for full data.

**Problem**: Want to exclude certain directories
**Solution**: Edit `tools/scripts/repo_screener.py` and add to `exclude_patterns`

## Next Steps

1. ✅ Review "Files with Analysis Errors" (if any)
2. ✅ Check "Files Without Tests" for critical modules
3. ✅ Fix "Missing Files" in your own modules
4. ✅ Clean up "Orphaned Imports" in maintained files
5. ⏳ Review "Unused Functions" (low priority, many false positives)

## Full Documentation

For complete details, see:
- **[Repository Screener Documentation](docs/REPOSITORY_SCREENER.md)**
- **[Full Analysis Report](REPOSITORY_ANALYSIS.md)**

---

*Quick Reference v1.0 | Last Updated: 2025-12-08*
