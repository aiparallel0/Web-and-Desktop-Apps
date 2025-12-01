"""
Tests for the Refactoring Engine module.

This test suite verifies the automated refactoring suggestion engine
that generates code improvement suggestions based on pattern analysis.
"""

import pytest
import uuid
from datetime import datetime
from pathlib import Path
import tempfile


class TestRefactoringEngine:
    """Tests for the RefactoringEngine singleton."""
    
    def setup_method(self):
        """Reset the engine and related components before each test."""
        from shared.circular_exchange.data_collector import (
            DATA_COLLECTOR, TestStatus, TestResult, LogEntry, ExtractionEvent
        )
        from shared.circular_exchange.metrics_analyzer import METRICS_ANALYZER
        from shared.circular_exchange.refactoring_engine import (
            REFACTORING_ENGINE, SuggestionType, ImpactLevel, EffortLevel
        )
        
        self.collector = DATA_COLLECTOR
        self.analyzer = METRICS_ANALYZER
        self.engine = REFACTORING_ENGINE
        
        self.TestStatus = TestStatus
        self.TestResult = TestResult
        self.LogEntry = LogEntry
        self.ExtractionEvent = ExtractionEvent
        self.SuggestionType = SuggestionType
        self.ImpactLevel = ImpactLevel
        self.EffortLevel = EffortLevel
        
        # Clear previous data
        self.collector.clear()
        self.analyzer.clear()
        self.engine.clear()
    
    def test_singleton_pattern(self):
        """Test that RefactoringEngine is a singleton."""
        from shared.circular_exchange.refactoring_engine import RefactoringEngine
        
        engine1 = RefactoringEngine()
        engine2 = RefactoringEngine()
        
        assert engine1 is engine2
    
    def test_analyze_error_handling_no_data(self):
        """Test error handling analysis with no data."""
        suggestions = self.engine.analyze_error_handling()
        assert suggestions == []
    
    def test_analyze_error_handling_with_patterns(self):
        """Test error handling suggestions from error patterns."""
        # Add error logs to create patterns
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Database connection timeout",
                module="db_module",
                function="connect",
                line_number=100
            ))
        
        # Analyze patterns first
        self.analyzer.analyze_error_patterns()
        
        # Generate suggestions
        suggestions = self.engine.analyze_error_handling()
        
        # Should have at least one suggestion
        assert len(suggestions) >= 1
        assert suggestions[0].suggestion_type == self.SuggestionType.ERROR_HANDLING
    
    def test_analyze_performance_no_data(self):
        """Test performance analysis with no data."""
        suggestions = self.engine.analyze_performance()
        assert suggestions == []
    
    def test_analyze_testing_with_flaky_tests(self):
        """Test testing analysis with flaky tests."""
        # Add flaky test results
        for i in range(4):
            self.collector.record_test_result(self.TestResult(
                test_id=str(uuid.uuid4()),
                test_name="test_flaky_example",
                module_path="tests/test_example.py",
                status=self.TestStatus.PASSED if i < 2 else self.TestStatus.FAILED,
                duration_ms=100.0
            ))
        
        suggestions = self.engine.analyze_testing()
        
        # Should have flaky test suggestion
        flaky_suggestions = [s for s in suggestions if "flaky" in s.title.lower()]
        assert len(flaky_suggestions) >= 1
    
    def test_analyze_testing_with_slow_tests(self):
        """Test testing analysis with slow tests."""
        # Add slow test result
        self.collector.record_test_result(self.TestResult(
            test_id="slow1",
            test_name="test_very_slow",
            module_path="tests/test_slow.py",
            status=self.TestStatus.PASSED,
            duration_ms=10000.0  # 10 seconds
        ))
        
        suggestions = self.engine.analyze_testing()
        
        # Should have slow test suggestion
        slow_suggestions = [s for s in suggestions if "slow" in s.title.lower()]
        assert len(slow_suggestions) >= 1
    
    def test_code_suggestion_priority_score(self):
        """Test CodeSuggestion priority score calculation."""
        from shared.circular_exchange.refactoring_engine import CodeSuggestion, CodeLocation
        
        high_priority = CodeSuggestion(
            suggestion_id="high",
            suggestion_type=self.SuggestionType.ERROR_HANDLING,
            title="Critical fix",
            description="Important fix",
            location=CodeLocation("file.py", 1, 10),
            current_code="",
            suggested_code="",
            impact=self.ImpactLevel.CRITICAL,
            effort=self.EffortLevel.TRIVIAL
        )
        
        low_priority = CodeSuggestion(
            suggestion_id="low",
            suggestion_type=self.SuggestionType.DOCUMENTATION,
            title="Minor improvement",
            description="Nice to have",
            location=CodeLocation("file.py", 1, 10),
            current_code="",
            suggested_code="",
            impact=self.ImpactLevel.COSMETIC,
            effort=self.EffortLevel.MAJOR
        )
        
        # Higher priority = lower score
        assert high_priority.priority_score() < low_priority.priority_score()
    
    def test_create_refactoring_plan(self):
        """Test creating a refactoring plan."""
        # Generate some suggestions first
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Test error for plan",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        self.analyzer.analyze_error_patterns()
        self.engine.analyze_error_handling()
        
        plan = self.engine.create_refactoring_plan(
            title="Test Plan",
            description="Test refactoring plan",
            auto_select=True,
            max_suggestions=5
        )
        
        assert plan.plan_id is not None
        assert plan.title == "Test Plan"
    
    def test_generate_comprehensive_plan(self):
        """Test generating a comprehensive refactoring plan."""
        # Add some data for analysis
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Comprehensive test error",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        plan = self.engine.generate_comprehensive_plan()
        
        assert plan is not None
        assert plan.plan_id is not None
    
    def test_analyze_all(self):
        """Test analyze_all method runs all analyses and returns combined suggestions."""
        # Add some data for analysis
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Analyze all test error",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        # Also add a flaky test
        for i in range(4):
            self.collector.record_test_result(self.TestResult(
                test_id=str(uuid.uuid4()),
                test_name="test_flaky_for_analyze_all",
                module_path="tests/test_example.py",
                status=self.TestStatus.PASSED if i < 2 else self.TestStatus.FAILED,
                duration_ms=100.0
            ))
        
        # Analyze patterns
        self.analyzer.analyze_error_patterns()
        
        # Call analyze_all
        suggestions = self.engine.analyze_all()
        
        # Should return a list
        assert isinstance(suggestions, list)
        
        # Should have suggestions from both error handling and testing
        error_suggestions = [s for s in suggestions if s.suggestion_type == self.SuggestionType.ERROR_HANDLING]
        testing_suggestions = [s for s in suggestions if s.suggestion_type == self.SuggestionType.TESTING]
        
        # At least one error handling suggestion
        assert len(error_suggestions) >= 1
        # At least one testing suggestion (for flaky test)
        assert len(testing_suggestions) >= 1
    
    def test_get_summary(self):
        """Test getting engine summary."""
        summary = self.engine.get_summary()
        
        assert "total_suggestions" in summary
        assert "by_type" in summary
        assert "by_impact" in summary
        assert "by_effort" in summary
        assert "auto_fixable_count" in summary
    
    def test_get_suggestions_filtering(self):
        """Test filtering suggestions by type."""
        # Generate some suggestions
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Filter test error",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        self.analyzer.analyze_error_patterns()
        self.engine.analyze_error_handling()
        
        # Filter by type
        error_suggestions = self.engine.get_suggestions(
            suggestion_type=self.SuggestionType.ERROR_HANDLING
        )
        
        for s in error_suggestions:
            assert s.suggestion_type == self.SuggestionType.ERROR_HANDLING
    
    def test_subscriber_notification(self):
        """Test subscriber notifications for new suggestions."""
        received = []
        
        def on_suggestion(suggestion):
            received.append(suggestion)
        
        self.engine.subscribe(on_suggestion)
        
        # Generate suggestions
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Subscriber test error",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        self.analyzer.analyze_error_patterns()
        self.engine.analyze_error_handling()
        
        # Should have received notifications
        assert len(received) >= 1
        
        self.engine.unsubscribe(on_suggestion)
    
    def test_export_suggestions(self):
        """Test exporting suggestions to JSON."""
        # Generate some suggestions
        for i in range(3):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Export test error",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        self.analyzer.analyze_error_patterns()
        self.engine.analyze_error_handling()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "suggestions.json"
            result_path = self.engine.export_suggestions(output_path)
            
            assert result_path.exists()
            
            import json
            with open(result_path) as f:
                data = json.load(f)
            
            assert "suggestions" in data
            assert "generated_at" in data
    
    def test_clear_engine(self):
        """Test clearing engine data."""
        # Generate some suggestions
        for i in range(3):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Clear test error",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        self.analyzer.analyze_error_patterns()
        self.engine.analyze_error_handling()
        
        # Verify we have suggestions
        assert len(self.engine.get_suggestions()) > 0
        
        # Clear
        self.engine.clear()
        
        # Should be empty
        assert len(self.engine.get_suggestions()) == 0


class TestCodeLocation:
    """Tests for CodeLocation dataclass."""
    
    def test_code_location_to_dict(self):
        """Test CodeLocation serialization."""
        from shared.circular_exchange.refactoring_engine import CodeLocation
        
        location = CodeLocation(
            file_path="path/to/file.py",
            start_line=10,
            end_line=20,
            function_name="my_function",
            class_name="MyClass"
        )
        
        data = location.to_dict()
        
        assert data["file_path"] == "path/to/file.py"
        assert data["start_line"] == 10
        assert data["function_name"] == "my_function"


class TestEnums:
    """Tests for refactoring engine enums."""
    
    def test_suggestion_type_values(self):
        """Test SuggestionType enum values."""
        from shared.circular_exchange.refactoring_engine import SuggestionType
        
        assert SuggestionType.ERROR_HANDLING.value == "error_handling"
        assert SuggestionType.PERFORMANCE.value == "performance"
        assert SuggestionType.TESTING.value == "testing"
    
    def test_effort_level_ordering(self):
        """Test EffortLevel enum ordering."""
        from shared.circular_exchange.refactoring_engine import EffortLevel
        
        assert EffortLevel.TRIVIAL.value < EffortLevel.LOW.value
        assert EffortLevel.LOW.value < EffortLevel.MEDIUM.value
        assert EffortLevel.MEDIUM.value < EffortLevel.HIGH.value
        assert EffortLevel.HIGH.value < EffortLevel.MAJOR.value
    
    def test_impact_level_ordering(self):
        """Test ImpactLevel enum ordering."""
        from shared.circular_exchange.refactoring_engine import ImpactLevel
        
        assert ImpactLevel.CRITICAL.value < ImpactLevel.HIGH.value
        assert ImpactLevel.HIGH.value < ImpactLevel.MEDIUM.value
        assert ImpactLevel.MEDIUM.value < ImpactLevel.LOW.value
        assert ImpactLevel.LOW.value < ImpactLevel.COSMETIC.value


class TestIntegration:
    """Integration tests for refactoring engine with other components."""
    
    def test_cef_module_registration(self):
        """Test that refactoring engine is registered with CEF."""
        from shared.circular_exchange import REFACTORING_ENGINE
        
        assert REFACTORING_ENGINE is not None
    
    def test_full_pipeline(self):
        """Test the full pipeline: data → analysis → suggestions."""
        from shared.circular_exchange import (
            DATA_COLLECTOR, METRICS_ANALYZER, REFACTORING_ENGINE,
            TestStatus, TestResult, LogEntry, ExtractionEvent
        )
        
        # Clear everything
        DATA_COLLECTOR.clear()
        METRICS_ANALYZER.clear()
        REFACTORING_ENGINE.clear()
        
        # Step 1: Collect data
        for i in range(10):
            DATA_COLLECTOR.record_log_entry(LogEntry(
                log_id=str(i),
                level="ERROR",
                message="Pipeline test error",
                module="pipeline_module",
                function="pipeline_func",
                line_number=100
            ))
        
        # Step 2: Analyze patterns
        patterns = METRICS_ANALYZER.analyze_error_patterns()
        
        # Step 3: Generate suggestions
        suggestions = REFACTORING_ENGINE.analyze_error_handling()
        
        # Step 4: Create plan
        plan = REFACTORING_ENGINE.generate_comprehensive_plan()
        
        # Verify pipeline worked
        assert len(patterns) >= 1
        assert plan is not None
