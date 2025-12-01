# File Relationships for AI Agents

This document provides a structured view of the file relationships in the Web-and-Desktop-Apps project, optimized for AI agent comprehension.

## Table of Contents
- [Circular Exchange Framework](#circular-exchange-framework)
- [Module Dependency Graph](#module-dependency-graph)
- [Integration Status](#integration-status)
- [Quick Reference](#quick-reference)

---

## Circular Exchange Framework

The **Circular Exchange Framework** is the central configuration and dependency management system.

### Core Components

| Component | File Path | Purpose |
|-----------|-----------|---------|
| PROJECT_CONFIG | `shared/circular_exchange/project_config.py` | Global configuration singleton hub |
| VariablePackage | `shared/circular_exchange/variable_package.py` | Observable value containers with auto-tuning |
| PackageRegistry | `shared/circular_exchange/variable_package.py` | Registry for managing multiple packages |
| ModuleRegistration | `shared/circular_exchange/project_config.py` | Module metadata for dependency tracking |
| ChangeNotifier | `shared/circular_exchange/change_notifier.py` | Change event propagation |
| DependencyRegistry | `shared/circular_exchange/dependency_registry.py` | Module dependency tracking |
| ModuleContainer | `shared/circular_exchange/module_container.py` | Docker-like module isolation |

### Integration Pattern

```python
# Step 1: Import framework
from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry

# Step 2: Register module
PROJECT_CONFIG.register_module(ModuleRegistration(
    module_id="your.module.name",
    file_path=__file__,
    description="Brief description",
    dependencies=["list", "of", "dependencies"],
    exports=["ExportedClass", "exported_function"]
))

# Step 3: Create variable packages for configurable parameters
registry = PackageRegistry()
registry.create_package(
    name='module.parameter_name',
    initial_value=default_value,
    source_module='your.module.name',
    validator=lambda v: validation_expression
)
```

---

## Module Dependency Graph

### Layer 1: Circular Exchange Core (Foundation)

```
shared/circular_exchange/
├── __init__.py            # Public API exports
├── project_config.py      # PROJECT_CONFIG singleton
├── variable_package.py    # VariablePackage, PackageRegistry
├── change_notifier.py     # Change event system
├── dependency_registry.py # Module tracking
├── circular_exchange.py   # Core exchange logic
├── module_container.py    # Container orchestration
└── style_checker.py       # Code style validation
```

### Layer 2: Configuration

```
shared/
├── models/ocr_config.py   # OCR parameter configuration (✓ Integrated)
└── config/settings.py     # Project settings
```

### Layer 3: Models (Processing Logic)

```
shared/models/
├── ocr_processor.py       # Tesseract OCR processor (✓ Integrated)
├── processors.py          # EasyOCR, PaddleOCR processors
├── ai_models.py           # AI/ML models (Florence-2)
├── model_manager.py       # Model lifecycle management
└── ocr_common.py          # Shared OCR utilities
```

### Layer 4: Utilities

```
shared/utils/
├── image_processing.py    # Image preprocessing (✓ Integrated)
├── data_structures.py     # Receipt data models (✓ Integrated)
├── centralized_logging.py # Logging system (✓ Integrated)
└── errors.py              # Error handling (✓ Integrated)
```

### Layer 5: Web Application

```
web-app/backend/
├── app.py                 # Flask application
├── auth.py                # Authentication
└── database.py            # Database operations
```

---

## Detailed Module Dependencies

### shared/models/ocr_processor.py

**Module ID:** `shared.models.ocr_processor`

**Dependencies:**
- `shared.circular_exchange` (PROJECT_CONFIG, ModuleRegistration, PackageRegistry)
- `shared.utils.image_processing` (load_and_validate_image, preprocess_for_ocr)
- `shared.utils.data_structures` (LineItem, ReceiptData, ExtractionResult)
- `shared.models.ocr_common` (get_detection_config, record_detection_result)
- `pytesseract` (external)
- `PIL` (external)
- `cv2` (external)
- `numpy` (external)

**Exports:**
- `OCRProcessor` class

**Circular Exchange Integration:**
- ✅ Module registered with PROJECT_CONFIG
- ✅ Uses get_detection_config() from ocr_common
- ✅ Records detection results for auto-tuning

---

### shared/utils/image_processing.py

**Module ID:** `shared.utils.image_processing`

**Dependencies:**
- `shared.circular_exchange` (PROJECT_CONFIG, ModuleRegistration, PackageRegistry)
- `PIL` (external)
- `cv2` (external)
- `numpy` (external)

**Exports:**
- `load_and_validate_image(image_path: str) -> Image.Image`
- `enhance_image(image: Image.Image, ...) -> Image.Image`
- `preprocess_for_ocr(image: Image.Image, aggressive: bool) -> Image.Image`
- `assess_image_quality(image: Image.Image) -> dict`
- `get_image_config() -> dict`
- `detect_text_regions(image: Image.Image) -> list`
- `preprocess_multi_pass(image: Image.Image) -> list`

**Configuration Packages:**
| Package Name | Default | Validator |
|--------------|---------|-----------|
| `image.brightness_threshold` | 100 | 0 <= v <= 255 |
| `image.contrast_threshold` | 40 | 0 <= v <= 255 |
| `image.upscale_threshold` | 1000 | v >= 100 |
| `image.enhancement_factor` | 1.2 | 0.5 <= v <= 3.0 |

---

### shared/models/ocr_config.py

**Module ID:** `shared.models.ocr_config`

**Dependencies:**
- `shared.circular_exchange.variable_package` (VariablePackage, PackageRegistry)

**Exports:**
- `OCRConfig` class (singleton)
- `get_ocr_config() -> OCRConfig`
- `reset_ocr_config() -> None`
- `OCRPipelineStage` dataclass

**Configuration Packages:**
| Package Name | Default | Purpose |
|--------------|---------|---------|
| `ocr.min_confidence` | 0.3 | Minimum confidence threshold |
| `ocr.relaxed_confidence` | 0.2 | Relaxed mode threshold |
| `ocr.relaxed_mode` | False | Enable relaxed validation |
| `ocr.auto_fallback` | True | Auto-fallback to relaxed mode |
| `ocr.detection.min_confidence` | 0.25 | Detection confidence |
| `ocr.detection.box_threshold` | 0.3 | Box detection threshold |
| `ocr.detection.auto_retry` | True | Auto-retry on failure |

**Key Methods:**
- `get_detection_config() -> Dict` - Returns all detection parameters
- `record_detection_result(...)` - Records for auto-tuning
- `export_config() -> Dict` - Export current configuration
- `import_config(config: Dict)` - Import configuration

---

## Integration Status

### ✅ Fully Integrated with Circular Exchange

| Module | Integration Features |
|--------|---------------------|
| `shared/models/ocr_config.py` | VariablePackage, auto-tuning, pipeline stages |
| `shared/models/ocr_processor.py` | ModuleRegistration, detection config |
| `shared/utils/image_processing.py` | ModuleRegistration, PackageRegistry |
| `shared/utils/data_structures.py` | ModuleRegistration |
| `shared/utils/centralized_logging.py` | ModuleRegistration |
| `shared/utils/errors.py` | ModuleRegistration |

### ⚠️ Needs Integration

| Module | Status |
|--------|--------|
| `shared/models/ai_models.py` | Missing ModuleRegistration |
| `shared/models/processors.py` | Missing ModuleRegistration |
| `shared/config/settings.py` | Missing ModuleRegistration |
| `web-app/backend/app.py` | Missing ModuleRegistration |
| `web-app/backend/auth.py` | Missing ModuleRegistration |
| `web-app/backend/database.py` | Missing ModuleRegistration |

---

## Quick Reference

### How to Check if a Module is Integrated

```python
from shared.circular_exchange import PROJECT_CONFIG

# After importing the module you want to check
print(PROJECT_CONFIG.get_all_modules())
# Should include the module_id if properly integrated
```

### How to Get Configuration Values

```python
# For OCR configuration
from shared.models.ocr_config import get_ocr_config
config = get_ocr_config()
min_conf = config.min_confidence

# For image processing configuration
from shared.utils.image_processing import get_image_config
img_config = get_image_config()
brightness_threshold = img_config['brightness_threshold']
```

### How to Subscribe to Changes

```python
from shared.circular_exchange import PROJECT_CONFIG

# Subscribe to debug mode changes
PROJECT_CONFIG.debug.subscribe(
    lambda change: print(f"Debug changed: {change.new_value}")
)

# Subscribe to specific package
config = get_ocr_config()
pkg = config.get_package('ocr.min_confidence')
pkg.subscribe(lambda c: handle_confidence_change(c))
```

---

## Data Flow Diagram (Text)

```
┌─────────────────┐
│   Image Input   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   shared/utils/image_processing.py  │
│   - load_and_validate_image()       │
│   - preprocess_for_ocr()            │
│   - get_image_config() ◄── CE       │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   shared/models/ocr_processor.py    │
│   - OCRProcessor.extract()          │
│   - get_detection_config() ◄── CE   │
│   - record_detection_result() ►─ CE │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   shared/models/ocr_config.py       │
│   - OCRConfig (singleton)           │
│   - Auto-tuning parameters          │
│   - Pipeline stage tracking         │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   shared/utils/data_structures.py   │
│   - ReceiptData                     │
│   - LineItem                        │
│   - ExtractionResult                │
└─────────────────────────────────────┘

CE = Circular Exchange Framework
```

---

## Related Documentation

- [CIRCULAR_EXCHANGE_GUIDE.md](../CIRCULAR_EXCHANGE_GUIDE.md) - Full integration guide
- [docs/FILE_RELATIONSHIPS.html](FILE_RELATIONSHIPS.html) - Visual web diagram
- [docs/FILE_RELATIONSHIPS.json](FILE_RELATIONSHIPS.json) - Machine-readable format
