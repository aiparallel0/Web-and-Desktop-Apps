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
from .metrics_analyzer import (
    METRICS_ANALYZER,
    MetricsAnalyzer,
    Pattern,
    PatternType,
    Insight,
    InsightPriority,
    RefactorCategory,
    PerformanceBottleneck,
    TestHealthReport,
    ModelPerformanceReport
)
from .refactoring_engine import (
    REFACTORING_ENGINE,
    RefactoringEngine,
    CodeSuggestion,
    RefactoringPlan,
    SuggestionType,
    ImpactLevel,
    EffortLevel,
    CodeLocation
)
from .feedback_loop import (
    FEEDBACK_LOOP,
    FeedbackLoop,
    AutoTuner,
    ModelTrainingPipeline,
    TuningDecision,
    TrainingJob,
    TuningAction,
    FeedbackType,
    TrainingStatus
)
from .webhook_notifier import (
    WEBHOOK_NOTIFIER,
    WebhookNotifier,
    NotificationConfig,
    NotificationLevel,
    NotificationChannel,
    Notification
)
from .persistence import (
    PERSISTENCE_LAYER,
    PersistenceLayer,
    DBConfig,
    ConnectionPool
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
    # Metrics Analysis (for pattern detection and insights)
    'METRICS_ANALYZER',
    'MetricsAnalyzer',
    'Pattern',
    'PatternType',
    'Insight',
    'InsightPriority',
    'RefactorCategory',
    'PerformanceBottleneck',
    'TestHealthReport',
    'ModelPerformanceReport',
    # Refactoring Engine (for automated code improvement)
    'REFACTORING_ENGINE',
    'RefactoringEngine',
    'CodeSuggestion',
    'RefactoringPlan',
    'SuggestionType',
    'ImpactLevel',
    'EffortLevel',
    'CodeLocation',
    # Feedback Loop (for continuous auto-tuning and model fine-tuning)
    'FEEDBACK_LOOP',
    'FeedbackLoop',
    'AutoTuner',
    'ModelTrainingPipeline',
    'TuningDecision',
    'TrainingJob',
    'TuningAction',
    'FeedbackType',
    'TrainingStatus',
    # Webhook Notifications (for real-time alerts)
    'WEBHOOK_NOTIFIER',
    'WebhookNotifier',
    'NotificationConfig',
    'NotificationLevel',
    'NotificationChannel',
    'Notification',
    # Persistence Layer (for data storage)
    'PERSISTENCE_LAYER',
    'PersistenceLayer',
    'DBConfig',
    'ConnectionPool',
]

__version__ = '2.1.0'
