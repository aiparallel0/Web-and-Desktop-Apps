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
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f"Module registration failed: {e}")
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Re-export DonutFinetuner from engine module
# Use relative import since this module is part of the shared.models package
from .engine import DonutFinetuner

__all__ = ['DonutFinetuner']
