"""
Circular Exchange Framework
============================

Connects all modules in this project through a shared dependency graph.
When you change PROJECT_CONFIG, every connected module updates automatically.

Quick Start:
    from shared.circular_exchange import PROJECT_CONFIG
    
    # Read config
    debug = PROJECT_CONFIG.debug.value
    
    # Subscribe to changes
    PROJECT_CONFIG.debug.subscribe(lambda c: print(f"Debug changed to {c.new_value}"))

How files connect:
    
    PROJECT_CONFIG (central hub, affects everything)
         │
         ├── shared/models/ (OCR and AI processors)
         ├── shared/utils/ (data structures, logging, errors)  
         ├── shared/config/ (settings)
         └── web-app/backend/ (Flask API)

Each file registers itself:
    PROJECT_CONFIG.register_module(ModuleRegistration(
        module_id="my.module",
        file_path="path/to/file.py",
        dependencies=["shared.utils"],
        exports=["MyClass"]
    ))

The graph tracks which files import which, so changes propagate correctly.
Files with higher "degree" can access more modules. PROJECT_CONFIG has
infinite degree - it reaches everything.

See project_config.py for the weighted graph implementation.
See module_container.py for Docker-like isolation between modules.
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
from .project_config import (
    PROJECT_CONFIG,
    ProjectConfiguration,
    ModuleRegistration,
    SecurityPolicy,
    CodingStandards,
    GraphNode,
    GraphEdge,
    PropagationMode
)
from .module_container import (
    CONTAINER_ORCHESTRATOR,
    ContainerOrchestrator,
    ModuleContainer,
    ContainerPort,
    ContainerDependency,
    ContainerStatus,
    CompatibilityLevel,
    CompatibilityReport,
    create_container,
    check_compatibility,
    standardize_code
)
from .data_collector import (
    DATA_COLLECTOR,
    DataCollector,
    DataCategory,
    TestStatus,
    TestResult,
    LogEntry,
    MetricsSnapshot,
    ExtractionEvent,
    RefactorSuggestion
)

__all__ = [
    # Core
    'DependencyRegistry',
    'ModuleInfo',
    'VariablePackage',
    'PackageRegistry',
    'PackageChange',
    'ChangeNotifier',
    'ChangeType',
    'ChangeEvent',
    'NotificationResult',
    'CircularExchange',
    'ModuleExport',
    'ModuleImport',
    # Config
    'PROJECT_CONFIG',
    'ProjectConfiguration',
    'ModuleRegistration',
    'SecurityPolicy',
    'CodingStandards',
    # Graph
    'GraphNode',
    'GraphEdge',
    'PropagationMode',
    # Containers
    'CONTAINER_ORCHESTRATOR',
    'ContainerOrchestrator',
    'ModuleContainer',
    'ContainerPort',
    'ContainerDependency',
    'ContainerStatus',
    'CompatibilityLevel',
    'CompatibilityReport',
    'create_container',
    'check_compatibility',
    'standardize_code',
    # Data Collection (for continuous improvement)
    'DATA_COLLECTOR',
    'DataCollector',
    'DataCategory',
    'TestStatus',
    'TestResult',
    'LogEntry',
    'MetricsSnapshot',
    'ExtractionEvent',
    'RefactorSuggestion',
]

__version__ = '2.0.0'
