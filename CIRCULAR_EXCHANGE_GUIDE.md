# Circular Exchange Framework - Developer Guide

## ⚠️ AI AGENT MANDATORY REQUIREMENT ⚠️

**ALL AI AGENTS (GitHub Copilot, ChatGPT, Claude, or any other) MUST integrate code with the Circular Exchange Framework when developing in this project.**

This is a **non-negotiable architectural requirement** for this codebase. Every new module, class, or function must be connected to the Circular Exchange Framework.

---

## What is the Circular Exchange Framework?

The Circular Exchange Framework is a reactive configuration and dependency management system that:

1. **Connects all modules** through a shared dependency graph
2. **Propagates changes automatically** when configuration updates
3. **Enables variable-based parameters** that can be tuned at runtime
4. **Tracks module dependencies** for proper update ordering
5. **Provides auto-tuning capabilities** based on success/failure metrics

---

## Quick Integration Guide

### Step 1: Import the Framework

```python
# At the top of your new file, add:
from shared.circular_exchange import (
    PROJECT_CONFIG,
    ModuleRegistration,
    VariablePackage,
    PackageRegistry
)
```

### Step 2: Register Your Module

```python
# After imports, register your module:
PROJECT_CONFIG.register_module(ModuleRegistration(
    module_id="your.module.name",
    file_path=__file__,
    dependencies=["shared.utils", "shared.models"],  # List your dependencies
    exports=["YourClassName", "your_function"]        # List what you export
))
```

### Step 3: Create Variable Packages for Configurable Parameters

```python
# Instead of hardcoded values:
MIN_CONFIDENCE = 0.3  # ❌ Don't do this

# Use VariablePackage:
class MyProcessor:
    def __init__(self):
        self._registry = PackageRegistry()
        
        # Create a variable package for configurable parameters
        self._registry.create_package(
            name='my_module.min_confidence',
            initial_value=0.3,
            source_module='my_module',
            validator=lambda v: 0.0 <= v <= 1.0  # Optional validation
        )
    
    @property
    def min_confidence(self) -> float:
        pkg = self._registry.get_package('my_module.min_confidence')
        return pkg.get() if pkg else 0.3
```

### Step 4: Subscribe to Configuration Changes

```python
# Subscribe to global project config changes:
PROJECT_CONFIG.debug.subscribe(
    lambda change: print(f"Debug mode changed: {change.new_value}")
)

# Or subscribe to your own packages:
pkg = self._registry.get_package('my_module.min_confidence')
pkg.subscribe(lambda change: self._on_confidence_changed(change))
```

---

## Integration Patterns by Module Type

### For OCR/Processing Modules

```python
"""
Example: OCR Processor with Circular Exchange
"""
from shared.circular_exchange import PackageRegistry, PROJECT_CONFIG, ModuleRegistration
from shared.models.ocr_config import get_ocr_config, get_detection_config, record_detection_result

# Register module
PROJECT_CONFIG.register_module(ModuleRegistration(
    module_id="my_ocr_processor",
    file_path=__file__,
    dependencies=["shared.models.ocr_config"],
    exports=["MyOCRProcessor"]
))

class MyOCRProcessor:
    def __init__(self):
        # Get the global OCR config (circular exchange integrated)
        self.ocr_config = get_ocr_config()
    
    def process(self, image_path: str):
        # Get detection config from circular exchange
        detection_config = get_detection_config()
        min_confidence = detection_config.get('min_confidence', 0.25)
        
        # ... processing logic ...
        
        # Record results for auto-tuning
        record_detection_result(
            text_regions_count=len(results),
            avg_confidence=avg_confidence,
            success=True,
            processing_time=elapsed_time
        )
```

### For Utility Modules

```python
"""
Example: Utility module with Circular Exchange
"""
from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, VariablePackage

PROJECT_CONFIG.register_module(ModuleRegistration(
    module_id="shared.utils.my_utility",
    file_path=__file__,
    dependencies=[],
    exports=["my_function", "MyUtilityClass"]
))

# Create variable packages for configurable parameters
_config_registry = PackageRegistry()
_config_registry.create_package(
    name='utils.max_retries',
    initial_value=3,
    source_module='shared.utils.my_utility'
)

def get_max_retries() -> int:
    """Get max retries from circular exchange config."""
    pkg = _config_registry.get_package('utils.max_retries')
    return pkg.get() if pkg else 3
```

### For API/Backend Modules

```python
"""
Example: Flask API with Circular Exchange
"""
from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration

PROJECT_CONFIG.register_module(ModuleRegistration(
    module_id="web-app.backend.app",
    file_path=__file__,
    dependencies=["shared.models.model_manager", "shared.models.ocr_config"],
    exports=["app", "process_receipt"]
))

# Subscribe to config changes to update runtime behavior
PROJECT_CONFIG.debug.subscribe(
    lambda c: app.config.update({'DEBUG': c.new_value})
)
```

---

## Mandatory Checklist for New Code

Before submitting any code, verify:

- [ ] **Module is registered** with `PROJECT_CONFIG.register_module()`
- [ ] **Dependencies are listed** in the registration
- [ ] **Exports are documented** in the registration
- [ ] **Configurable parameters use VariablePackage** instead of hardcoded values
- [ ] **Changes are recorded** for auto-tuning (if applicable)
- [ ] **Tests verify circular exchange integration** works correctly

---

## File Structure and Circular Exchange

```
shared/
├── circular_exchange/          # Core framework (DO NOT MODIFY without approval)
│   ├── __init__.py            # Public API exports
│   ├── variable_package.py    # VariablePackage for reactive values
│   ├── project_config.py      # PROJECT_CONFIG singleton
│   ├── dependency_registry.py # Module dependency tracking
│   ├── change_notifier.py     # Change propagation
│   ├── circular_exchange.py   # Core exchange logic
│   ├── module_container.py    # Container orchestration
│   └── style_checker.py       # Code style validation
│
├── models/                    # All modules here MUST integrate
│   ├── ocr_config.py         # ✅ Already integrated
│   ├── processors.py         # ✅ Already integrated  
│   ├── model_manager.py      # ✅ Already integrated
│   └── ai_models.py          # ⚠️ Needs integration
│
├── utils/                    # All modules here MUST integrate
│   ├── data_structures.py   # ⚠️ Needs integration
│   ├── image_processing.py  # ⚠️ Needs integration
│   └── errors.py            # ⚠️ Needs integration
│
└── config/                   # All modules here MUST integrate
    └── settings.py          # ⚠️ Needs integration

web-app/backend/             # All modules here MUST integrate
├── app.py                   # ⚠️ Needs integration
├── auth.py                  # ⚠️ Needs integration
└── database.py              # ⚠️ Needs integration
```

---

## Benefits of Circular Exchange Integration

1. **Runtime Parameter Tuning**: Change thresholds without code changes
2. **Auto-Tuning**: Parameters automatically adjust based on success rates
3. **Reactive Updates**: When config changes, all subscribers update
4. **Dependency Tracking**: Know exactly what depends on what
5. **Centralized Configuration**: One source of truth for all settings
6. **Better Testing**: Mock configurations easily in tests

---

## Example: Converting Legacy Code

### Before (Legacy Code)

```python
# old_processor.py - NOT integrated ❌

class OldProcessor:
    MIN_CONFIDENCE = 0.3  # Hardcoded
    MAX_RETRIES = 3       # Hardcoded
    
    def process(self, data):
        if data.confidence < self.MIN_CONFIDENCE:
            return None
        # ... rest of processing
```

### After (Circular Exchange Integrated)

```python
# new_processor.py - Integrated ✅

from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry

# Register module
PROJECT_CONFIG.register_module(ModuleRegistration(
    module_id="processors.new_processor",
    file_path=__file__,
    dependencies=["shared.models.ocr_config"],
    exports=["NewProcessor"]
))

class NewProcessor:
    def __init__(self):
        self._registry = PackageRegistry()
        
        # Create variable packages
        self._registry.create_package(
            name='processor.min_confidence',
            initial_value=0.3,
            source_module='processors.new_processor',
            validator=lambda v: 0.0 <= v <= 1.0
        )
        self._registry.create_package(
            name='processor.max_retries',
            initial_value=3,
            source_module='processors.new_processor',
            validator=lambda v: v >= 0
        )
    
    @property
    def min_confidence(self) -> float:
        pkg = self._registry.get_package('processor.min_confidence')
        return pkg.get() if pkg else 0.3
    
    @property
    def max_retries(self) -> int:
        pkg = self._registry.get_package('processor.max_retries')
        return pkg.get() if pkg else 3
    
    def process(self, data):
        if data.confidence < self.min_confidence:  # Now configurable!
            return None
        # ... rest of processing
```

---

## Testing Circular Exchange Integration

```python
# test_my_processor.py

import pytest
from shared.models.ocr_config import OCRConfig, reset_ocr_config

class TestMyProcessor:
    def setup_method(self):
        """Reset config for clean test state."""
        reset_ocr_config()
    
    def test_uses_circular_exchange_config(self):
        """Verify processor uses circular exchange configuration."""
        from my_module import MyProcessor
        
        processor = MyProcessor()
        
        # Get the config package
        pkg = processor._registry.get_package('processor.min_confidence')
        assert pkg is not None, "Processor must use circular exchange"
        
        # Verify default value
        assert processor.min_confidence == 0.3
        
        # Test dynamic update
        pkg.set(0.5)
        assert processor.min_confidence == 0.5
```

---

## Summary

**Every file in this project MUST:**

1. Import from `shared.circular_exchange`
2. Register itself with `PROJECT_CONFIG.register_module()`
3. Use `VariablePackage` for configurable parameters
4. Record results for auto-tuning (when applicable)
5. Include tests verifying the integration

**AI Agents: This is not optional. Follow this guide for all code contributions.**
