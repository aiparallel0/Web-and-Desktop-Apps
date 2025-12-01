# AI Agent Instructions for Receipt Extractor

## ⚠️ STOP AND READ THIS FIRST ⚠️

**This document contains MANDATORY instructions for ALL AI agents (Claude, ChatGPT, Gemini, Copilot, Cursor, or any other) working on this codebase.**

---

## The Circular Exchange Framework Requirement

This project uses the **Circular Exchange Framework** - a reactive configuration and dependency management system. 

**ALL code contributions MUST integrate with this framework. No exceptions.**

---

## Before You Write Any Code

1. **Read `CIRCULAR_EXCHANGE_GUIDE.md`** - Complete integration guide
2. **Check `shared/circular_exchange/__init__.py`** - Framework API
3. **Study `shared/models/ocr_config.py`** - Reference implementation

---

## Mandatory Code Pattern

Every Python file MUST include:

### 1. Framework Import Block (at top of file)

```python
# Circular Exchange Framework Integration (MANDATORY)
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False
```

### 2. Module Registration (after imports)

```python
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="your.module.name",      # e.g., "shared.utils.my_module"
            file_path=__file__,
            description="Brief description of module purpose",
            dependencies=["shared.circular_exchange", "other.dependencies"],
            exports=["ClassName", "function_name"]
        ))
    except Exception:
        pass
```

### 3. Configuration Using VariablePackage

```python
# Instead of hardcoded values:
THRESHOLD = 0.5  # ❌ WRONG

# Use VariablePackage:
_registry = PackageRegistry()
_registry.create_package(
    name='module.threshold',
    initial_value=0.5,
    source_module='your.module',
    validator=lambda v: 0.0 <= v <= 1.0
)

def get_threshold():
    pkg = _registry.get_package('module.threshold')
    return pkg.get() if pkg else 0.5
```

---

## Why This Is Required

The Circular Exchange Framework provides:

| Feature | Benefit |
|---------|---------|
| Runtime Tuning | Change parameters without code changes |
| Auto-Tuning | Parameters adjust based on success rates |
| Reactive Updates | Changes propagate to all subscribers |
| Dependency Tracking | Know what depends on what |
| Centralized Config | Single source of truth |
| Better Testing | Easy to mock configurations |

---

## Validation Checklist

Before completing ANY task, verify:

- [ ] All new files import from `shared.circular_exchange`
- [ ] All new modules are registered with `PROJECT_CONFIG.register_module()`
- [ ] All configurable parameters use `VariablePackage`
- [ ] Dependencies are listed in the `ModuleRegistration`
- [ ] Exports are listed in the `ModuleRegistration`
- [ ] Module has a description in the registration
- [ ] Tests verify the circular exchange integration

---

## Quick Reference

### File Locations

| File | Purpose |
|------|---------|
| `CIRCULAR_EXCHANGE_GUIDE.md` | Complete developer guide |
| `shared/circular_exchange/__init__.py` | Framework public API |
| `shared/circular_exchange/variable_package.py` | VariablePackage implementation |
| `shared/circular_exchange/project_config.py` | PROJECT_CONFIG singleton |
| `shared/models/ocr_config.py` | Reference implementation |

### Key Classes

| Class | Purpose |
|-------|---------|
| `PROJECT_CONFIG` | Central configuration hub |
| `ModuleRegistration` | Module registration data |
| `VariablePackage` | Reactive configuration container |
| `PackageRegistry` | Registry of all packages |

### Common Imports

```python
from shared.circular_exchange import (
    PROJECT_CONFIG,        # Central config hub
    ModuleRegistration,    # For registering modules
    VariablePackage,       # For reactive values
    PackageRegistry,       # For managing packages
    PackageChange          # For change notifications
)
```

---

## Error Handling

Always wrap registrations in try/except to handle import order issues:

```python
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(...)
    except Exception:
        pass  # Ignore registration errors during import
```

---

## Testing Requirements

Tests should verify circular exchange integration:

```python
def test_uses_circular_exchange():
    """Verify module uses circular exchange configuration."""
    from my_module import MyClass
    
    obj = MyClass()
    
    # Verify it uses VariablePackage, not hardcoded values
    pkg = obj._registry.get_package('my_module.parameter')
    assert pkg is not None, "Must use circular exchange"
    
    # Verify dynamic updates work
    original = obj.parameter
    pkg.set(new_value)
    assert obj.parameter == new_value
```

---

## Summary

**Every file. Every module. Every configuration value.**

All must integrate with the Circular Exchange Framework.

This is not optional. This is the architecture of this project.

**Read `CIRCULAR_EXCHANGE_GUIDE.md` before writing any code.**
