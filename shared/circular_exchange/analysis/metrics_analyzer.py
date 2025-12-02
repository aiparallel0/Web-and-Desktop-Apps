"""
=============================================================================
METRICS ANALYZER - Pattern Detection and Insights for Continuous Improvement
=============================================================================

This module implements pattern detection and analysis from collected data:
- Identifies recurring error patterns
- Detects performance bottlenecks
- Analyzes test failure patterns
- Generates insights for code refactoring
- Prepares data for model fine-tuning

Circular Exchange Framework Integration:
-----------------------------------------
Module ID: shared.circular_exchange.metrics_analyzer
Description: Pattern detection and metrics analysis for continuous improvement
Dependencies: [shared.circular_exchange.data_collector, shared.circular_exchange.variable_package]
Exports: [MetricsAnalyzer, Pattern, Insight, PerformanceBottleneck, METRICS_ANALYZER]

=============================================================================
"""

import logging
import threading
import re
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns detected in the data."""
    ERROR_RECURRING = "error_recurring"
    TEST_FLAKY = "test_flaky"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    LOG_ANOMALY = "log_anomaly"
    EXTRACTION_FAILURE = "extraction_failure"
    CODE_SMELL = "code_smell"
    HOT_PATH = "hot_path"  # Frequently executed code paths


class InsightPriority(Enum):
    """Priority levels for insights."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


class RefactorCategory(Enum):
    """Categories of refactoring suggestions."""
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    READABILITY = "readability"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    TESTABILITY = "testability"


@dataclass
class Pattern:
    """Represents a detected pattern in the data."""
    pattern_id: str
    pattern_type: PatternType
    description: str
    occurrences: int
    first_seen: datetime
    last_seen: datetime
    affected_modules: List[str] = field(default_factory=list)
    affected_tests: List[str] = field(default_factory=list)
    sample_data: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['pattern_type'] = self.pattern_type.value
        data['first_seen'] = self.first_seen.isoformat()
        data['last_seen'] = self.last_seen.isoformat()
        return data


@dataclass
class Insight:
    """Represents an actionable insight derived from pattern analysis."""
    insight_id: str
    title: str
    description: str
    priority: InsightPriority
    category: RefactorCategory
    source_patterns: List[str] = field(default_factory=list)  # Pattern IDs
    recommended_actions: List[str] = field(default_factory=list)
    estimated_impact: str = ""  # Description of potential improvement
    auto_fixable: bool = False
    fix_suggestion: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['category'] = self.category.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class PerformanceBottleneck:
    """Represents a detected performance bottleneck."""
    bottleneck_id: str
    location: str  # File path or module
    function_name: str
    avg_duration_ms: float
    max_duration_ms: float
    call_count: int
    percentile_95_ms: float
    first_detected: datetime
    trend: str  # "improving", "stable", "degrading"
    suggested_optimization: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['first_detected'] = self.first_detected.isoformat()
        return data


@dataclass
class TestHealthReport:
    """Report on the health of the test suite."""
    report_id: str
    timestamp: datetime
    total_tests: int
    pass_rate: float
    avg_duration_ms: float
    flaky_tests: List[str] = field(default_factory=list)
    slow_tests: List[str] = field(default_factory=list)
    frequently_failing: List[str] = field(default_factory=list)
    coverage_trend: str = "stable"  # "improving", "stable", "declining"
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class ModelPerformanceReport:
    """Report on AI/OCR model performance for fine-tuning decisions."""
    report_id: str
    model_id: str
    timestamp: datetime
    total_extractions: int
    success_rate: float
    avg_confidence: float
    avg_processing_time_ms: float
    error_distribution: Dict[str, int] = field(default_factory=dict)
    low_confidence_patterns: List[str] = field(default_factory=list)
    recommended_training_focus: List[str] = field(default_factory=list)
    training_data_quality_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class MetricsAnalyzer:
    """
    Analyzes collected data to detect patterns and generate insights.
    
    This singleton analyzes:
    - Error patterns for reliability improvements
    - Performance data for bottleneck detection
    - Test results for test suite health
    - Extraction events for model fine-tuning decisions
    
    The analyzer produces:
    - Patterns: Recurring issues detected in the data
    - Insights: Actionable recommendations for improvement
    - Reports: Comprehensive analysis of specific areas
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global metrics analysis."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the metrics analyzer."""
        if self._initialized:
            return
        
        self._lock = threading.RLock()
        
        # Pattern storage
        self._patterns: Dict[str, Pattern] = {}
        self._insights: List[Insight] = []
        self._bottlenecks: Dict[str, PerformanceBottleneck] = {}
        
        # Analysis configuration
        self._error_pattern_threshold = 3  # Min occurrences to be a pattern
        self._flaky_test_threshold = 2  # Min failures to consider flaky
        self._slow_test_threshold_ms = 5000  # Tests slower than this are "slow"
        self._performance_sample_size = 100  # Samples for performance analysis
        
        # Subscribers for real-time notifications
        self._pattern_subscribers: List[callable] = []
        self._insight_subscribers: List[callable] = []
        
        # Reference to data collector
        self._data_collector = None
        
        self._initialized = True
        logger.info("MetricsAnalyzer initialized")
    
    def _get_data_collector(self):
        """Lazy-load the data collector to avoid circular imports."""
        if self._data_collector is None:
            try:
                from shared.circular_exchange.data_collector import DATA_COLLECTOR
                self._data_collector = DATA_COLLECTOR
            except ImportError:
                logger.warning("Could not import DATA_COLLECTOR")
        return self._data_collector
    
    # =========================================================================
    # ERROR PATTERN DETECTION
    # =========================================================================
    
    def analyze_error_patterns(self, time_window_hours: int = 24) -> List[Pattern]:
        """
        Analyze log entries to detect recurring error patterns.
        
        Args:
            time_window_hours: Time window to analyze
            
        Returns:
            List of detected error patterns
        """
        collector = self._get_data_collector()
        if collector is None:
            return []
        
        since = datetime.now() - timedelta(hours=time_window_hours)
        log_entries = collector.get_log_entries(level="ERROR", since=since, limit=1000)
        
        # Group errors by normalized message
        error_groups: Dict[str, List] = defaultdict(list)
        
        for entry in log_entries:
            # Normalize the error message (remove variable parts)
            normalized = self._normalize_error_message(entry.message)
            error_groups[normalized].append(entry)
        
        patterns = []
        for normalized_msg, entries in error_groups.items():
            if len(entries) >= self._error_pattern_threshold:
                pattern = Pattern(
                    pattern_id=f"error_{hash(normalized_msg) % 100000}",
                    pattern_type=PatternType.ERROR_RECURRING,
                    description=f"Recurring error: {normalized_msg[:100]}...",
                    occurrences=len(entries),
                    first_seen=min(e.timestamp for e in entries),
                    last_seen=max(e.timestamp for e in entries),
                    affected_modules=list(set(e.module for e in entries)),
                    sample_data=[e.to_dict() for e in entries[:5]],
                    confidence=min(len(entries) / 10.0, 1.0)
                )
                patterns.append(pattern)
                self._patterns[pattern.pattern_id] = pattern
        
        # Notify subscribers
        for pattern in patterns:
            self._notify_pattern_subscribers(pattern)
        
        logger.info("Detected %d error patterns", len(patterns))
        return patterns
    
    def _normalize_error_message(self, message: str) -> str:
        """Normalize an error message by removing variable parts."""
        # Remove timestamps
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', '<TIMESTAMP>', message)
        # Remove file paths
        normalized = re.sub(r'(/[a-zA-Z0-9_\-./]+)+', '<PATH>', normalized)
        # Remove numbers that look like IDs
        normalized = re.sub(r'\b[a-f0-9]{8,}\b', '<ID>', normalized)
        # Remove line numbers
        normalized = re.sub(r'line \d+', 'line <N>', normalized)
        return normalized
    
    # =========================================================================
    # TEST HEALTH ANALYSIS
    # =========================================================================
    
    def analyze_test_health(self, time_window_hours: int = 168) -> TestHealthReport:
        """
        Analyze test results to generate a health report.
        
        Args:
            time_window_hours: Time window to analyze (default: 1 week)
            
        Returns:
            TestHealthReport with analysis results
        """
        collector = self._get_data_collector()
        if collector is None:
            return TestHealthReport(
                report_id="empty",
                timestamp=datetime.now(),
                total_tests=0,
                pass_rate=0.0,
                avg_duration_ms=0.0
            )
        
        since = datetime.now() - timedelta(hours=time_window_hours)
        all_results = collector.get_test_results(since=since, limit=10000)
        
        if not all_results:
            return TestHealthReport(
                report_id=f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                total_tests=0,
                pass_rate=0.0,
                avg_duration_ms=0.0,
                recommendations=["No test data available for analysis"]
            )
        
        # Calculate basic metrics
        total_tests = len(all_results)
        passed_count = sum(1 for r in all_results if r.status.value == "passed")
        pass_rate = passed_count / total_tests if total_tests > 0 else 0.0
        avg_duration = statistics.mean(r.duration_ms for r in all_results) if all_results else 0.0
        
        # Detect flaky tests (tests that both pass and fail)
        test_outcomes: Dict[str, List[str]] = defaultdict(list)
        for result in all_results:
            test_outcomes[result.test_name].append(result.status.value)
        
        flaky_tests = [
            name for name, outcomes in test_outcomes.items()
            if len(set(outcomes)) > 1 and outcomes.count("failed") >= self._flaky_test_threshold
        ]
        
        # Detect slow tests
        slow_tests = list(set(
            r.test_name for r in all_results 
            if r.duration_ms > self._slow_test_threshold_ms
        ))
        
        # Detect frequently failing tests
        failure_counts = Counter(
            r.test_name for r in all_results 
            if r.status.value in ("failed", "error")
        )
        frequently_failing = [
            name for name, count in failure_counts.most_common(10) 
            if count >= 3
        ]
        
        # Generate recommendations
        recommendations = []
        if pass_rate < 0.9:
            recommendations.append(f"Test pass rate ({pass_rate:.1%}) is below 90%. Review failing tests.")
        if flaky_tests:
            recommendations.append(f"Found {len(flaky_tests)} flaky tests. Consider fixing or quarantining them.")
        if slow_tests:
            recommendations.append(f"Found {len(slow_tests)} slow tests (>{self._slow_test_threshold_ms}ms). Consider optimization.")
        if frequently_failing:
            recommendations.append(f"Found {len(frequently_failing)} frequently failing tests. Priority fix needed.")
        
        report = TestHealthReport(
            report_id=f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            total_tests=total_tests,
            pass_rate=pass_rate,
            avg_duration_ms=avg_duration,
            flaky_tests=flaky_tests[:10],
            slow_tests=slow_tests[:10],
            frequently_failing=frequently_failing[:10],
            recommendations=recommendations
        )
        
        # Generate insights from the report
        self._generate_test_insights(report)
        
        return report
    
    def _generate_test_insights(self, report: TestHealthReport) -> None:
        """Generate insights from a test health report."""
        if report.flaky_tests:
            insight = Insight(
                insight_id=f"insight_flaky_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                title="Flaky Tests Detected",
                description=f"Found {len(report.flaky_tests)} tests with inconsistent results.",
                priority=InsightPriority.HIGH,
                category=RefactorCategory.RELIABILITY,
                recommended_actions=[
                    "Review test isolation - ensure tests don't share state",
                    "Check for race conditions in async tests",
                    "Add explicit waits for asynchronous operations",
                    "Consider running flaky tests in isolation"
                ],
                estimated_impact="Improved CI reliability and developer confidence"
            )
            self._insights.append(insight)
            self._notify_insight_subscribers(insight)
        
        if report.pass_rate < 0.8:
            insight = Insight(
                insight_id=f"insight_passrate_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                title="Low Test Pass Rate",
                description=f"Test pass rate is {report.pass_rate:.1%}, below acceptable threshold.",
                priority=InsightPriority.CRITICAL,
                category=RefactorCategory.RELIABILITY,
                recommended_actions=[
                    "Prioritize fixing frequently failing tests",
                    "Review recent code changes for regressions",
                    "Consider reverting problematic commits"
                ],
                estimated_impact="Restored code quality and deployment confidence"
            )
            self._insights.append(insight)
            self._notify_insight_subscribers(insight)
    
    # =========================================================================
    # PERFORMANCE ANALYSIS
    # =========================================================================
    
    def analyze_performance(self, time_window_hours: int = 24) -> List[PerformanceBottleneck]:
        """
        Analyze extraction events to detect performance bottlenecks.
        
        Args:
            time_window_hours: Time window to analyze
            
        Returns:
            List of detected performance bottlenecks
        """
        collector = self._get_data_collector()
        if collector is None:
            return []
        
        since = datetime.now() - timedelta(hours=time_window_hours)
        events = collector.get_extraction_events(since=since, limit=1000)
        
        if not events:
            return []
        
        # Group by model
        model_events: Dict[str, List] = defaultdict(list)
        for event in events:
            model_events[event.model_id].append(event)
        
        bottlenecks = []
        for model_id, model_event_list in model_events.items():
            durations = [e.processing_time_ms for e in model_event_list]
            
            if len(durations) < 5:
                continue
            
            avg_duration = statistics.mean(durations)
            max_duration = max(durations)
            
            # Calculate 95th percentile
            sorted_durations = sorted(durations)
            p95_index = int(len(sorted_durations) * 0.95)
            p95_duration = sorted_durations[p95_index] if p95_index < len(sorted_durations) else max_duration
            
            # Detect if this is a bottleneck (p95 > 2x average)
            if p95_duration > avg_duration * 2 or avg_duration > 3000:
                bottleneck = PerformanceBottleneck(
                    bottleneck_id=f"perf_{model_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    location=f"models/{model_id}",
                    function_name="extract",
                    avg_duration_ms=avg_duration,
                    max_duration_ms=max_duration,
                    call_count=len(durations),
                    percentile_95_ms=p95_duration,
                    first_detected=min(e.timestamp for e in model_event_list),
                    trend="stable",  # Would need historical data for trend
                    suggested_optimization=self._suggest_optimization(model_id, avg_duration)
                )
                bottlenecks.append(bottleneck)
                self._bottlenecks[bottleneck.bottleneck_id] = bottleneck
        
        logger.info("Detected %d performance bottlenecks", len(bottlenecks))
        return bottlenecks
    
    def _suggest_optimization(self, model_id: str, avg_duration_ms: float) -> str:
        """Generate optimization suggestions based on model and performance."""
        suggestions = []
        
        if avg_duration_ms > 5000:
            suggestions.append("Consider using GPU acceleration")
            suggestions.append("Evaluate model quantization for faster inference")
        
        if "donut" in model_id.lower():
            suggestions.append("Consider image preprocessing to reduce input size")
        
        if "ocr" in model_id.lower():
            suggestions.append("Batch multiple images for efficiency")
        
        return "; ".join(suggestions) if suggestions else "Monitor for trends"
    
    # =========================================================================
    # MODEL PERFORMANCE ANALYSIS
    # =========================================================================
    
    def analyze_model_performance(self, model_id: Optional[str] = None) -> List[ModelPerformanceReport]:
        """
        Analyze extraction events to generate model performance reports.
        
        Args:
            model_id: Optional specific model to analyze
            
        Returns:
            List of model performance reports
        """
        collector = self._get_data_collector()
        if collector is None:
            return []
        
        events = collector.get_extraction_events(model_id=model_id, limit=10000)
        
        if not events:
            return []
        
        # Group by model
        model_events: Dict[str, List] = defaultdict(list)
        for event in events:
            model_events[event.model_id].append(event)
        
        reports = []
        for mid, model_event_list in model_events.items():
            if len(model_event_list) < 5:
                continue
            
            success_count = sum(1 for e in model_event_list if e.success)
            success_rate = success_count / len(model_event_list)
            
            avg_confidence = statistics.mean(e.confidence_score for e in model_event_list)
            avg_processing_time = statistics.mean(e.processing_time_ms for e in model_event_list)
            
            # Analyze error distribution
            error_types = Counter(e.error_type for e in model_event_list if e.error_type)
            
            # Identify low confidence patterns
            low_conf_events = [e for e in model_event_list if e.confidence_score < 0.5]
            low_conf_patterns = self._identify_low_confidence_patterns(low_conf_events)
            
            # Generate training recommendations
            training_focus = self._generate_training_recommendations(
                success_rate, avg_confidence, dict(error_types), low_conf_patterns
            )
            
            # Calculate training data quality score
            labeled_count = sum(1 for e in model_event_list if e.ground_truth is not None)
            quality_score = labeled_count / len(model_event_list) if model_event_list else 0.0
            
            report = ModelPerformanceReport(
                report_id=f"model_{mid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                model_id=mid,
                timestamp=datetime.now(),
                total_extractions=len(model_event_list),
                success_rate=success_rate,
                avg_confidence=avg_confidence,
                avg_processing_time_ms=avg_processing_time,
                error_distribution=dict(error_types),
                low_confidence_patterns=low_conf_patterns,
                recommended_training_focus=training_focus,
                training_data_quality_score=quality_score
            )
            reports.append(report)
            
            # Generate insights
            self._generate_model_insights(report)
        
        return reports
    
    def _identify_low_confidence_patterns(self, events: List) -> List[str]:
        """Identify patterns in low confidence extractions."""
        patterns = []
        
        if not events:
            return patterns
        
        # Check for common metadata patterns
        metadata_counter: Dict[str, int] = defaultdict(int)
        for event in events:
            for key, value in event.metadata.items():
                metadata_counter[f"{key}={value}"] += 1
        
        for pattern, count in metadata_counter.items():
            if count >= len(events) * 0.3:  # If pattern appears in 30%+ of low-conf events
                patterns.append(pattern)
        
        return patterns[:5]
    
    def _generate_training_recommendations(
        self,
        success_rate: float,
        avg_confidence: float,
        error_distribution: Dict[str, int],
        low_conf_patterns: List[str]
    ) -> List[str]:
        """Generate training focus recommendations."""
        recommendations = []
        
        if success_rate < 0.9:
            recommendations.append("Increase training data volume for better generalization")
        
        if avg_confidence < 0.7:
            recommendations.append("Add more diverse training examples")
        
        # Recommend based on common errors
        for error_type, count in sorted(error_distribution.items(), key=lambda x: -x[1])[:3]:
            if error_type:
                recommendations.append(f"Focus on reducing '{error_type}' errors")
        
        if low_conf_patterns:
            recommendations.append(f"Add training data for patterns: {', '.join(low_conf_patterns[:3])}")
        
        return recommendations
    
    def _generate_model_insights(self, report: ModelPerformanceReport) -> None:
        """Generate insights from model performance report."""
        if report.success_rate < 0.8:
            insight = Insight(
                insight_id=f"insight_model_{report.model_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                title=f"Low Success Rate for {report.model_id}",
                description=f"Model {report.model_id} has {report.success_rate:.1%} success rate.",
                priority=InsightPriority.HIGH,
                category=RefactorCategory.RELIABILITY,
                recommended_actions=report.recommended_training_focus,
                estimated_impact="Improved extraction accuracy and user satisfaction"
            )
            self._insights.append(insight)
            self._notify_insight_subscribers(insight)
        
        if report.training_data_quality_score < 0.5:
            insight = Insight(
                insight_id=f"insight_training_{report.model_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                title=f"Low Training Data Quality for {report.model_id}",
                description=f"Only {report.training_data_quality_score:.1%} of extractions have ground truth labels.",
                priority=InsightPriority.MEDIUM,
                category=RefactorCategory.MAINTAINABILITY,
                recommended_actions=[
                    "Implement user feedback collection for labeling",
                    "Add manual review workflow for low-confidence results",
                    "Consider active learning to prioritize labeling"
                ],
                estimated_impact="Better fine-tuning data for model improvement"
            )
            self._insights.append(insight)
            self._notify_insight_subscribers(insight)
    
    # =========================================================================
    # INSIGHT GENERATION
    # =========================================================================
    
    def generate_refactoring_insights(self) -> List[Insight]:
        """
        Generate comprehensive refactoring insights from all detected patterns.
        
        Returns:
            List of actionable insights
        """
        collector = self._get_data_collector()
        if collector is None:
            return []
        
        insights = []
        
        # Analyze error patterns
        error_patterns = self.analyze_error_patterns()
        for pattern in error_patterns:
            if pattern.occurrences >= 5:
                insight = Insight(
                    insight_id=f"insight_error_{pattern.pattern_id}",
                    title=f"Recurring Error Pattern Detected",
                    description=pattern.description,
                    priority=InsightPriority.HIGH if pattern.occurrences >= 10 else InsightPriority.MEDIUM,
                    category=RefactorCategory.RELIABILITY,
                    source_patterns=[pattern.pattern_id],
                    recommended_actions=[
                        f"Review error handling in modules: {', '.join(pattern.affected_modules[:3])}",
                        "Add targeted error handling or input validation",
                        "Consider adding retry logic for transient failures"
                    ],
                    estimated_impact=f"Reduce error occurrences by addressing root cause"
                )
                insights.append(insight)
        
        # Analyze performance
        bottlenecks = self.analyze_performance()
        for bottleneck in bottlenecks:
            insight = Insight(
                insight_id=f"insight_perf_{bottleneck.bottleneck_id}",
                title=f"Performance Bottleneck in {bottleneck.function_name}",
                description=f"Average processing time: {bottleneck.avg_duration_ms:.0f}ms, P95: {bottleneck.percentile_95_ms:.0f}ms",
                priority=InsightPriority.MEDIUM,
                category=RefactorCategory.PERFORMANCE,
                recommended_actions=[
                    bottleneck.suggested_optimization,
                    "Profile the function to identify slow operations",
                    "Consider caching frequently computed results"
                ],
                estimated_impact=f"Potential {(bottleneck.percentile_95_ms - bottleneck.avg_duration_ms)/bottleneck.avg_duration_ms*100:.0f}% reduction in worst-case latency"
            )
            insights.append(insight)
        
        # Store insights
        self._insights.extend(insights)
        
        return insights
    
    # =========================================================================
    # SUBSCRIPTION MANAGEMENT
    # =========================================================================
    
    def subscribe_to_patterns(self, callback: callable) -> None:
        """Subscribe to pattern detection notifications."""
        with self._lock:
            if callback not in self._pattern_subscribers:
                self._pattern_subscribers.append(callback)
    
    def subscribe_to_insights(self, callback: callable) -> None:
        """Subscribe to insight generation notifications."""
        with self._lock:
            if callback not in self._insight_subscribers:
                self._insight_subscribers.append(callback)
    
    def _notify_pattern_subscribers(self, pattern: Pattern) -> None:
        """Notify all pattern subscribers."""
        for callback in self._pattern_subscribers:
            try:
                callback(pattern)
            except Exception as e:
                logger.error("Error notifying pattern subscriber: %s", e)
    
    def _notify_insight_subscribers(self, insight: Insight) -> None:
        """Notify all insight subscribers."""
        for callback in self._insight_subscribers:
            try:
                callback(insight)
            except Exception as e:
                logger.error("Error notifying insight subscriber: %s", e)
    
    # =========================================================================
    # QUERY METHODS
    # =========================================================================
    
    def get_patterns(
        self,
        pattern_type: Optional[PatternType] = None,
        min_occurrences: int = 1
    ) -> List[Pattern]:
        """Get detected patterns with optional filtering."""
        with self._lock:
            patterns = list(self._patterns.values())
        
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        
        patterns = [p for p in patterns if p.occurrences >= min_occurrences]
        
        return sorted(patterns, key=lambda p: p.occurrences, reverse=True)
    
    def get_insights(
        self,
        priority: Optional[InsightPriority] = None,
        category: Optional[RefactorCategory] = None,
        limit: int = 50
    ) -> List[Insight]:
        """Get generated insights with optional filtering."""
        with self._lock:
            insights = self._insights.copy()
        
        if priority:
            insights = [i for i in insights if i.priority == priority]
        
        if category:
            insights = [i for i in insights if i.category == category]
        
        # Sort by priority (lower number = higher priority)
        insights.sort(key=lambda i: i.priority.value)
        
        return insights[:limit]
    
    def get_bottlenecks(self, limit: int = 20) -> List[PerformanceBottleneck]:
        """Get detected performance bottlenecks."""
        with self._lock:
            bottlenecks = list(self._bottlenecks.values())
        
        # Sort by average duration (slowest first)
        bottlenecks.sort(key=lambda b: b.avg_duration_ms, reverse=True)
        
        return bottlenecks[:limit]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all analysis results."""
        return {
            "total_patterns": len(self._patterns),
            "total_insights": len(self._insights),
            "total_bottlenecks": len(self._bottlenecks),
            "patterns_by_type": dict(Counter(p.pattern_type.value for p in self._patterns.values())),
            "insights_by_priority": dict(Counter(i.priority.value for i in self._insights)),
            "insights_by_category": dict(Counter(i.category.value for i in self._insights)),
        }
    
    def clear(self) -> None:
        """Clear all analysis results."""
        with self._lock:
            self._patterns.clear()
            self._insights.clear()
            self._bottlenecks.clear()


# Global singleton instance
METRICS_ANALYZER = MetricsAnalyzer()


# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.circular_exchange.metrics_analyzer",
            file_path=__file__,
            description="Pattern detection and metrics analysis for continuous improvement",
            dependencies=["shared.circular_exchange.data_collector", "shared.circular_exchange.variable_package"],
            exports=["MetricsAnalyzer", "Pattern", "Insight", "PerformanceBottleneck", 
                    "TestHealthReport", "ModelPerformanceReport", "METRICS_ANALYZER",
                    "PatternType", "InsightPriority", "RefactorCategory"]
        ))
    except Exception:
        pass  # Ignore registration errors during import
