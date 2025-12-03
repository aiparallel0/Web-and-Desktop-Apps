"""
=============================================================================
DONUT FINETUNER MODULE - Model Finetuning for Donut Models
=============================================================================

Module: shared.models.donut_finetuner
Description: Re-exports DonutFinetuner class from engine module
Compliance Version: 2.0.0

CIRCULAR EXCHANGE INTEGRATION:
This module is integrated with the Circular Information Exchange Framework.
It provides the DonutFinetuner class for finetuning Donut models on custom
receipt data.

Dependencies: shared.models.engine, shared.circular_exchange
Exports: DonutFinetuner

=============================================================================
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
    
    PROJECT_CONFIG.register_module(ModuleRegistration(
        module_id="shared.models.donut_finetuner",
        file_path=__file__,
        description="Donut model finetuning module",
        dependencies=["shared.models.engine", "shared.circular_exchange"],
        exports=["DonutFinetuner"]
    ))
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Re-export DonutFinetuner from engine module
# Using try/except for both absolute and relative imports
try:
    from .engine import DonutFinetuner
except ImportError:
    try:
        from shared.models.engine import DonutFinetuner
    except ImportError:
        from engine import DonutFinetuner

__all__ = ['DonutFinetuner']
