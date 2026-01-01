# Code Quality Improvement Checklist

**Date:** 2026-01-01  
**Purpose:** Actionable, prioritized list of improvements with clear acceptance criteria

---

## 📋 How to Use This Checklist

1. Start with **Immediate** items before production deployment
2. Complete **Short Term** items within 30 days of launch
3. Address **Medium Term** items in months 2-3
4. Consider **Long Term** items as capacity allows

Each item includes:
- Clear description
- Time estimate
- Priority level
- Acceptance criteria
- Why it matters

---

## 🚨 Immediate (Pre-Launch) - OPTIONAL

### 1. Fix Documentation Example with Placeholder API Key
- **File:** `shared/services/cloud_finetuning.py:425`
- **Time:** 5 minutes
- **Priority:** 🟢 Low (cosmetic)
- **Status:** ✅ COMPLETED

**What to do:**
```python
# Change this:
# trainer = RunPodTrainer(api_key="xxxxx")

# To this:
# trainer = RunPodTrainer(api_key=os.getenv('RUNPOD_API_KEY'))
```

**Acceptance Criteria:**
- [ ] No placeholder API keys in documentation examples
- [ ] Example shows environment variable usage
- [ ] Imports added if needed

**Why it matters:**
- Prevents confusion for developers
- Models best practices
- Minimal effort, good hygiene

---

## 🎯 Short Term (First 30 Days) - RECOMMENDED

### 2. Add Type Hints to `web/backend/app.py`
- **Current Coverage:** 39% (13/33 functions)
- **Target Coverage:** 90%+ (30/33 functions)
- **Time:** 2 hours
- **Priority:** 🟡 Medium
- **Status:** ⬜ NOT STARTED

**What to do:**
```python
# Before:
def create_receipt(data):
    return process(data)

# After:
def create_receipt(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    return process(data)
```

**Acceptance Criteria:**
- [ ] All public functions have return type hints
- [ ] All function parameters have type hints
- [ ] Complex types use proper typing imports (Dict, List, Optional, Tuple)
- [ ] Code passes `python -m py_compile web/backend/app.py`
- [ ] Type coverage ≥ 90%

**How to verify:**
```bash
python -c "
import re
content = open('web/backend/app.py').read()
funcs = re.findall(r'def\s+\w+\s*\([^)]*\)', content)
typed = [f for f in funcs if '->' in f or ':' in f.split('(')[1]]
print(f'{len(typed)}/{len(funcs)} = {len(typed)/len(funcs)*100:.0f}%')
"
```

**Why it matters:**
- Improves IDE autocomplete
- Catches type errors early
- Easier code review
- Better documentation

---

### 3. Add Type Hints to `web/backend/database.py`
- **Current Coverage:** 38% (15/40 functions)
- **Target Coverage:** 90%+ (36/40 functions)
- **Time:** 2 hours
- **Priority:** 🟡 Medium
- **Status:** ⬜ NOT STARTED

**What to do:**
```python
# Add typing imports
from typing import Optional, List, Dict, Any, Generator
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

# Before:
def get_user(user_id):
    return db.query(User).filter_by(id=user_id).first()

# After:
def get_user(user_id: int) -> Optional[User]:
    return db.query(User).filter_by(id=user_id).first()
```

**Acceptance Criteria:**
- [ ] All database functions have type hints
- [ ] Use `Optional[Model]` for queries that might return None
- [ ] Use `List[Model]` for queries returning multiple results
- [ ] Generator functions properly typed
- [ ] Code passes syntax check

**Why it matters:**
- Database queries are common error sources
- Type hints prevent None-related bugs
- Makes ORM usage clearer

---

### 4. Complete Type Hints in `shared/models/engine.py`
- **Current Coverage:** 76% (54/71 functions)
- **Target Coverage:** 95%+ (67/71 functions)
- **Time:** 1-2 hours
- **Priority:** 🟡 Medium
- **Status:** ⬜ NOT STARTED

**What to do:**
Add type hints to remaining 17 functions.

**Acceptance Criteria:**
- [ ] All public API functions have complete type hints
- [ ] Internal helper functions typed where practical
- [ ] Uses `DetectionResult` return type consistently
- [ ] Coverage ≥ 95%

**Why it matters:**
- Engine is the core of the application
- Most called module across the codebase
- Type safety here prevents cascading errors

---

### 5. Set Up mypy for Type Checking
- **Time:** 1 hour
- **Priority:** 🟡 Medium
- **Status:** ⬜ NOT STARTED

**What to do:**
1. Create `mypy.ini` configuration
2. Run mypy on critical modules
3. Fix any errors found
4. Document in README

**Configuration:**
```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False  # Start lenient
check_untyped_defs = True

[mypy-tests.*]
ignore_errors = True

[mypy-numpy.*]
ignore_missing_imports = True
```

**Acceptance Criteria:**
- [ ] mypy.ini created
- [ ] Can run `mypy shared/models/engine.py` without critical errors
- [ ] Can run `mypy web/backend/app.py` without critical errors
- [ ] Instructions added to docs/TESTING.md

**Why it matters:**
- Automated type checking
- Catches errors before runtime
- CI integration possible

---

## 📅 Medium Term (Months 2-3) - IMPORTANT

### 6. Split `web/backend/app.py` into Flask Blueprints
- **Current Size:** 1,511 lines
- **Target Size:** 200-300 lines main app + 6-8 blueprint files
- **Time:** 4-6 hours
- **Priority:** 🟡 Medium
- **Status:** ⬜ NOT STARTED

**What to do:**
```
Current: app.py (1,511 lines)

Proposed:
web/backend/
├── app.py (250 lines) - App initialization
├── routes/
│   ├── auth.py - Authentication
│   ├── receipts.py - Receipt management
│   ├── users.py - User management
│   ├── billing.py - Billing & subscriptions
│   ├── analytics.py - Analytics
│   └── health.py - Health checks
```

**Implementation Steps:**
1. Create `routes/` directory
2. Extract route groups to blueprints
3. Register blueprints in `app.py`
4. Update imports
5. Test all endpoints
6. Update documentation

**Acceptance Criteria:**
- [ ] No file exceeds 500 lines
- [ ] Each blueprint has single responsibility
- [ ] All tests pass
- [ ] No functionality changed
- [ ] API endpoints unchanged
- [ ] Imports updated across codebase

**How to verify:**
```bash
# All tests pass
pytest tools/tests/api/ -v

# No import errors
python -m py_compile web/backend/**/*.py

# App starts successfully
python web/backend/app.py
```

**Why it matters:**
- Easier to find specific functionality
- Reduces merge conflicts
- Smaller code review chunks
- Follows Flask best practices
- Team can work in parallel

---

### 7. Split `web/backend/database.py` Models
- **Current Size:** 1,390 lines
- **Target Size:** 200 lines core + 6-8 model files
- **Time:** 3-4 hours
- **Priority:** 🟡 Medium
- **Status:** ⬜ NOT STARTED

**What to do:**
```
Current: database.py (1,390 lines)

Proposed:
web/backend/
├── database.py (200 lines) - DB init, session management
├── models/
│   ├── __init__.py - Export all models
│   ├── user.py - User model
│   ├── receipt.py - Receipt model
│   ├── subscription.py - Subscription model
│   ├── usage.py - Usage tracking
│   └── audit.py - Audit logs
```

**Acceptance Criteria:**
- [ ] Models separated into logical files
- [ ] `__init__.py` exports all models for backward compatibility
- [ ] All relationships work correctly
- [ ] Migrations still run
- [ ] All tests pass

**Why it matters:**
- Each model can be understood independently
- Easier to find and modify specific models
- Reduces file size significantly

---

### 8. Split `shared/models/engine.py`
- **Current Size:** 1,756 lines
- **Target Size:** 300 lines orchestration + 4-5 module files
- **Time:** 4-6 hours
- **Priority:** 🟡 Medium
- **Status:** ⬜ NOT STARTED

**What to do:**
```
Current: engine.py (1,756 lines)

Proposed:
shared/models/
├── engine.py (300 lines) - Main orchestration
├── preprocessing/
│   ├── __init__.py
│   ├── image_preprocessor.py
│   └── filters.py
├── extraction/
│   ├── __init__.py
│   └── text_extractor.py
└── postprocessing/
    ├── __init__.py
    ├── text_cleaner.py
    └── result_merger.py
```

**Acceptance Criteria:**
- [ ] Clear separation of concerns
- [ ] Main engine.py coordinates stages
- [ ] Each stage in separate module
- [ ] All tests pass
- [ ] API unchanged

**Why it matters:**
- Engine is the most critical component
- Current size makes it hard to navigate
- Separation makes testing easier
- Each stage can evolve independently

---

## 🎓 Long Term (Months 4-6) - NICE TO HAVE

### 9. Split Large Test Files
- **Target:** No test file exceeds 1,000 lines
- **Time:** 8-12 hours total
- **Priority:** 🟢 Low
- **Status:** ⬜ NOT STARTED

**Files to split:**
```
2,417 lines - test_models.py → split by model type
2,244 lines - test_utils.py → split by utility category  
2,177 lines - test_ocr.py → split by OCR engine
2,040 lines - test_core.py → split by component
```

**Why it matters:**
- Test files are less critical than production code
- Current organization works but could be better
- Lower priority than production code splitting

---

### 10. CI Type Checking
- **Time:** 2 hours
- **Priority:** 🟢 Low
- **Status:** ⬜ NOT STARTED

**What to do:**
1. Add mypy to GitHub Actions
2. Run on critical files only initially
3. Gradually expand coverage

**Why it matters:**
- Automated type checking
- Prevents type regressions
- Quality gate for PRs

---

### 11. Performance Profiling
- **Time:** 4-6 hours
- **Priority:** 🟢 Low
- **Status:** ⬜ NOT STARTED

**What to do:**
1. Profile API endpoints
2. Identify bottlenecks
3. Optimize if needed
4. Document findings

**Why it matters:**
- Understand performance characteristics
- Identify optimization opportunities
- Plan for scaling

---

## 📊 Progress Tracking

### Overall Progress
- **Immediate (1 item):** ✅ 1/1 complete (100%)
- **Short Term (4 items):** ⬜ 0/4 complete (0%)
- **Medium Term (3 items):** ⬜ 0/3 complete (0%)
- **Long Term (3 items):** ⬜ 0/3 complete (0%)

**Total:** 1/11 complete (9%)

### Estimated Time Investment
- **Completed:** 0.08 hours (5 minutes)
- **Remaining Short Term:** 6-8 hours
- **Remaining Medium Term:** 11-16 hours
- **Remaining Long Term:** 14-20 hours
- **Total Remaining:** 31-44 hours (~1 month part-time)

### Priority Breakdown
- 🟢 **Low Priority:** 4 items (can skip if needed)
- 🟡 **Medium Priority:** 7 items (recommended for quality)
- 🔴 **High Priority:** 0 items (none!)

---

## 🎯 Recommended 30-Day Plan

### Week 1: Type Hints Sprint
- Day 1-2: Add type hints to `app.py` ✓
- Day 3-4: Add type hints to `database.py` ✓
- Day 5: Complete `engine.py` type hints ✓

### Week 2: Setup & Validation
- Day 1: Set up mypy configuration ✓
- Day 2-3: Fix mypy errors ✓
- Day 4-5: Documentation and verification ✓

### Week 3-4: File Splitting (Optional)
- Week 3: Split `app.py` into blueprints ✓
- Week 4: Split `database.py` models ✓

---

## ✅ How to Mark Items Complete

When completing an item:
1. Check all acceptance criteria
2. Run verification commands
3. Update status from ⬜ to ✅
4. Add completion date
5. Note any deviations or findings

**Example:**
```markdown
### 2. Add Type Hints to `web/backend/app.py`
- **Status:** ✅ COMPLETED (2026-01-15)
- **Actual Time:** 1.5 hours
- **Notes:** Also improved function docstrings while adding hints
```

---

## 📝 Notes

### Why These Priorities?

**Medium Priority (not High) because:**
- Code works correctly now
- Not blocking production
- Primarily impacts developer experience
- Can be done incrementally
- Won't cause user-facing issues if delayed

**Low Priority items:**
- Nice to have but optional
- High effort to benefit ratio
- Can be delayed indefinitely without consequence

### Success Metrics

After completing Short Term items:
- Developer satisfaction ↑
- Onboarding time ↓
- Code review time ↓
- Bug detection in development ↑

After completing Medium Term items:
- Merge conflicts ↓
- Time to locate code ↓
- Parallel development easier
- Technical debt ↓

---

*This checklist provides concrete, actionable steps for improving code quality*  
*All items are optional improvements, not blocking issues*  
*Date: 2026-01-01*
