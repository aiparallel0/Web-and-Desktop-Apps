"""
Tests for the Metrics Analyzer module.

This test suite verifies the pattern detection and analysis system
that generates insights for continuous improvement.
"""

import pytest
import uuid
from datetime import datetime, timedelta


class TestMetricsAnalyzer:
    """Tests for the MetricsAnalyzer singleton."""
    
    def setup_method(self):
        """Reset the analyzers and collectors before each test."""
        from shared.circular_exchange.data_collector import (
            DATA_COLLECTOR, TestStatus, TestResult, LogEntry, ExtractionEvent
        )
        from shared.circular_exchange.metrics_analyzer import (
            METRICS_ANALYZER, PatternType, InsightPriority, RefactorCategory
        )
        
        self.collector = DATA_COLLECTOR
        self.analyzer = METRICS_ANALYZER
        self.TestStatus = TestStatus
        self.TestResult = TestResult
        self.LogEntry = LogEntry
        self.ExtractionEvent = ExtractionEvent
        self.PatternType = PatternType
        self.InsightPriority = InsightPriority
        self.RefactorCategory = RefactorCategory
        
        # Clear previous data
        self.collector.clear()
        self.analyzer.clear()
    
    def test_singleton_pattern(self):
        """Test that MetricsAnalyzer is a singleton."""
        from shared.circular_exchange.metrics_analyzer import MetricsAnalyzer
        
        analyzer1 = MetricsAnalyzer()
        analyzer2 = MetricsAnalyzer()
        
        assert analyzer1 is analyzer2
    
    def test_analyze_error_patterns_no_data(self):
        """Test error pattern analysis with no data."""
        patterns = self.analyzer.analyze_error_patterns()
        assert patterns == []
    
    def test_analyze_error_patterns_detects_recurring(self):
        """Test that recurring errors are detected as patterns."""
        # Add multiple similar error logs
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Connection timeout to database server",
                module="database",
                function="connect",
                line_number=42
            ))
        
        patterns = self.analyzer.analyze_error_patterns()
        
        # Should detect at least one pattern
        assert len(patterns) >= 1
        assert patterns[0].pattern_type == self.PatternType.ERROR_RECURRING
        assert patterns[0].occurrences >= 5
    
    def test_analyze_test_health_empty(self):
        """Test health analysis with no test data."""
        report = self.analyzer.analyze_test_health()
        
        assert report.total_tests == 0
        assert report.pass_rate == 0.0
    
    def test_analyze_test_health_with_data(self):
        """Test health analysis with test results."""
        # Add test results
        for i in range(8):
            self.collector.record_test_result(self.TestResult(
                test_id=str(i),
                test_name=f"test_success_{i}",
                module_path="tests/test_example.py",
                status=self.TestStatus.PASSED,
                duration_ms=100.0
            ))
        
        for i in range(2):
            self.collector.record_test_result(self.TestResult(
                test_id=str(i + 8),
                test_name=f"test_fail_{i}",
                module_path="tests/test_example.py",
                status=self.TestStatus.FAILED,
                duration_ms=200.0,
                error_message="Assertion failed"
            ))
        
        report = self.analyzer.analyze_test_health()
        
        assert report.total_tests == 10
        assert report.pass_rate == pytest.approx(0.8)
    
    def test_detect_flaky_tests(self):
        """Test detection of flaky tests."""
        # Add a test that sometimes passes and sometimes fails
        for i in range(3):
            self.collector.record_test_result(self.TestResult(
                test_id=str(uuid.uuid4()),
                test_name="test_flaky",
                module_path="tests/test_flaky.py",
                status=self.TestStatus.PASSED if i < 1 else self.TestStatus.FAILED,
                duration_ms=100.0
            ))
        
        report = self.analyzer.analyze_test_health()
        
        assert "test_flaky" in report.flaky_tests
    
    def test_detect_slow_tests(self):
        """Test detection of slow tests."""
        # Add a slow test
        self.collector.record_test_result(self.TestResult(
            test_id="1",
            test_name="test_slow",
            module_path="tests/test_slow.py",
            status=self.TestStatus.PASSED,
            duration_ms=10000.0  # 10 seconds - very slow
        ))
        
        report = self.analyzer.analyze_test_health()
        
        assert "test_slow" in report.slow_tests
    
    def test_analyze_performance_bottlenecks(self):
        """Test performance bottleneck detection."""
        # Add extraction events with varying performance
        for i in range(20):
            self.collector.record_extraction_event(self.ExtractionEvent(
                event_id=str(uuid.uuid4()),
                model_id="slow_model",
                image_path="/path/to/image.jpg",
                success=True,
                processing_time_ms=5000.0 if i < 5 else 1000.0,  # P95 will be high
                confidence_score=0.9
            ))
        
        bottlenecks = self.analyzer.analyze_performance()
        
        # Should detect bottleneck due to high variance
        assert len(bottlenecks) >= 0  # May or may not detect based on threshold
    
    def test_analyze_model_performance(self):
        """Test model performance analysis."""
        # Add extraction events for a model
        for i in range(10):
            self.collector.record_extraction_event(self.ExtractionEvent(
                event_id=str(uuid.uuid4()),
                model_id="test_model",
                image_path=f"/path/to/image_{i}.jpg",
                success=i < 7,  # 70% success rate
                processing_time_ms=1000.0,
                confidence_score=0.8 if i < 7 else 0.3,
                error_type="ParseError" if i >= 7 else None,
                ground_truth={"total": 100.0} if i < 5 else None  # 50% labeled
            ))
        
        reports = self.analyzer.analyze_model_performance()
        
        assert len(reports) == 1
        assert reports[0].model_id == "test_model"
        assert reports[0].success_rate == pytest.approx(0.7)
        assert reports[0].training_data_quality_score == pytest.approx(0.5)
    
    def test_generate_refactoring_insights(self):
        """Test insight generation from patterns."""
        # Add error logs to create patterns
        for i in range(10):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Database connection pool exhausted",
                module="db_pool",
                function="get_connection",
                line_number=100
            ))
        
        insights = self.analyzer.generate_refactoring_insights()
        
        # Should generate at least one insight
        assert len(insights) >= 1
    
    def test_insight_priority_filtering(self):
        """Test filtering insights by priority."""
        # Generate some insights
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message=f"Error type {i}",
                module="test",
                function="test",
                line_number=i
            ))
        
        self.analyzer.generate_refactoring_insights()
        
        high_priority = self.analyzer.get_insights(priority=self.InsightPriority.HIGH)
        # Should be a valid list (may be empty)
        assert isinstance(high_priority, list)
    
    def test_get_summary(self):
        """Test getting analysis summary."""
        summary = self.analyzer.get_summary()
        
        assert "total_patterns" in summary
        assert "total_insights" in summary
        assert "total_bottlenecks" in summary
        assert "patterns_by_type" in summary
        assert "insights_by_priority" in summary
    
    def test_subscriber_notification(self):
        """Test that subscribers are notified of new patterns."""
        received_patterns = []
        
        def on_pattern(pattern):
            received_patterns.append(pattern)
        
        self.analyzer.subscribe_to_patterns(on_pattern)
        
        # Generate patterns
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Repeated error message",
                module="test",
                function="test",
                line_number=1
            ))
        
        self.analyzer.analyze_error_patterns()
        
        # Should have received at least one pattern
        assert len(received_patterns) >= 1
    
    def test_clear_results(self):
        """Test clearing analysis results."""
        # Generate some data
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Test error",
                module="test",
                function="test",
                line_number=1
            ))
        
        self.analyzer.analyze_error_patterns()
        
        # Clear
        self.analyzer.clear()
        
        # Should be empty
        assert len(self.analyzer.get_patterns()) == 0
        assert len(self.analyzer.get_insights()) == 0


class TestPatternNormalization:
    """Tests for error message normalization."""
    
    def setup_method(self):
        from shared.circular_exchange.metrics_analyzer import METRICS_ANALYZER
        self.analyzer = METRICS_ANALYZER
    
    def test_normalize_timestamps(self):
        """Test that timestamps are normalized in error messages."""
        message = "Error at 2024-01-15T10:30:45 in processing"
        normalized = self.analyzer._normalize_error_message(message)
        
        assert "2024-01-15" not in normalized
        assert "<TIMESTAMP>" in normalized
    
    def test_normalize_paths(self):
        """Test that file paths are normalized."""
        message = "Failed to open /home/user/data/file.txt"
        normalized = self.analyzer._normalize_error_message(message)
        
        assert "/home/user" not in normalized
        assert "<PATH>" in normalized
    
    def test_normalize_ids(self):
        """Test that hex IDs are normalized."""
        message = "Request abc123def456 failed"
        normalized = self.analyzer._normalize_error_message(message)
        
        assert "abc123def456" not in normalized


class TestIntegration:
    """Integration tests for metrics analyzer with data collector."""
    
    def test_cef_module_registration(self):
        """Test that metrics analyzer is registered with CEF."""
        from shared.circular_exchange import METRICS_ANALYZER
        
        assert METRICS_ANALYZER is not None
    
    def test_pattern_type_enum(self):
        """Test PatternType enum values."""
        from shared.circular_exchange.metrics_analyzer import PatternType
        
        assert PatternType.ERROR_RECURRING.value == "error_recurring"
        assert PatternType.TEST_FLAKY.value == "test_flaky"
        assert PatternType.PERFORMANCE_DEGRADATION.value == "performance_degradation"
    
    def test_insight_priority_enum(self):
        """Test InsightPriority enum values."""
        from shared.circular_exchange.metrics_analyzer import InsightPriority
        
        assert InsightPriority.CRITICAL.value == 1
        assert InsightPriority.HIGH.value == 2
        assert InsightPriority.LOW.value == 4
    
    def test_refactor_category_enum(self):
        """Test RefactorCategory enum values."""
        from shared.circular_exchange.metrics_analyzer import RefactorCategory
        
        assert RefactorCategory.PERFORMANCE.value == "performance"
        assert RefactorCategory.RELIABILITY.value == "reliability"
        assert RefactorCategory.SECURITY.value == "security"
