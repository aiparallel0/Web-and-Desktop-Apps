# Copilot Instructions

**All code must integrate with the Circular Exchange Framework.**

Reference: `shared/models/ocr_config.py`

```python
from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
PROJECT_CONFIG.register_module(ModuleRegistration(
    module_id="your.module", file_path=__file__,
    dependencies=["deps"], exports=["exports"]))
```
