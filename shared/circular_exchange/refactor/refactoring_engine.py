"""
=============================================================================
REFACTORING ENGINE - Automated Code Improvement Suggestions
=============================================================================

This module implements an automated refactoring suggestion engine that:
- Analyzes patterns from MetricsAnalyzer to generate code improvements
- Creates actionable refactoring suggestions with code examples
- Prioritizes suggestions based on impact and effort
- Supports auto-fixable suggestions for common patterns
- Exports suggestions for AI-assisted code review

Circular Exchange Framework Integration:
-----------------------------------------
Module ID: shared.circular_exchange.refactoring_engine
Description: Automated refactoring suggestion engine for continuous code improvement
Dependencies: [shared.circular_exchange.metrics_analyzer, shared.circular_exchange.data_collector]
Exports: [RefactoringEngine, CodeSuggestion, RefactoringPlan, REFACTORING_ENGINE]

=============================================================================
"""

import logging
import threading
import re
import ast
import os
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict, Counter
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class SuggestionType(Enum):
    """Types of refactoring suggestions."""
    ERROR_HANDLING = "error_handling"
    PERFORMANCE = "performance"
    CODE_ORGANIZATION = "code_organization"
    TESTING = "testing"
    LOGGING = "logging"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    TYPE_HINTS = "type_hints"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"


class EffortLevel(Enum):
    """Estimated effort to implement a suggestion."""
    TRIVIAL = 1  # Minutes - simple one-line changes
    LOW = 2      # < 1 hour - straightforward changes
    MEDIUM = 3   # 1-4 hours - requires some thought
    HIGH = 4     # 1-2 days - significant refactoring
    MAJOR = 5    # > 2 days - architectural changes


class ImpactLevel(Enum):
    """Estimated impact of implementing a suggestion."""
    CRITICAL = 1  # Fixes security issues or major bugs
    HIGH = 2      # Significant performance/reliability improvement
    MEDIUM = 3    # Noticeable improvement
    LOW = 4       # Minor improvement
    COSMETIC = 5  # Code style/readability only


@dataclass
class CodeLocation:
    """Represents a location in the codebase."""
    file_path: str
    start_line: int
    end_line: int
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CodeSuggestion:
    """Represents a specific code change suggestion."""
    suggestion_id: str
    suggestion_type: SuggestionType
    title: str
    description: str
    location: CodeLocation
    current_code: str
    suggested_code: str
    impact: ImpactLevel
    effort: EffortLevel
    auto_fixable: bool = False
    evidence: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['suggestion_type'] = self.suggestion_type.value
        data['impact'] = self.impact.value
        data['effort'] = self.effort.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def priority_score(self) -> float:
        """Calculate priority score (lower = higher priority)."""
        # Combine impact and effort for prioritization
        # Higher impact (lower value) + lower effort = higher priority
        return (self.impact.value * 0.7) + (self.effort.value * 0.3)


@dataclass
class RefactoringPlan:
    """A plan containing multiple related suggestions."""
    plan_id: str
    title: str
    description: str
    suggestions: List[CodeSuggestion] = field(default_factory=list)
    total_impact: str = ""
    estimated_time: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            'plan_id': self.plan_id,
            'title': self.title,
            'description': self.description,
            'suggestions': [s.to_dict() for s in self.suggestions],
            'total_impact': self.total_impact,
            'estimated_time': self.estimated_time,
            'created_at': self.created_at.isoformat(),
            'tags': self.tags,
        }
        return data


class RefactoringEngine:
    """
    Automated refactoring suggestion engine.
    
    This singleton analyzes patterns and insights from the MetricsAnalyzer
    to generate actionable code improvement suggestions. It:
    
    1. Analyzes error patterns → suggests better error handling
    2. Analyzes performance data → suggests optimizations
    3. Analyzes test results → suggests testing improvements
    4. Analyzes code structure → suggests organization improvements
    
    Suggestions can be:
    - Auto-fixable: Engine can generate the exact code change
    - Manual: Requires human judgment but provides guidance
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global refactoring engine."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the refactoring engine."""
        if self._initialized:
            return
        
        self._lock = threading.RLock()
        
        # Suggestion storage
        self._suggestions: Dict[str, CodeSuggestion] = {}
        self._plans: Dict[str, RefactoringPlan] = {}
        
        # References to other components
        self._metrics_analyzer = None
        self._data_collector = None
        
        # Configuration
        self._project_root = Path(os.getcwd())
        
        # Subscribers
        self._suggestion_subscribers: List[callable] = []
        
        self._initialized = True
        logger.info("RefactoringEngine initialized")
    
    def _get_metrics_analyzer(self):
        """Lazy-load the metrics analyzer."""
        if self._metrics_analyzer is None:
            try:
                from shared.circular_exchange.analysis.metrics_analyzer import METRICS_ANALYZER
                self._metrics_analyzer = METRICS_ANALYZER
            except ImportError:
                logger.warning("Could not import METRICS_ANALYZER")
        return self._metrics_analyzer

    def _get_data_collector(self):
        """Lazy-load the data collector."""
        if self._data_collector is None:
            try:
                from shared.circular_exchange.analysis.data_collector import DATA_COLLECTOR
                self._data_collector = DATA_COLLECTOR
            except ImportError:
                logger.warning("Could not import DATA_COLLECTOR")
        return self._data_collector
    
    # =========================================================================
    # ERROR HANDLING SUGGESTIONS
    # =========================================================================
    
    def analyze_error_handling(self) -> List[CodeSuggestion]:
        """
        Analyze error patterns and suggest improved error handling.
        
        Returns:
            List of error handling improvement suggestions
        """
        analyzer = self._get_metrics_analyzer()
        if analyzer is None:
            return []
        
        suggestions = []
        patterns = analyzer.get_patterns()
        
        for pattern in patterns:
            if pattern.pattern_type.value == "error_recurring":
                # Generate suggestion based on error pattern
                suggestion = self._create_error_handling_suggestion(pattern)
                if suggestion:
                    suggestions.append(suggestion)
                    self._suggestions[suggestion.suggestion_id] = suggestion
        
        # Notify subscribers
        for suggestion in suggestions:
            self._notify_subscribers(suggestion)
        
        return suggestions
    
    def _create_error_handling_suggestion(self, pattern) -> Optional[CodeSuggestion]:
        """Create an error handling suggestion from a pattern."""
        if not pattern.affected_modules:
            return None
        
        module = pattern.affected_modules[0]
        suggestion_id = f"err_{pattern.pattern_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Generate suggestion based on pattern description
        current_code = "# Current error handling (if any)"
        
        # Create improved error handling template
        suggested_code = f'''try:
    # Original code that raises the error
    pass
except Exception as e:
    logger.error(
        "Error in {module}: %s",
        str(e),
        extra={{"pattern": "{pattern.pattern_id}", "occurrences": {pattern.occurrences}}}
    )
    # Consider: retry logic, fallback behavior, or graceful degradation
    raise  # or handle appropriately'''
        
        return CodeSuggestion(
            suggestion_id=suggestion_id,
            suggestion_type=SuggestionType.ERROR_HANDLING,
            title=f"Improve error handling for recurring error",
            description=f"This error has occurred {pattern.occurrences} times. Consider adding:\n"
                       f"- Specific exception handling\n"
                       f"- Retry logic for transient failures\n"
                       f"- Better error logging with context",
            location=CodeLocation(
                file_path=f"{module.replace('.', '/')}.py",
                start_line=0,
                end_line=0
            ),
            current_code=current_code,
            suggested_code=suggested_code,
            impact=ImpactLevel.HIGH if pattern.occurrences > 10 else ImpactLevel.MEDIUM,
            effort=EffortLevel.LOW,
            auto_fixable=False,
            evidence=[
                f"Error occurred {pattern.occurrences} times",
                f"First seen: {pattern.first_seen.isoformat()}",
                f"Last seen: {pattern.last_seen.isoformat()}"
            ],
            related_patterns=[pattern.pattern_id],
            tags=["error-handling", "reliability"]
        )
    
    # =========================================================================
    # PERFORMANCE SUGGESTIONS
    # =========================================================================
    
    def analyze_performance(self) -> List[CodeSuggestion]:
        """
        Analyze performance bottlenecks and suggest optimizations.
        
        Returns:
            List of performance improvement suggestions
        """
        analyzer = self._get_metrics_analyzer()
        if analyzer is None:
            return []
        
        suggestions = []
        bottlenecks = analyzer.get_bottlenecks()
        
        for bottleneck in bottlenecks:
            suggestion = self._create_performance_suggestion(bottleneck)
            if suggestion:
                suggestions.append(suggestion)
                self._suggestions[suggestion.suggestion_id] = suggestion
        
        # Notify subscribers
        for suggestion in suggestions:
            self._notify_subscribers(suggestion)
        
        return suggestions
    
    def _create_performance_suggestion(self, bottleneck) -> Optional[CodeSuggestion]:
        """Create a performance suggestion from a bottleneck."""
        suggestion_id = f"perf_{bottleneck.bottleneck_id}"
        
        # Generate optimization suggestions based on the bottleneck
        suggested_optimizations = []
        
        if bottleneck.avg_duration_ms > 5000:
            suggested_optimizations.append("Consider async/await for I/O operations")
            suggested_optimizations.append("Add caching for frequently accessed data")
        
        if bottleneck.percentile_95_ms > bottleneck.avg_duration_ms * 3:
            suggested_optimizations.append("High variance detected - consider timeout handling")
            suggested_optimizations.append("Profile edge cases causing slow performance")
        
        suggested_code = f'''# Performance optimization for {bottleneck.function_name}

# Option 1: Add caching
from functools import lru_cache

@lru_cache(maxsize=128)
def {bottleneck.function_name}_cached(*args):
    return {bottleneck.function_name}(*args)

# Option 2: Add timeout handling
import asyncio

async def {bottleneck.function_name}_with_timeout(*args, timeout=30):
    try:
        return await asyncio.wait_for(
            {bottleneck.function_name}_async(*args),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning("{bottleneck.function_name} timed out after %d seconds", timeout)
        raise'''
        
        return CodeSuggestion(
            suggestion_id=suggestion_id,
            suggestion_type=SuggestionType.PERFORMANCE,
            title=f"Optimize {bottleneck.function_name} performance",
            description=f"Average processing time: {bottleneck.avg_duration_ms:.0f}ms\n"
                       f"P95 latency: {bottleneck.percentile_95_ms:.0f}ms\n"
                       f"Call count: {bottleneck.call_count}\n\n"
                       f"Suggestions:\n" + "\n".join(f"- {s}" for s in suggested_optimizations),
            location=CodeLocation(
                file_path=bottleneck.location,
                start_line=0,
                end_line=0,
                function_name=bottleneck.function_name
            ),
            current_code=f"# Current implementation of {bottleneck.function_name}",
            suggested_code=suggested_code,
            impact=ImpactLevel.HIGH if bottleneck.avg_duration_ms > 3000 else ImpactLevel.MEDIUM,
            effort=EffortLevel.MEDIUM,
            auto_fixable=False,
            evidence=[
                f"Average duration: {bottleneck.avg_duration_ms:.0f}ms",
                f"P95 duration: {bottleneck.percentile_95_ms:.0f}ms",
                f"Call count: {bottleneck.call_count}",
                bottleneck.suggested_optimization
            ],
            related_patterns=[],
            tags=["performance", "optimization"]
        )
    
    # =========================================================================
    # TEST IMPROVEMENT SUGGESTIONS
    # =========================================================================
    
    def analyze_testing(self) -> List[CodeSuggestion]:
        """
        Analyze test health and suggest testing improvements.
        
        Returns:
            List of testing improvement suggestions
        """
        analyzer = self._get_metrics_analyzer()
        if analyzer is None:
            return []
        
        suggestions = []
        
        # Analyze test health
        report = analyzer.analyze_test_health()
        
        # Suggest fixes for flaky tests
        for flaky_test in report.flaky_tests[:5]:
            suggestion = self._create_flaky_test_suggestion(flaky_test)
            suggestions.append(suggestion)
            self._suggestions[suggestion.suggestion_id] = suggestion
        
        # Suggest optimizations for slow tests
        for slow_test in report.slow_tests[:5]:
            suggestion = self._create_slow_test_suggestion(slow_test)
            suggestions.append(suggestion)
            self._suggestions[suggestion.suggestion_id] = suggestion
        
        # Notify subscribers
        for suggestion in suggestions:
            self._notify_subscribers(suggestion)
        
        return suggestions
    
    def _create_flaky_test_suggestion(self, test_name: str) -> CodeSuggestion:
        """Create a suggestion for fixing a flaky test."""
        suggestion_id = f"test_flaky_{hash(test_name) % 100000}"
        
        suggested_code = f'''# Fix for flaky test: {test_name}

import pytest
from unittest.mock import patch, MagicMock

class Test{test_name.replace("test_", "").title().replace("_", "")}:
    """Refactored test with better isolation."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure clean state before each test."""
        # Reset any shared state
        yield
        # Cleanup after test
    
    def test_with_retry(self):
        """Original test with retry logic for transient failures."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Original test logic
                assert True  # Replace with actual assertions
                break
            except AssertionError:
                if attempt == max_retries - 1:
                    raise
                # Brief delay before retry
                import time
                time.sleep(0.1)'''
        
        return CodeSuggestion(
            suggestion_id=suggestion_id,
            suggestion_type=SuggestionType.TESTING,
            title=f"Fix flaky test: {test_name}",
            description="This test has inconsistent results. Consider:\n"
                       "- Adding proper test isolation\n"
                       "- Mocking external dependencies\n"
                       "- Adding retry logic for transient failures\n"
                       "- Checking for race conditions",
            location=CodeLocation(
                file_path="tests/",
                start_line=0,
                end_line=0,
                function_name=test_name
            ),
            current_code=f"def {test_name}():\n    # Flaky test implementation",
            suggested_code=suggested_code,
            impact=ImpactLevel.HIGH,
            effort=EffortLevel.MEDIUM,
            auto_fixable=False,
            evidence=["Test has both pass and fail results in recent runs"],
            tags=["testing", "flaky", "reliability"]
        )
    
    def _create_slow_test_suggestion(self, test_name: str) -> CodeSuggestion:
        """Create a suggestion for optimizing a slow test."""
        suggestion_id = f"test_slow_{hash(test_name) % 100000}"
        
        suggested_code = f'''# Optimization for slow test: {test_name}

import pytest
from unittest.mock import patch, MagicMock

# Option 1: Use mocking to avoid slow I/O
@patch('module.slow_external_call')
def {test_name}(mock_call):
    mock_call.return_value = {{"expected": "data"}}
    # Test logic without actual I/O
    result = function_under_test()
    assert result is not None

# Option 2: Use pytest fixtures with scope for expensive setup
@pytest.fixture(scope="module")
def expensive_resource():
    """Shared expensive resource across tests."""
    resource = create_expensive_resource()
    yield resource
    resource.cleanup()

# Option 3: Skip slow tests in CI with marker
@pytest.mark.slow
def {test_name}_full():
    """Full integration test - run only when needed."""
    pass'''
        
        return CodeSuggestion(
            suggestion_id=suggestion_id,
            suggestion_type=SuggestionType.TESTING,
            title=f"Optimize slow test: {test_name}",
            description="This test exceeds the duration threshold. Consider:\n"
                       "- Mocking slow external dependencies\n"
                       "- Using fixtures with broader scope\n"
                       "- Marking as slow/integration test\n"
                       "- Parallelizing independent operations",
            location=CodeLocation(
                file_path="tests/",
                start_line=0,
                end_line=0,
                function_name=test_name
            ),
            current_code=f"def {test_name}():\n    # Slow test implementation",
            suggested_code=suggested_code,
            impact=ImpactLevel.MEDIUM,
            effort=EffortLevel.LOW,
            auto_fixable=False,
            evidence=["Test duration exceeds threshold"],
            tags=["testing", "performance", "optimization"]
        )
    
    # =========================================================================
    # MODEL FINE-TUNING SUGGESTIONS
    # =========================================================================
    
    def analyze_model_training(self) -> List[CodeSuggestion]:
        """
        Analyze model performance and suggest training improvements.
        
        Returns:
            List of model training suggestions
        """
        analyzer = self._get_metrics_analyzer()
        if analyzer is None:
            return []
        
        suggestions = []
        reports = analyzer.analyze_model_performance()
        
        for report in reports:
            if report.success_rate < 0.9:
                suggestion = self._create_model_training_suggestion(report)
                suggestions.append(suggestion)
                self._suggestions[suggestion.suggestion_id] = suggestion
        
        return suggestions
    
    def _create_model_training_suggestion(self, report) -> CodeSuggestion:
        """Create a model training suggestion from performance report."""
        suggestion_id = f"model_{report.model_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        training_focus = "\n".join(f"- {focus}" for focus in report.recommended_training_focus)
        
        suggested_code = f'''# Fine-tuning configuration for {report.model_id}

training_config = {{
    "model_id": "{report.model_id}",
    "target_success_rate": 0.95,
    "current_success_rate": {report.success_rate:.2f},
    
    # Training data requirements
    "min_samples": 1000,
    "validation_split": 0.2,
    
    # Focus areas based on error analysis
    "training_focus": {report.recommended_training_focus},
    
    # Hyperparameters (adjust based on model type)
    "learning_rate": 1e-5,
    "batch_size": 16,
    "epochs": 10,
    
    # Data augmentation to address low confidence patterns
    "augmentation": {{
        "enabled": True,
        "techniques": ["rotation", "noise", "contrast"]
    }}
}}

# Export training data
from shared.circular_exchange.data_collector import DATA_COLLECTOR
DATA_COLLECTOR.export_training_data(Path("training_data/{report.model_id}.jsonl"))'''
        
        return CodeSuggestion(
            suggestion_id=suggestion_id,
            suggestion_type=SuggestionType.CONFIGURATION,
            title=f"Fine-tune {report.model_id} model",
            description=f"Current success rate: {report.success_rate:.1%}\n"
                       f"Average confidence: {report.avg_confidence:.1%}\n"
                       f"Training data quality: {report.training_data_quality_score:.1%}\n\n"
                       f"Recommended focus areas:\n{training_focus}",
            location=CodeLocation(
                file_path=f"shared/models/{report.model_id}.py",
                start_line=0,
                end_line=0
            ),
            current_code="# Current model configuration",
            suggested_code=suggested_code,
            impact=ImpactLevel.HIGH,
            effort=EffortLevel.HIGH,
            auto_fixable=False,
            evidence=[
                f"Success rate: {report.success_rate:.1%}",
                f"Avg confidence: {report.avg_confidence:.1%}",
                f"Total extractions: {report.total_extractions}",
                f"Training data quality: {report.training_data_quality_score:.1%}"
            ],
            tags=["model", "fine-tuning", "ml"]
        )
    
    # =========================================================================
    # REFACTORING PLANS
    # =========================================================================
    
    def create_refactoring_plan(
        self,
        title: str,
        description: str,
        suggestion_ids: Optional[List[str]] = None,
        auto_select: bool = False,
        max_suggestions: int = 10
    ) -> RefactoringPlan:
        """
        Create a refactoring plan from selected suggestions.
        
        Args:
            title: Plan title
            description: Plan description
            suggestion_ids: Specific suggestion IDs to include
            auto_select: If True, auto-select high-priority suggestions
            max_suggestions: Maximum suggestions to include
            
        Returns:
            RefactoringPlan object
        """
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if suggestion_ids:
            suggestions = [
                self._suggestions[sid] 
                for sid in suggestion_ids 
                if sid in self._suggestions
            ]
        elif auto_select:
            # Auto-select based on priority
            all_suggestions = sorted(
                self._suggestions.values(),
                key=lambda s: s.priority_score()
            )
            suggestions = all_suggestions[:max_suggestions]
        else:
            suggestions = []
        
        # Calculate total impact
        impact_scores = {
            ImpactLevel.CRITICAL: 5,
            ImpactLevel.HIGH: 4,
            ImpactLevel.MEDIUM: 3,
            ImpactLevel.LOW: 2,
            ImpactLevel.COSMETIC: 1
        }
        total_impact_score = sum(impact_scores[s.impact] for s in suggestions)
        total_impact = f"Total impact score: {total_impact_score}"
        
        # Estimate time
        effort_hours = {
            EffortLevel.TRIVIAL: 0.25,
            EffortLevel.LOW: 1,
            EffortLevel.MEDIUM: 4,
            EffortLevel.HIGH: 16,
            EffortLevel.MAJOR: 40
        }
        total_hours = sum(effort_hours[s.effort] for s in suggestions)
        estimated_time = f"Estimated time: {total_hours:.1f} hours"
        
        # Collect tags
        all_tags = set()
        for s in suggestions:
            all_tags.update(s.tags)
        
        plan = RefactoringPlan(
            plan_id=plan_id,
            title=title,
            description=description,
            suggestions=suggestions,
            total_impact=total_impact,
            estimated_time=estimated_time,
            tags=list(all_tags)
        )
        
        self._plans[plan_id] = plan
        
        return plan
    
    def generate_comprehensive_plan(self) -> RefactoringPlan:
        """
        Generate a comprehensive refactoring plan by analyzing all data.
        
        Returns:
            RefactoringPlan with prioritized suggestions
        """
        # Run all analyses
        error_suggestions = self.analyze_error_handling()
        performance_suggestions = self.analyze_performance()
        testing_suggestions = self.analyze_testing()
        model_suggestions = self.analyze_model_training()
        
        all_suggestions = (
            error_suggestions + 
            performance_suggestions + 
            testing_suggestions + 
            model_suggestions
        )
        
        if not all_suggestions:
            return RefactoringPlan(
                plan_id=f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                title="No Suggestions",
                description="No refactoring suggestions generated. The codebase appears healthy."
            )
        
        # Sort by priority
        all_suggestions.sort(key=lambda s: s.priority_score())
        
        return self.create_refactoring_plan(
            title="Comprehensive Refactoring Plan",
            description="Auto-generated plan based on error patterns, performance bottlenecks, "
                       "test health, and model performance analysis.",
            suggestion_ids=[s.suggestion_id for s in all_suggestions[:20]],
            auto_select=False
        )
    
    def analyze_all(self) -> List[CodeSuggestion]:
        """
        Run all analysis methods and return combined suggestions.
        
        This method runs:
        - analyze_error_handling()
        - analyze_performance()
        - analyze_testing()
        - analyze_model_training()
        
        Returns:
            List of all CodeSuggestion objects from all analyses
        """
        error_suggestions = self.analyze_error_handling()
        performance_suggestions = self.analyze_performance()
        testing_suggestions = self.analyze_testing()
        model_suggestions = self.analyze_model_training()
        
        all_suggestions = (
            error_suggestions + 
            performance_suggestions + 
            testing_suggestions + 
            model_suggestions
        )
        
        # Sort by priority
        all_suggestions.sort(key=lambda s: s.priority_score())
        
        return all_suggestions
    
    # =========================================================================
    # EXPORT & REPORTING
    # =========================================================================
    
    def export_suggestions(self, output_path: Optional[Path] = None) -> Path:
        """
        Export all suggestions to a JSON file.
        
        Args:
            output_path: Optional output path
            
        Returns:
            Path to the exported file
        """
        import json
        
        if output_path is None:
            output_path = Path("data/refactoring_suggestions.json")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            data = {
                "generated_at": datetime.now().isoformat(),
                "total_suggestions": len(self._suggestions),
                "suggestions": [s.to_dict() for s in self._suggestions.values()],
                "plans": [p.to_dict() for p in self._plans.values()]
            }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info("Exported %d suggestions to %s", len(self._suggestions), output_path)
        return output_path
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all suggestions."""
        with self._lock:
            suggestions = list(self._suggestions.values())
        
        return {
            "total_suggestions": len(suggestions),
            "by_type": dict(Counter(s.suggestion_type.value for s in suggestions)),
            "by_impact": dict(Counter(s.impact.value for s in suggestions)),
            "by_effort": dict(Counter(s.effort.value for s in suggestions)),
            "auto_fixable_count": sum(1 for s in suggestions if s.auto_fixable),
            "total_plans": len(self._plans)
        }
    
    # =========================================================================
    # SUBSCRIPTION MANAGEMENT
    # =========================================================================
    
    def subscribe(self, callback: callable) -> None:
        """Subscribe to new suggestion notifications."""
        with self._lock:
            if callback not in self._suggestion_subscribers:
                self._suggestion_subscribers.append(callback)
    
    def unsubscribe(self, callback: callable) -> None:
        """Unsubscribe from notifications."""
        with self._lock:
            if callback in self._suggestion_subscribers:
                self._suggestion_subscribers.remove(callback)
    
    def _notify_subscribers(self, suggestion: CodeSuggestion) -> None:
        """Notify all subscribers of a new suggestion."""
        for callback in self._suggestion_subscribers:
            try:
                callback(suggestion)
            except Exception as e:
                logger.error("Error notifying subscriber: %s", e)
    
    # =========================================================================
    # QUERY METHODS
    # =========================================================================
    
    def get_suggestions(
        self,
        suggestion_type: Optional[SuggestionType] = None,
        min_impact: Optional[ImpactLevel] = None,
        max_effort: Optional[EffortLevel] = None,
        auto_fixable_only: bool = False,
        limit: int = 50
    ) -> List[CodeSuggestion]:
        """Get suggestions with optional filtering."""
        with self._lock:
            suggestions = list(self._suggestions.values())
        
        if suggestion_type:
            suggestions = [s for s in suggestions if s.suggestion_type == suggestion_type]
        
        if min_impact:
            suggestions = [s for s in suggestions if s.impact.value <= min_impact.value]
        
        if max_effort:
            suggestions = [s for s in suggestions if s.effort.value <= max_effort.value]
        
        if auto_fixable_only:
            suggestions = [s for s in suggestions if s.auto_fixable]
        
        # Sort by priority
        suggestions.sort(key=lambda s: s.priority_score())
        
        return suggestions[:limit]
    
    def get_plans(self) -> List[RefactoringPlan]:
        """Get all refactoring plans."""
        with self._lock:
            return list(self._plans.values())
    
    def clear(self) -> None:
        """Clear all suggestions and plans."""
        with self._lock:
            self._suggestions.clear()
            self._plans.clear()


# Global singleton instance
REFACTORING_ENGINE = RefactoringEngine()


# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.circular_exchange.refactoring_engine",
            file_path=__file__,
            description="Automated refactoring suggestion engine for continuous code improvement",
            dependencies=["shared.circular_exchange.metrics_analyzer", "shared.circular_exchange.data_collector"],
            exports=["RefactoringEngine", "CodeSuggestion", "RefactoringPlan", 
                    "REFACTORING_ENGINE", "SuggestionType", "ImpactLevel", "EffortLevel"]
        ))
    except Exception:
        pass  # Ignore registration errors during import
