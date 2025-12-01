"""
=============================================================================
CIRCULAR EXCHANGE COMPLIANT MODULE
=============================================================================

Module: shared
Path: shared/__init__.py
Description: SHARED CORE MODULE - Enterprise Architecture Foundation
Compliance Version: 2.0.0

CIRCULAR EXCHANGE INTEGRATION:
This module is the root of the Circular Information Exchange Framework.
All submodules are integrated and tracked through the reactive system.

Dependencies: None (Root module)
Exports: CircularExchange, VariablePackage, PROJECT_CONFIG, all submodule exports

AI AGENT INSTRUCTIONS:
- Always import PROJECT_CONFIG for configuration values
- Register modules with CircularExchange
- Use VariablePackages for shared data
- All modules in this package are circular exchange compliant

=============================================================================

SHARED CORE MODULE - Enterprise Architecture Foundation

This module serves as the foundational layer for the Receipt Extraction System,
implementing production-proven patterns for scalable OCR processing.

Architecture Principles:
- Circular Information Exchange: Automatic dependency tracking and update propagation
- Variable-Based Coding: Centralized configuration via PROJECT_CONFIG
- Event-Driven Design: Loose coupling through event-based communication
- Hexagonal Architecture: Domain-centric design with ports and adapters
- SOLID Principles: Single responsibility, Open/Closed, Liskov substitution,
                    Interface segregation, Dependency inversion

Module Structure:
├── circular_exchange/   - Core framework for dependency management
│   ├── project_config.py   - CENTRAL VARIABLE-BASED CONFIGURATION HUB
│   ├── circular_exchange.py - Main orchestrator
│   ├── dependency_registry.py - Module dependency tracking
│   ├── variable_package.py - Observable data containers
│   └── change_notifier.py - Event propagation system
├── models/             - AI/ML model management and processors
├── utils/              - Cross-cutting utilities and data structures
└── config/             - Configuration management

Integration Pattern:
    from shared import CircularExchange, VariablePackage, PROJECT_CONFIG
    
    # Access centralized configuration
    debug_mode = PROJECT_CONFIG.debug.value
    
    # Initialize global exchange
    exchange = CircularExchange.get_instance()
    
    # Create reactive data packages
    config = exchange.create_package('app_config', initial_value={})
    
    # Automatic dependency propagation
    exchange.register_module('my_module', __file__)

Usage for centralized logging:
    from shared.utils import get_module_logger, log_errors
    logger = get_module_logger()
    
    @log_errors
    def my_function():
        logger.info("Processing...")

=============================================================================
"""

from typing import TYPE_CHECKING

# =============================================================================
# CIRCULAR EXCHANGE INTEGRATION - ROOT MODULE REGISTRATION
# =============================================================================
try:
    from shared.circular_exchange.project_config import PROJECT_CONFIG, ModuleRegistration
    
    # Register this root module with the circular exchange
    PROJECT_CONFIG.register_module(ModuleRegistration(
        module_id="shared",
        file_path="shared/__init__.py",
        description="Shared Core Module - Enterprise Architecture Foundation",
        dependencies=[],
        exports=[
            "CircularExchange", "VariablePackage", "PROJECT_CONFIG",
            "DependencyRegistry", "ChangeNotifier", "ModelManager",
            "LineItem", "ReceiptData", "ExtractionResult"
        ],
        is_circular_exchange_compliant=True,
        compliance_version="2.0.0"
    ))
except ImportError:
    PROJECT_CONFIG = None  # Graceful fallback

# Lazy imports for performance optimization
_CIRCULAR_EXCHANGE_IMPORTS = {
    'CircularExchange': 'circular_exchange.circular_exchange',
    'DependencyRegistry': 'circular_exchange.dependency_registry',
    'VariablePackage': 'circular_exchange.variable_package',
    'PackageRegistry': 'circular_exchange.variable_package',
    'ChangeNotifier': 'circular_exchange.change_notifier',
    'ChangeType': 'circular_exchange.change_notifier',
    'PROJECT_CONFIG': 'circular_exchange.project_config',
    'ProjectConfiguration': 'circular_exchange.project_config',
    'ModuleRegistration': 'circular_exchange.project_config',
    'SecurityPolicy': 'circular_exchange.project_config',
    'CodingStandards': 'circular_exchange.project_config',
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
    'get_module_logger': 'utils.centralized_logging',
    'log_errors': 'utils.centralized_logging',
    'logging_context': 'utils.centralized_logging',
    'set_context': 'utils.centralized_logging',
    'clear_context': 'utils.centralized_logging',
    'ErrorHandler': 'utils.centralized_logging',
}


def __getattr__(name: str):
    """
    Lazy import handler for optimized module loading.
    
    This pattern provides:
    - Faster initial import times
    - Reduced memory footprint
    - Better dependency isolation
    
    CIRCULAR EXCHANGE NOTE:
    All lazy-loaded modules are automatically registered with the
    circular exchange when first accessed.
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
    # Circular Exchange Framework - Core
    'CircularExchange',
    'DependencyRegistry', 
    'VariablePackage',
    'PackageRegistry',
    'ChangeNotifier',
    'ChangeType',
    # Circular Exchange Framework - Configuration Hub
    'PROJECT_CONFIG',
    'ProjectConfiguration',
    'ModuleRegistration',
    'SecurityPolicy',
    'CodingStandards',
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
    # Centralized logging
    'get_module_logger',
    'log_errors',
    'logging_context',
    'set_context',
    'clear_context',
    'ErrorHandler',
]

__version__ = '2.0.0'
__author__ = 'Enterprise Architecture Team'
