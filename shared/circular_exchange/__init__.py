"""
=============================================================================
CIRCULAR INFORMATION EXCHANGE FRAMEWORK - Enterprise Core
=============================================================================

This framework implements a sophisticated dependency tracking and change
propagation system inspired by reactive programming patterns used in
mission-critical systems at top-tier technology companies.

Architecture Overview:
┌─────────────────────────────────────────────────────────────────────────┐
│                    Circular Information Exchange                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │ DependencyRegistry│◄──►│  ChangeNotifier  │◄──►│  VariablePackage │  │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘  │
│           │                       │                        │            │
│           └───────────────────────┼────────────────────────┘            │
│                                   │                                      │
│                    ┌──────────────┴──────────────┐                      │
│                    │      CircularExchange        │                      │
│                    │    (Central Orchestrator)    │                      │
│                    └─────────────────────────────┘                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Key Components:
- DependencyRegistry: Tracks module dependencies in a bidirectional graph
- VariablePackage: Observable data containers with change notifications
- ChangeNotifier: Event-driven change propagation system
- CircularExchange: Central orchestrator combining all components

Design Patterns Implemented:
- Observer Pattern: Reactive change notifications
- Mediator Pattern: Centralized coordination
- Registry Pattern: Dependency management
- Event Sourcing: Change history tracking

Use Cases:
1. Automatic dependency resolution during file updates
2. Reactive data flow between modules
3. Circular dependency detection and handling
4. Project-wide impact analysis for code changes

Example Usage:
    from shared.circular_exchange import CircularExchange, VariablePackage
    
    # Initialize the exchange
    exchange = CircularExchange.get_instance(project_root='/path/to/project')
    
    # Register modules
    exchange.register_module('config', 'config.py')
    exchange.register_module('processor', 'processor.py')
    exchange.add_dependency('processor', 'config')
    
    # Create reactive data packages
    config = exchange.create_package('app_config', initial_value={'debug': True})
    
    # Subscribe to changes
    config.subscribe(lambda change: print(f'Config changed: {change}'))
    
    # Updates automatically propagate
    config.value = {'debug': False}

Thread Safety:
    All components are thread-safe and can be used in concurrent environments.

Performance:
    Optimized for high-throughput scenarios with batching and caching.

=============================================================================
"""

from .dependency_registry import (
    DependencyRegistry,
    ModuleInfo
)
from .variable_package import (
    VariablePackage,
    PackageRegistry,
    PackageChange
)
from .change_notifier import (
    ChangeNotifier,
    ChangeType,
    ChangeEvent,
    NotificationResult
)
from .circular_exchange import (
    CircularExchange,
    ModuleExport,
    ModuleImport
)

__all__ = [
    # Core Registry
    'DependencyRegistry',
    'ModuleInfo',
    # Variable Packages
    'VariablePackage',
    'PackageRegistry',
    'PackageChange',
    # Change Notification
    'ChangeNotifier',
    'ChangeType',
    'ChangeEvent',
    'NotificationResult',
    # Main Orchestrator
    'CircularExchange',
    'ModuleExport',
    'ModuleImport'
]

__version__ = '2.0.0'
__author__ = 'Enterprise Architecture Team'
