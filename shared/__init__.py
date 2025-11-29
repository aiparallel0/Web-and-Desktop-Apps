"""
=============================================================================
SHARED CORE MODULE - Enterprise Architecture Foundation
=============================================================================

This module serves as the foundational layer for the Receipt Extraction System,
implementing enterprise-grade patterns used by top-tier technology companies.

Architecture Principles:
- Circular Information Exchange: Automatic dependency tracking and update propagation
- Event-Driven Design: Loose coupling through event-based communication
- Hexagonal Architecture: Domain-centric design with ports and adapters
- SOLID Principles: Single responsibility, Open/Closed, Liskov substitution,
                    Interface segregation, Dependency inversion

Module Structure:
├── circular_exchange/   - Core framework for dependency management
├── models/             - AI/ML model management and processors
├── utils/              - Cross-cutting utilities and data structures
└── config/             - Configuration management

Integration Pattern:
    from shared import CircularExchange, VariablePackage
    
    # Initialize global exchange
    exchange = CircularExchange.get_instance()
    
    # Create reactive data packages
    config = exchange.create_package('app_config', initial_value={})
    
    # Automatic dependency propagation
    exchange.register_module('my_module', __file__)

=============================================================================
"""

from typing import TYPE_CHECKING

# Lazy imports for performance optimization
_CIRCULAR_EXCHANGE_IMPORTS = {
    'CircularExchange': 'circular_exchange.circular_exchange',
    'DependencyRegistry': 'circular_exchange.dependency_registry',
    'VariablePackage': 'circular_exchange.variable_package',
    'PackageRegistry': 'circular_exchange.variable_package',
    'ChangeNotifier': 'circular_exchange.change_notifier',
    'ChangeType': 'circular_exchange.change_notifier',
}

_MODEL_IMPORTS = {
    'ModelManager': 'models.model_manager',
    'BaseProcessor': 'models.processors',
    'EasyOCRProcessor': 'models.processors',
    'PaddleProcessor': 'models.processors',
}

_UTIL_IMPORTS = {
    'LineItem': 'utils.data_structures',
    'ReceiptData': 'utils.data_structures',
    'ExtractionResult': 'utils.data_structures',
    'setup_logger': 'utils.logger',
    'get_logger': 'utils.logger',
}


def __getattr__(name: str):
    """
    Lazy import handler for enterprise-grade module loading.
    
    This pattern provides:
    - Faster initial import times
    - Reduced memory footprint
    - Better dependency isolation
    """
    import importlib
    
    all_imports = {**_CIRCULAR_EXCHANGE_IMPORTS, **_MODEL_IMPORTS, **_UTIL_IMPORTS}
    
    if name in all_imports:
        module_path = all_imports[name]
        full_path = f"shared.{module_path}"
        module = importlib.import_module(full_path.rsplit('.', 1)[0], package='shared')
        return getattr(module, name)
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Circular Exchange Framework
    'CircularExchange',
    'DependencyRegistry', 
    'VariablePackage',
    'PackageRegistry',
    'ChangeNotifier',
    'ChangeType',
    # Model Management
    'ModelManager',
    'BaseProcessor',
    'EasyOCRProcessor',
    'PaddleProcessor',
    # Data Structures
    'LineItem',
    'ReceiptData',
    'ExtractionResult',
    # Utilities
    'setup_logger',
    'get_logger',
]

__version__ = '2.0.0'
__author__ = 'Enterprise Architecture Team'