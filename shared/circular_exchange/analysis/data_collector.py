"""
=============================================================================
DATA COLLECTOR - Centralized Data Collection for Continuous Improvement
=============================================================================

This module implements a centralized data collection system that captures:
- Test results and metrics
- User interaction logs
- System performance data
- Error patterns and recovery information

The collected data feeds into:
1. Real-time system monitoring
2. Automated code quality analysis
3. Model fine-tuning datasets
4. Continuous refactoring recommendations

Circular Exchange Framework Integration:
-----------------------------------------
Module ID: shared.circular_exchange.data_collector
Description: Centralized data collection for tests, logs, and continuous improvement
Dependencies: [shared.circular_exchange.variable_package, shared.circular_exchange.change_notifier]
Exports: [DataCollector, ExecutionResult, ExecutionStatus, LogEntry, MetricsSnapshot, DATA_COLLECTOR]

=============================================================================
"""

import logging
import threading
import json
import os
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class DataCategory(Enum):
    """Categories of data being collected."""
    TEST_RESULT = "test_result"
    USER_LOG = "user_log"
    SYSTEM_METRIC = "system_metric"
    ERROR_EVENT = "error_event"
    EXTRACTION_RESULT = "extraction_result"
    MODEL_PERFORMANCE = "model_performance"
    CODE_QUALITY = "code_quality"
    REFACTOR_SUGGESTION = "refactor_suggestion"


class ExecutionStatus(Enum):
    """Status of a test execution."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


# Backward compatibility aliases (deprecated, use ExecutionStatus/ExecutionResult)
TestStatus = ExecutionStatus


@dataclass
class ExecutionResult:
    """Represents a test execution result."""
    test_id: str
    test_name: str
    module_path: str
    status: ExecutionStatus
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    assertions: int = 0
    coverage_lines: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


# Backward compatibility alias (deprecated, use ExecutionResult)
TestResult = ExecutionResult


@dataclass
class LogEntry:
    """Represents a log entry for analysis."""
    log_id: str
    level: str
    message: str
    module: str
    function: str
    line_number: int
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    exception_info: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class MetricsSnapshot:
    """Represents a point-in-time metrics snapshot."""
    snapshot_id: str
    category: DataCategory
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['category'] = self.category.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class ExtractionEvent:
    """Represents an OCR/AI extraction event for model fine-tuning."""
    event_id: str
    model_id: str
    image_path: str
    success: bool
    processing_time_ms: float
    confidence_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    ground_truth: Optional[Dict[str, Any]] = None  # For labeled data
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class RefactorSuggestion:
    """Represents a code refactoring suggestion based on collected data."""
    suggestion_id: str
    file_path: str
    category: str  # performance, readability, security, etc.
    priority: int  # 1-10, higher = more important
    description: str
    suggested_change: str
    evidence: List[str] = field(default_factory=list)  # Supporting data points
    timestamp: datetime = field(default_factory=datetime.now)
    auto_fixable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class DataCollector:
    """
    Centralized data collection hub for the Circular Exchange Framework.
    
    This singleton collects and stores:
    - Test results for quality tracking
    - Log entries for pattern analysis
    - System metrics for performance monitoring
    - Extraction events for model fine-tuning
    - Refactoring suggestions for continuous improvement
    
    The data is stored in structured format and can be exported
    for model training, analysis, or reporting.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global data collection."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the data collector."""
        if self._initialized:
            return
        
        self._lock = threading.RLock()
        
        # Data stores
        self._test_results: List[ExecutionResult] = []
        self._log_entries: List[LogEntry] = []
        self._metrics_snapshots: List[MetricsSnapshot] = []
        self._extraction_events: List[ExtractionEvent] = []
        self._refactor_suggestions: List[RefactorSuggestion] = []
        
        # Configuration
        self._max_items_per_category = int(os.getenv('DATA_COLLECTOR_MAX_ITEMS', 10000))
        self._data_dir = Path(os.getenv('DATA_COLLECTOR_DIR', 'data/collected'))
        self._auto_persist = os.getenv('DATA_COLLECTOR_AUTO_PERSIST', 'true').lower() == 'true'
        self._persist_threshold = int(os.getenv('DATA_COLLECTOR_PERSIST_THRESHOLD', 1000))
        
        # Subscribers for real-time data notifications
        self._subscribers: Dict[DataCategory, List[Callable]] = {
            category: [] for category in DataCategory
        }
        
        # Statistics
        self._stats = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'total_logs': 0,
            'error_logs': 0,
            'total_extractions': 0,
            'successful_extractions': 0,
        }
        
        # Ensure data directory exists
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        self._initialized = True
        logger.info("DataCollector initialized with data_dir=%s", self._data_dir)
    
    # =========================================================================
    # TEST RESULT COLLECTION
    # =========================================================================
    
    def record_test_result(self, result: ExecutionResult) -> None:
        """
        Record a test execution result.
        
        Args:
            result: ExecutionResult object containing test execution data
        """
        with self._lock:
            self._test_results.append(result)
            self._stats['total_tests'] += 1
            
            if result.status == ExecutionStatus.PASSED:
                self._stats['passed_tests'] += 1
            elif result.status == ExecutionStatus.FAILED:
                self._stats['failed_tests'] += 1
            
            # Trim if over limit
            if len(self._test_results) > self._max_items_per_category:
                self._test_results = self._test_results[-self._max_items_per_category:]
            
            # Auto-persist if threshold reached
            if self._auto_persist and len(self._test_results) >= self._persist_threshold:
                self._persist_data(DataCategory.TEST_RESULT)
            
            # Notify subscribers
            self._notify_subscribers(DataCategory.TEST_RESULT, result)
    
    def get_test_results(
        self,
        status: Optional[ExecutionStatus] = None,
        module_path: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ExecutionResult]:
        """
        Query test results with optional filters.
        
        Args:
            status: Filter by test status
            module_path: Filter by module path
            since: Filter by timestamp
            limit: Maximum number of results
            
        Returns:
            List of matching ExecutionResult objects
        """
        with self._lock:
            results = self._test_results.copy()
        
        if status:
            results = [r for r in results if r.status == status]
        if module_path:
            results = [r for r in results if module_path in r.module_path]
        if since:
            results = [r for r in results if r.timestamp >= since]
        
        return results[-limit:]
    
    # =========================================================================
    # LOG ENTRY COLLECTION
    # =========================================================================
    
    def record_log_entry(self, entry: LogEntry) -> None:
        """
        Record a log entry for analysis.
        
        Args:
            entry: LogEntry object containing log data
        """
        with self._lock:
            self._log_entries.append(entry)
            self._stats['total_logs'] += 1
            
            if entry.level in ('ERROR', 'CRITICAL'):
                self._stats['error_logs'] += 1
            
            # Trim if over limit
            if len(self._log_entries) > self._max_items_per_category:
                self._log_entries = self._log_entries[-self._max_items_per_category:]
            
            # Auto-persist if threshold reached
            if self._auto_persist and len(self._log_entries) >= self._persist_threshold:
                self._persist_data(DataCategory.USER_LOG)
            
            # Notify subscribers
            self._notify_subscribers(DataCategory.USER_LOG, entry)
    
    def get_log_entries(
        self,
        level: Optional[str] = None,
        module: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[LogEntry]:
        """
        Query log entries with optional filters.
        
        Args:
            level: Filter by log level
            module: Filter by module name
            since: Filter by timestamp
            limit: Maximum number of results
            
        Returns:
            List of matching LogEntry objects
        """
        with self._lock:
            entries = self._log_entries.copy()
        
        if level:
            entries = [e for e in entries if e.level == level]
        if module:
            entries = [e for e in entries if module in e.module]
        if since:
            entries = [e for e in entries if e.timestamp >= since]
        
        return entries[-limit:]
    
    # =========================================================================
    # EXTRACTION EVENT COLLECTION (FOR MODEL FINE-TUNING)
    # =========================================================================
    
    def record_extraction_event(self, event: ExtractionEvent) -> None:
        """
        Record an extraction event for model fine-tuning.
        
        Args:
            event: ExtractionEvent object containing extraction data
        """
        with self._lock:
            self._extraction_events.append(event)
            self._stats['total_extractions'] += 1
            
            if event.success:
                self._stats['successful_extractions'] += 1
            
            # Trim if over limit
            if len(self._extraction_events) > self._max_items_per_category:
                self._extraction_events = self._extraction_events[-self._max_items_per_category:]
            
            # Auto-persist if threshold reached
            if self._auto_persist and len(self._extraction_events) >= self._persist_threshold:
                self._persist_data(DataCategory.EXTRACTION_RESULT)
            
            # Notify subscribers
            self._notify_subscribers(DataCategory.EXTRACTION_RESULT, event)
    
    def get_extraction_events(
        self,
        model_id: Optional[str] = None,
        success: Optional[bool] = None,
        min_confidence: Optional[float] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ExtractionEvent]:
        """
        Query extraction events with optional filters.
        
        Args:
            model_id: Filter by model ID
            success: Filter by success status
            min_confidence: Filter by minimum confidence score
            since: Filter by timestamp
            limit: Maximum number of results
            
        Returns:
            List of matching ExtractionEvent objects
        """
        with self._lock:
            events = self._extraction_events.copy()
        
        if model_id:
            events = [e for e in events if e.model_id == model_id]
        if success is not None:
            events = [e for e in events if e.success == success]
        if min_confidence is not None:
            events = [e for e in events if e.confidence_score >= min_confidence]
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        return events[-limit:]
    
    def export_training_data(self, output_path: Optional[Path] = None) -> Path:
        """
        Export extraction events as a training dataset for model fine-tuning.
        
        Args:
            output_path: Optional path for the output file
            
        Returns:
            Path to the exported training data file
        """
        if output_path is None:
            output_path = self._data_dir / f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        with self._lock:
            events = self._extraction_events.copy()
        
        with open(output_path, 'w') as f:
            for event in events:
                # Only include events with ground truth for supervised learning
                if event.ground_truth:
                    training_sample = {
                        'input': {
                            'image_path': event.image_path,
                            'model_id': event.model_id,
                        },
                        'output': event.ground_truth,
                        'metadata': {
                            'confidence': event.confidence_score,
                            'processing_time_ms': event.processing_time_ms,
                            'timestamp': event.timestamp.isoformat(),
                        }
                    }
                    f.write(json.dumps(training_sample) + '\n')
        
        logger.info("Exported training data to %s", output_path)
        return output_path
    
    # =========================================================================
    # REFACTORING SUGGESTIONS
    # =========================================================================
    
    def record_refactor_suggestion(self, suggestion: RefactorSuggestion) -> None:
        """
        Record a refactoring suggestion based on collected data analysis.
        
        Args:
            suggestion: RefactorSuggestion object
        """
        with self._lock:
            self._refactor_suggestions.append(suggestion)
            
            # Notify subscribers
            self._notify_subscribers(DataCategory.REFACTOR_SUGGESTION, suggestion)
    
    def get_refactor_suggestions(
        self,
        file_path: Optional[str] = None,
        category: Optional[str] = None,
        min_priority: int = 1,
        limit: int = 100
    ) -> List[RefactorSuggestion]:
        """
        Query refactoring suggestions with optional filters.
        
        Args:
            file_path: Filter by file path
            category: Filter by suggestion category
            min_priority: Minimum priority (1-10)
            limit: Maximum number of results
            
        Returns:
            List of matching RefactorSuggestion objects
        """
        with self._lock:
            suggestions = self._refactor_suggestions.copy()
        
        if file_path:
            suggestions = [s for s in suggestions if file_path in s.file_path]
        if category:
            suggestions = [s for s in suggestions if s.category == category]
        
        suggestions = [s for s in suggestions if s.priority >= min_priority]
        
        # Sort by priority (descending)
        suggestions.sort(key=lambda s: s.priority, reverse=True)
        
        return suggestions[:limit]
    
    # =========================================================================
    # METRICS AND STATISTICS
    # =========================================================================
    
    def record_metrics_snapshot(self, snapshot: MetricsSnapshot) -> None:
        """
        Record a metrics snapshot.
        
        Args:
            snapshot: MetricsSnapshot object
        """
        with self._lock:
            self._metrics_snapshots.append(snapshot)
            
            # Trim if over limit
            if len(self._metrics_snapshots) > self._max_items_per_category:
                self._metrics_snapshots = self._metrics_snapshots[-self._max_items_per_category:]
            
            # Notify subscribers
            self._notify_subscribers(DataCategory.SYSTEM_METRIC, snapshot)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current statistics summary.
        
        Returns:
            Dictionary of statistics
        """
        with self._lock:
            stats = self._stats.copy()
            
            # Add calculated metrics
            if stats['total_tests'] > 0:
                stats['test_pass_rate'] = stats['passed_tests'] / stats['total_tests']
            else:
                stats['test_pass_rate'] = 0.0
            
            if stats['total_extractions'] > 0:
                stats['extraction_success_rate'] = stats['successful_extractions'] / stats['total_extractions']
            else:
                stats['extraction_success_rate'] = 0.0
            
            # Add item counts
            stats['stored_test_results'] = len(self._test_results)
            stats['stored_log_entries'] = len(self._log_entries)
            stats['stored_extraction_events'] = len(self._extraction_events)
            stats['stored_refactor_suggestions'] = len(self._refactor_suggestions)
            
            return stats
    
    # =========================================================================
    # SUBSCRIPTION MANAGEMENT
    # =========================================================================
    
    def subscribe(self, category: DataCategory, callback: Callable) -> None:
        """
        Subscribe to data updates for a specific category.
        
        Args:
            category: DataCategory to subscribe to
            callback: Function to call when new data is recorded
        """
        with self._lock:
            if callback not in self._subscribers[category]:
                self._subscribers[category].append(callback)
    
    def unsubscribe(self, category: DataCategory, callback: Callable) -> None:
        """
        Unsubscribe from data updates.
        
        Args:
            category: DataCategory to unsubscribe from
            callback: Function to remove
        """
        with self._lock:
            if callback in self._subscribers[category]:
                self._subscribers[category].remove(callback)
    
    def _notify_subscribers(self, category: DataCategory, data: Any) -> None:
        """Notify all subscribers of new data."""
        with self._lock:
            subscribers = self._subscribers[category].copy()
        
        for callback in subscribers:
            try:
                callback(data)
            except Exception as e:
                logger.error("Error notifying subscriber: %s", e)
    
    # =========================================================================
    # PERSISTENCE
    # =========================================================================
    
    def _persist_data(self, category: DataCategory) -> None:
        """Persist data of a specific category to disk."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if category == DataCategory.TEST_RESULT:
                data = [r.to_dict() for r in self._test_results]
                file_path = self._data_dir / f"test_results_{timestamp}.json"
            elif category == DataCategory.USER_LOG:
                data = [e.to_dict() for e in self._log_entries]
                file_path = self._data_dir / f"log_entries_{timestamp}.json"
            elif category == DataCategory.EXTRACTION_RESULT:
                data = [e.to_dict() for e in self._extraction_events]
                file_path = self._data_dir / f"extraction_events_{timestamp}.json"
            else:
                return
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Persisted %d items to %s", len(data), file_path)
            
        except Exception as e:
            logger.error("Error persisting data: %s", e)
    
    def persist_all(self) -> None:
        """Persist all collected data to disk."""
        for category in [DataCategory.TEST_RESULT, DataCategory.USER_LOG, DataCategory.EXTRACTION_RESULT]:
            self._persist_data(category)
    
    def clear(self, category: Optional[DataCategory] = None) -> None:
        """
        Clear collected data.
        
        Args:
            category: Optional specific category to clear, or all if None
        """
        with self._lock:
            if category is None or category == DataCategory.TEST_RESULT:
                self._test_results.clear()
            if category is None or category == DataCategory.USER_LOG:
                self._log_entries.clear()
            if category is None or category == DataCategory.EXTRACTION_RESULT:
                self._extraction_events.clear()
            if category is None or category == DataCategory.REFACTOR_SUGGESTION:
                self._refactor_suggestions.clear()
            if category is None:
                self._stats = {
                    'total_tests': 0,
                    'passed_tests': 0,
                    'failed_tests': 0,
                    'total_logs': 0,
                    'error_logs': 0,
                    'total_extractions': 0,
                    'successful_extractions': 0,
                }


# Global singleton instance
DATA_COLLECTOR = DataCollector()


# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.circular_exchange.data_collector",
            file_path=__file__,
            description="Centralized data collection for tests, logs, and continuous improvement",
            dependencies=["shared.circular_exchange.variable_package", "shared.circular_exchange.change_notifier"],
            exports=["DataCollector", "ExecutionResult", "ExecutionStatus", "LogEntry", "MetricsSnapshot", 
                    "ExtractionEvent", "RefactorSuggestion", "DATA_COLLECTOR", "DataCategory",
                    "TestResult", "TestStatus"]  # Include backward compatibility aliases
        ))
    except Exception:
        pass  # Ignore registration errors during import
