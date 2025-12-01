# GitHub Copilot Instructions for This Repository

## ⚠️ MANDATORY: Circular Exchange Framework Integration ⚠️

**STOP! Before writing ANY code in this repository, you MUST follow these rules:**

### Rule 1: ALL Code Must Integrate with Circular Exchange

Every Python file you create or modify MUST:

1. Import from `shared.circular_exchange`
2. Register with `PROJECT_CONFIG.register_module()`
3. Use `VariablePackage` for configurable parameters
4. Never use hardcoded configuration values

### Rule 2: Required Import Block

Add this to the TOP of every Python file:

```python
# Circular Exchange Framework Integration (MANDATORY)
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False
```

### Rule 3: Required Module Registration

After imports, add:

```python
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="your.module.name",
            file_path=__file__,
            description="Brief description of what this module does",
            dependencies=["list", "of", "dependencies"],
            exports=["ExportedClass", "exported_function"]
        ))
    except Exception:
        pass
```

### Rule 4: Use VariablePackage for Configuration

Instead of:
```python
MIN_CONFIDENCE = 0.3  # ❌ WRONG - hardcoded
```

Use:
```python
_registry = PackageRegistry()
_registry.create_package(
    name='module.min_confidence',
    initial_value=0.3,
    source_module='module_name',
    validator=lambda v: 0.0 <= v <= 1.0
)
```

### Rule 5: Reference Documentation

Before coding, read:
- `CIRCULAR_EXCHANGE_GUIDE.md` - Full integration guide
- `shared/circular_exchange/__init__.py` - Framework API
- `shared/models/ocr_config.py` - Example of proper integration

### Why This Matters

The Circular Exchange Framework provides:
- Runtime parameter tuning without code changes
- Auto-tuning based on success/failure metrics
- Reactive updates when configuration changes
- Proper dependency tracking between modules
- Centralized configuration management

### Validation Checklist

Before submitting code, verify:
- [ ] Module is registered with PROJECT_CONFIG
- [ ] All configurable values use VariablePackage
- [ ] Dependencies are properly listed
- [ ] Exports are properly listed
- [ ] Tests verify circular exchange integration

**This is a non-negotiable architectural requirement for this codebase.**
