"""
Circular Exchange Framework (CEF) with CEFR Integration
=========================================================

Connects all modules through a shared dependency graph.
All code must integrate with this framework.
"""

# Core components
from .core.dependency_registry import DependencyRegistry, ModuleInfo
from .core.variable_package import VariablePackage, PackageRegistry, PackageChange
from .core.change_notifier import ChangeNotifier, ChangeType, ChangeEvent, NotificationResult
from .core.circular_exchange import CircularExchange, ModuleExport, ModuleImport
from .core.project_config import (
    PROJECT_CONFIG, ProjectConfiguration, ModuleRegistration,
    SecurityPolicy, CodingStandards, GraphNode, GraphEdge, PropagationMode
)
from .core.module_container import (
    CONTAINER_ORCHESTRATOR, ContainerOrchestrator, ModuleContainer,
    ContainerPort, ContainerDependency, ContainerStatus,
    CompatibilityLevel, CompatibilityReport,
    create_container, check_compatibility, standardize_code
)

# Analysis components
from .analysis.data_collector import (
    DATA_COLLECTOR, DataCollector, DataCategory, TestStatus,
    TestResult, LogEntry, MetricsSnapshot, ExtractionEvent, RefactorSuggestion
)
from .analysis.metrics_analyzer import (
    METRICS_ANALYZER, MetricsAnalyzer, Pattern, PatternType,
    Insight, InsightPriority, RefactorCategory, PerformanceBottleneck,
    TestHealthReport, ModelPerformanceReport
)
from .analysis.intelligent_analyzer import (
    INTELLIGENT_ANALYZER, IntelligentAnalyzer, PatternClusterer,
    AnomalyDetector, TrendAnalyzer, CodeEmbeddings, PatternCluster,
    Anomaly, TrendAnalysis, CodeSimilarity, AnomalyType, TrendDirection, ClusterQuality
)

# Refactoring components
from .refactor.refactoring_engine import (
    REFACTORING_ENGINE, RefactoringEngine, CodeSuggestion, RefactoringPlan,
    SuggestionType, ImpactLevel, EffortLevel, CodeLocation
)
from .refactor.autonomous_refactor import (
    AutonomousRefactor, RefactorRisk, RefactorStatus, RefactorResult,
    ABTest, ABTestVariant, ABTestResult, ABTestManager,
    RollbackManager, RollbackTrigger, RollbackAction,
    CodeTransformer, PRGenerator, get_autonomous_refactor
)
from .refactor.feedback_loop import (
    FEEDBACK_LOOP, FeedbackLoop, AutoTuner, ModelTrainingPipeline,
    TuningDecision, TrainingJob, TuningAction, FeedbackType, TrainingStatus
)

# Persistence components
from .persist.persistence import PERSISTENCE_LAYER, PersistenceLayer, DBConfig, ConnectionPool
from .persist.webhook_notifier import (
    WEBHOOK_NOTIFIER, WebhookNotifier, NotificationConfig,
    NotificationLevel, NotificationChannel, Notification
)

# CEFR aliases (CEF Refactoring)
CEFR = REFACTORING_ENGINE
CEFRefactoringEngine = RefactoringEngine
CEFRSuggestion = CodeSuggestion
CEFRPlan = RefactoringPlan
CEFRSuggestionType = SuggestionType
CEFRImpactLevel = ImpactLevel
CEFREffortLevel = EffortLevel
CEFRCodeLocation = CodeLocation
CEFRAutonomous = AutonomousRefactor
get_cefr_autonomous = get_autonomous_refactor

__all__ = [
    # Core
    'DependencyRegistry', 'ModuleInfo', 'VariablePackage', 'PackageRegistry', 'PackageChange',
    'ChangeNotifier', 'ChangeType', 'ChangeEvent', 'NotificationResult',
    'CircularExchange', 'ModuleExport', 'ModuleImport',
    'PROJECT_CONFIG', 'ProjectConfiguration', 'ModuleRegistration',
    'SecurityPolicy', 'CodingStandards', 'GraphNode', 'GraphEdge', 'PropagationMode',
    'CONTAINER_ORCHESTRATOR', 'ContainerOrchestrator', 'ModuleContainer',
    'ContainerPort', 'ContainerDependency', 'ContainerStatus',
    'CompatibilityLevel', 'CompatibilityReport',
    'create_container', 'check_compatibility', 'standardize_code',
    # Analysis
    'DATA_COLLECTOR', 'DataCollector', 'DataCategory', 'TestStatus',
    'TestResult', 'LogEntry', 'MetricsSnapshot', 'ExtractionEvent', 'RefactorSuggestion',
    'METRICS_ANALYZER', 'MetricsAnalyzer', 'Pattern', 'PatternType',
    'Insight', 'InsightPriority', 'RefactorCategory', 'PerformanceBottleneck',
    'TestHealthReport', 'ModelPerformanceReport',
    'INTELLIGENT_ANALYZER', 'IntelligentAnalyzer', 'PatternClusterer',
    'AnomalyDetector', 'TrendAnalyzer', 'CodeEmbeddings', 'PatternCluster',
    'Anomaly', 'TrendAnalysis', 'CodeSimilarity', 'AnomalyType', 'TrendDirection', 'ClusterQuality',
    # Refactoring
    'REFACTORING_ENGINE', 'RefactoringEngine', 'CodeSuggestion', 'RefactoringPlan',
    'SuggestionType', 'ImpactLevel', 'EffortLevel', 'CodeLocation',
    'AutonomousRefactor', 'RefactorRisk', 'RefactorStatus', 'RefactorResult',
    'ABTest', 'ABTestVariant', 'ABTestResult', 'ABTestManager',
    'RollbackManager', 'RollbackTrigger', 'RollbackAction',
    'CodeTransformer', 'PRGenerator', 'get_autonomous_refactor',
    'FEEDBACK_LOOP', 'FeedbackLoop', 'AutoTuner', 'ModelTrainingPipeline',
    'TuningDecision', 'TrainingJob', 'TuningAction', 'FeedbackType', 'TrainingStatus',
    # Persistence
    'PERSISTENCE_LAYER', 'PersistenceLayer', 'DBConfig', 'ConnectionPool',
    'WEBHOOK_NOTIFIER', 'WebhookNotifier', 'NotificationConfig',
    'NotificationLevel', 'NotificationChannel', 'Notification',
    # CEFR aliases
    'CEFR', 'CEFRefactoringEngine', 'CEFRSuggestion', 'CEFRPlan',
    'CEFRSuggestionType', 'CEFRImpactLevel', 'CEFREffortLevel', 'CEFRCodeLocation',
    'CEFRAutonomous', 'get_cefr_autonomous',
]

__version__ = '3.1.0'
