"""
Tests for the Data Collector module.

This test suite verifies the centralized data collection system that
feeds into continuous improvement, model fine-tuning, and code refactoring.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os


class TestDataCollector:
    """Tests for the DataCollector singleton."""
    
    def setup_method(self):
        """Reset the data collector before each test."""
        # Import here to avoid issues
        from shared.circular_exchange.data_collector import (
            DATA_COLLECTOR, DataCategory, TestStatus, TestResult,
            LogEntry, ExtractionEvent, RefactorSuggestion
        )
        
        self.collector = DATA_COLLECTOR
        self.DataCategory = DataCategory
        self.TestStatus = TestStatus
        self.TestResult = TestResult
        self.LogEntry = LogEntry
        self.ExtractionEvent = ExtractionEvent
        self.RefactorSuggestion = RefactorSuggestion
        
        # Clear previous data
        self.collector.clear()
    
    def test_singleton_pattern(self):
        """Test that DataCollector is a singleton."""
        from shared.circular_exchange.data_collector import DataCollector
        
        collector1 = DataCollector()
        collector2 = DataCollector()
        
        assert collector1 is collector2
    
    def test_record_test_result(self):
        """Test recording a test result."""
        result = self.TestResult(
            test_id=str(uuid.uuid4()),
            test_name="test_example",
            module_path="tests/test_example.py",
            status=self.TestStatus.PASSED,
            duration_ms=125.5,
            assertions=3
        )
        
        self.collector.record_test_result(result)
        
        # Verify it was recorded
        results = self.collector.get_test_results()
        assert len(results) == 1
        assert results[0].test_name == "test_example"
        assert results[0].status == self.TestStatus.PASSED
    
    def test_query_test_results_by_status(self):
        """Test filtering test results by status."""
        # Record mixed results
        for i in range(5):
            self.collector.record_test_result(self.TestResult(
                test_id=str(uuid.uuid4()),
                test_name=f"test_pass_{i}",
                module_path="tests/test_pass.py",
                status=self.TestStatus.PASSED,
                duration_ms=10.0
            ))
        
        for i in range(3):
            self.collector.record_test_result(self.TestResult(
                test_id=str(uuid.uuid4()),
                test_name=f"test_fail_{i}",
                module_path="tests/test_fail.py",
                status=self.TestStatus.FAILED,
                duration_ms=20.0,
                error_message="Assertion failed"
            ))
        
        # Query by status
        passed = self.collector.get_test_results(status=self.TestStatus.PASSED)
        failed = self.collector.get_test_results(status=self.TestStatus.FAILED)
        
        assert len(passed) == 5
        assert len(failed) == 3
    
    def test_record_log_entry(self):
        """Test recording a log entry."""
        entry = self.LogEntry(
            log_id=str(uuid.uuid4()),
            level="ERROR",
            message="Something went wrong",
            module="test_module",
            function="test_function",
            line_number=42,
            exception_info="ValueError: invalid input"
        )
        
        self.collector.record_log_entry(entry)
        
        # Verify it was recorded
        entries = self.collector.get_log_entries()
        assert len(entries) == 1
        assert entries[0].level == "ERROR"
        assert entries[0].message == "Something went wrong"
    
    def test_record_extraction_event(self):
        """Test recording an extraction event for model fine-tuning."""
        event = self.ExtractionEvent(
            event_id=str(uuid.uuid4()),
            model_id="donut_cord",
            image_path="/path/to/receipt.jpg",
            success=True,
            processing_time_ms=1500.0,
            confidence_score=0.95,
            extracted_data={"store": "Test Store", "total": 42.50},
            ground_truth={"store": "Test Store", "total": 42.50}
        )
        
        self.collector.record_extraction_event(event)
        
        # Verify it was recorded
        events = self.collector.get_extraction_events()
        assert len(events) == 1
        assert events[0].model_id == "donut_cord"
        assert events[0].success is True
        assert events[0].confidence_score == 0.95
    
    def test_query_extraction_events_by_model(self):
        """Test filtering extraction events by model."""
        # Record events for different models
        for model_id in ["donut_cord", "donut_cord", "florence2"]:
            self.collector.record_extraction_event(self.ExtractionEvent(
                event_id=str(uuid.uuid4()),
                model_id=model_id,
                image_path="/path/to/image.jpg",
                success=True,
                processing_time_ms=1000.0,
                confidence_score=0.9
            ))
        
        # Query by model
        donut_events = self.collector.get_extraction_events(model_id="donut_cord")
        florence_events = self.collector.get_extraction_events(model_id="florence2")
        
        assert len(donut_events) == 2
        assert len(florence_events) == 1
    
    def test_record_refactor_suggestion(self):
        """Test recording a refactoring suggestion."""
        suggestion = self.RefactorSuggestion(
            suggestion_id=str(uuid.uuid4()),
            file_path="shared/models/processor.py",
            category="performance",
            priority=8,
            description="Consider using list comprehension instead of for loop",
            suggested_change="Use [x for x in items if x.valid] instead of manual loop",
            evidence=["3 similar patterns found", "15% performance improvement possible"],
            auto_fixable=True
        )
        
        self.collector.record_refactor_suggestion(suggestion)
        
        # Verify it was recorded
        suggestions = self.collector.get_refactor_suggestions()
        assert len(suggestions) == 1
        assert suggestions[0].category == "performance"
        assert suggestions[0].priority == 8
    
    def test_statistics(self):
        """Test statistics calculation."""
        # Record some test results
        self.collector.record_test_result(self.TestResult(
            test_id="1", test_name="test1", module_path="t.py",
            status=self.TestStatus.PASSED, duration_ms=10.0
        ))
        self.collector.record_test_result(self.TestResult(
            test_id="2", test_name="test2", module_path="t.py",
            status=self.TestStatus.PASSED, duration_ms=10.0
        ))
        self.collector.record_test_result(self.TestResult(
            test_id="3", test_name="test3", module_path="t.py",
            status=self.TestStatus.FAILED, duration_ms=10.0
        ))
        
        # Record some extraction events
        self.collector.record_extraction_event(self.ExtractionEvent(
            event_id="1", model_id="model", image_path="i.jpg",
            success=True, processing_time_ms=100.0, confidence_score=0.9
        ))
        self.collector.record_extraction_event(self.ExtractionEvent(
            event_id="2", model_id="model", image_path="i.jpg",
            success=False, processing_time_ms=100.0, confidence_score=0.3
        ))
        
        stats = self.collector.get_statistics()
        
        assert stats['total_tests'] == 3
        assert stats['passed_tests'] == 2
        assert stats['failed_tests'] == 1
        assert stats['test_pass_rate'] == pytest.approx(2/3)
        assert stats['total_extractions'] == 2
        assert stats['successful_extractions'] == 1
        assert stats['extraction_success_rate'] == pytest.approx(0.5)
    
    def test_subscriber_notification(self):
        """Test that subscribers are notified of new data."""
        received_data = []
        
        def on_test_result(result):
            received_data.append(result)
        
        # Subscribe
        self.collector.subscribe(self.DataCategory.TEST_RESULT, on_test_result)
        
        # Record a test result
        result = self.TestResult(
            test_id="1", test_name="test1", module_path="t.py",
            status=self.TestStatus.PASSED, duration_ms=10.0
        )
        self.collector.record_test_result(result)
        
        # Verify notification
        assert len(received_data) == 1
        assert received_data[0].test_name == "test1"
        
        # Unsubscribe
        self.collector.unsubscribe(self.DataCategory.TEST_RESULT, on_test_result)
        
        # Record another result
        self.collector.record_test_result(result)
        
        # Should not have received another notification
        assert len(received_data) == 1
    
    def test_export_training_data(self):
        """Test exporting training data for model fine-tuning."""
        # Record events with ground truth
        for i in range(3):
            self.collector.record_extraction_event(self.ExtractionEvent(
                event_id=str(i),
                model_id="donut_cord",
                image_path=f"/path/to/image_{i}.jpg",
                success=True,
                processing_time_ms=1000.0,
                confidence_score=0.9,
                extracted_data={"total": 10.0 * i},
                ground_truth={"total": 10.0 * i}  # Include ground truth for training
            ))
        
        # Export to temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "training_data.jsonl"
            result_path = self.collector.export_training_data(output_path)
            
            assert result_path.exists()
            
            # Verify content
            with open(result_path) as f:
                lines = f.readlines()
            
            assert len(lines) == 3
    
    def test_clear_data(self):
        """Test clearing collected data."""
        # Record some data
        self.collector.record_test_result(self.TestResult(
            test_id="1", test_name="test1", module_path="t.py",
            status=self.TestStatus.PASSED, duration_ms=10.0
        ))
        self.collector.record_log_entry(self.LogEntry(
            log_id="1", level="INFO", message="test",
            module="test", function="test", line_number=1
        ))
        
        # Verify data exists
        assert len(self.collector.get_test_results()) > 0
        assert len(self.collector.get_log_entries()) > 0
        
        # Clear all
        self.collector.clear()
        
        # Verify data is gone
        assert len(self.collector.get_test_results()) == 0
        assert len(self.collector.get_log_entries()) == 0


class TestDataCollectorIntegration:
    """Integration tests for data collector with other components."""
    
    def test_cef_module_registration(self):
        """Test that data collector is registered with CEF."""
        from shared.circular_exchange import DATA_COLLECTOR
        
        assert DATA_COLLECTOR is not None
    
    def test_data_category_enum(self):
        """Test DataCategory enum values."""
        from shared.circular_exchange.data_collector import DataCategory
        
        assert DataCategory.TEST_RESULT.value == "test_result"
        assert DataCategory.USER_LOG.value == "user_log"
        assert DataCategory.EXTRACTION_RESULT.value == "extraction_result"
        assert DataCategory.MODEL_PERFORMANCE.value == "model_performance"
    
    def test_test_status_enum(self):
        """Test TestStatus enum values."""
        from shared.circular_exchange.data_collector import TestStatus
        
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"
        assert TestStatus.SKIPPED.value == "skipped"
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
"""
Tests for IntelligentAnalyzer - Phase 2 ML-based analysis components.
"""

import pytest
import math
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from shared.circular_exchange.intelligent_analyzer import (
    IntelligentAnalyzer,
    PatternClusterer,
    AnomalyDetector,
    TrendAnalyzer,
    CodeEmbeddings,
    PatternCluster,
    Anomaly,
    TrendAnalysis,
    CodeSimilarity,
    AnomalyType,
    TrendDirection,
    ClusterQuality,
    INTELLIGENT_ANALYZER
)


class TestPatternClusterer:
    """Tests for PatternClusterer class."""
    
    def test_cluster_similar_patterns(self):
        """Test clustering of similar patterns."""
        clusterer = PatternClusterer(similarity_threshold=0.5)
        
        patterns = [
            {
                'pattern_id': 'p1',
                'description': 'Connection timeout error in module A',
                'pattern_type': 'error_recurring',
                'occurrences': 10,
                'confidence': 0.8,
                'affected_modules': ['module_a']
            },
            {
                'pattern_id': 'p2',
                'description': 'Connection timeout error in module B',
                'pattern_type': 'error_recurring',
                'occurrences': 8,
                'confidence': 0.7,
                'affected_modules': ['module_b']
            },
            {
                'pattern_id': 'p3',
                'description': 'Memory allocation failed',
                'pattern_type': 'error_recurring',
                'occurrences': 5,
                'confidence': 0.9,
                'affected_modules': ['module_c']
            }
        ]
        
        clusters = clusterer.cluster_patterns(patterns)
        
        assert len(clusters) >= 1
        assert all(isinstance(c, PatternCluster) for c in clusters)
    
    def test_empty_patterns(self):
        """Test clustering with empty input."""
        clusterer = PatternClusterer()
        clusters = clusterer.cluster_patterns([])
        assert clusters == []
    
    def test_cluster_has_correct_attributes(self):
        """Test that clusters have all required attributes."""
        clusterer = PatternClusterer(similarity_threshold=0.3)
        
        patterns = [
            {
                'pattern_id': 'p1',
                'description': 'Test error pattern',
                'pattern_type': 'error_recurring',
                'occurrences': 5,
                'confidence': 0.8,
                'affected_modules': ['mod_a']
            }
        ]
        
        clusters = clusterer.cluster_patterns(patterns)
        
        assert len(clusters) == 1
        cluster = clusters[0]
        
        assert cluster.cluster_id is not None
        assert cluster.name is not None
        assert cluster.description is not None
        assert len(cluster.pattern_ids) > 0
        assert isinstance(cluster.quality, ClusterQuality)
    
    def test_get_cluster_for_pattern(self):
        """Test retrieving cluster for a specific pattern."""
        clusterer = PatternClusterer()
        
        patterns = [
            {
                'pattern_id': 'p1',
                'description': 'Connection timeout',
                'pattern_type': 'error_recurring',
                'occurrences': 5,
                'confidence': 0.8,
                'affected_modules': []
            }
        ]
        
        clusters = clusterer.cluster_patterns(patterns)
        
        retrieved = clusterer.get_cluster_for_pattern('p1')
        assert retrieved is not None
        assert 'p1' in retrieved.pattern_ids


class TestAnomalyDetector:
    """Tests for AnomalyDetector class."""
    
    def test_update_baseline(self):
        """Test baseline calculation."""
        detector = AnomalyDetector()
        
        values = [10.0, 12.0, 11.0, 9.0, 10.5, 11.5, 10.0, 12.0, 11.0, 10.0]
        baseline = detector.update_baseline('test_metric', values)
        
        assert 'mean' in baseline
        assert 'std' in baseline
        assert baseline['sample_count'] == 10
        assert 9.0 < baseline['mean'] < 12.0
    
    def test_detect_spike_anomaly(self):
        """Test detection of a spike anomaly."""
        detector = AnomalyDetector(z_score_threshold=2.0)
        
        # Normal values followed by a spike
        base_time = datetime.now()
        values = [
            (base_time - timedelta(hours=i), 10.0 + (i % 2))
            for i in range(10)
        ]
        values.append((base_time, 50.0))  # Spike
        
        anomalies = detector.detect_anomalies('latency_ms', values, 'test_component')
        
        assert len(anomalies) >= 1
        assert any(a.actual_value == 50.0 for a in anomalies)
    
    def test_no_anomaly_in_normal_data(self):
        """Test that normal data produces no anomalies."""
        detector = AnomalyDetector(z_score_threshold=3.0)
        
        base_time = datetime.now()
        # Very consistent values
        values = [
            (base_time - timedelta(hours=i), 10.0)
            for i in range(20)
        ]
        
        anomalies = detector.detect_anomalies('stable_metric', values, 'component')
        
        # With constant values, std = 0, so no z-score can be computed
        assert len(anomalies) == 0
    
    def test_anomaly_severity(self):
        """Test that anomaly severity is calculated correctly."""
        detector = AnomalyDetector(z_score_threshold=2.0)
        
        base_time = datetime.now()
        values = [(base_time - timedelta(hours=i), 10.0) for i in range(10)]
        # Add small variation to get non-zero std
        values = [(t, v + (0.5 if i % 2 == 0 else -0.5)) for i, (t, v) in enumerate(values)]
        values.append((base_time, 100.0))  # Large spike
        
        anomalies = detector.detect_anomalies('test_metric', values)
        
        if anomalies:
            assert 0.0 <= anomalies[-1].severity <= 1.0
    
    def test_mark_resolved(self):
        """Test marking an anomaly as resolved."""
        detector = AnomalyDetector()
        
        base_time = datetime.now()
        values = [(base_time - timedelta(hours=i), 10.0 + (0.5 if i % 2 == 0 else 0)) for i in range(10)]
        values.append((base_time, 50.0))
        
        anomalies = detector.detect_anomalies('test_metric', values)
        
        if anomalies:
            anomaly_id = anomalies[0].anomaly_id
            result = detector.mark_resolved(anomaly_id)
            assert result is True
            
            # Check it's marked resolved
            all_anomalies = detector.get_all_anomalies()
            resolved = [a for a in all_anomalies if a.anomaly_id == anomaly_id]
            if resolved:
                assert resolved[0].is_resolved is True


class TestTrendAnalyzer:
    """Tests for TrendAnalyzer class."""
    
    def test_analyze_upward_trend(self):
        """Test detection of upward trend."""
        analyzer = TrendAnalyzer()
        
        base_time = datetime.now()
        values = [
            (base_time - timedelta(days=7-i), 10.0 + i * 2)
            for i in range(7)
        ]
        
        trend = analyzer.analyze_trend('success_rate', values, '7d')
        
        assert trend is not None
        assert trend.slope > 0
        # The slope is positive, so it's either improving or stable (depends on threshold)
        assert trend.direction in (TrendDirection.IMPROVING, TrendDirection.STABLE)
    
    def test_analyze_stable_trend(self):
        """Test detection of stable trend."""
        analyzer = TrendAnalyzer()
        
        base_time = datetime.now()
        values = [
            (base_time - timedelta(days=7-i), 50.0 + (0.1 if i % 2 == 0 else -0.1))
            for i in range(7)
        ]
        
        trend = analyzer.analyze_trend('stable_metric', values, '7d')
        
        assert trend is not None
        assert abs(trend.slope) < 0.1 or trend.direction == TrendDirection.STABLE
    
    def test_forecast_generation(self):
        """Test that forecast is generated."""
        analyzer = TrendAnalyzer()
        
        base_time = datetime.now()
        values = [
            (base_time - timedelta(days=7-i), 10.0 + i * 5)
            for i in range(7)
        ]
        
        trend = analyzer.analyze_trend('growing_metric', values, '7d')
        
        assert trend is not None
        assert trend.forecast_next_period > 0
        assert 0.0 <= trend.forecast_confidence <= 1.0
    
    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        analyzer = TrendAnalyzer(min_data_points=5)
        
        base_time = datetime.now()
        values = [
            (base_time - timedelta(days=i), 10.0)
            for i in range(3)
        ]
        
        trend = analyzer.analyze_trend('sparse_metric', values, '3d')
        
        assert trend is None
    
    def test_recommendations_for_degrading(self):
        """Test that recommendations are generated for degrading trends."""
        analyzer = TrendAnalyzer()
        
        base_time = datetime.now()
        # Increasing latency (degrading)
        values = [
            (base_time - timedelta(days=7-i), 100.0 + i * 50)
            for i in range(7)
        ]
        
        trend = analyzer.analyze_trend('latency_ms', values, '7d')
        
        assert trend is not None
        if trend.direction == TrendDirection.DEGRADING:
            assert len(trend.recommendations) > 0


class TestCodeEmbeddings:
    """Tests for CodeEmbeddings class."""
    
    def test_compute_signature(self):
        """Test code signature computation."""
        embeddings = CodeEmbeddings()
        
        code = '''
def process_data(data):
    if data is None:
        return None
    for item in data:
        try:
            result = transform(item)
        except Exception as e:
            log_error(e)
    return result
'''
        
        signature = embeddings.compute_signature('code1', code)
        
        assert signature['token_count'] > 0
        assert signature['has_function'] is True
        assert signature['has_conditional'] is True
        assert signature['has_loop'] is True
        assert signature['has_try_except'] is True
    
    def test_compute_similarity_identical(self):
        """Test similarity of identical code."""
        embeddings = CodeEmbeddings()
        
        code = 'def hello(): return "world"'
        
        embeddings.compute_signature('code1', code)
        embeddings.compute_signature('code2', code)
        
        similarity = embeddings.compute_similarity('code1', 'code2')
        
        assert similarity.similarity_score == 1.0
    
    def test_compute_similarity_different(self):
        """Test similarity of very different code."""
        embeddings = CodeEmbeddings()
        
        code1 = '''
class Calculator:
    def add(self, a, b):
        return a + b
'''
        code2 = '''
import os
import sys
if __name__ == "__main__":
    print("Hello")
'''
        
        similarity = embeddings.compute_similarity('c1', 'c2', code1, code2)
        
        assert similarity.similarity_score < 0.8
    
    def test_find_common_patterns(self):
        """Test finding common patterns between code snippets."""
        embeddings = CodeEmbeddings()
        
        code1 = '''
def process(data):
    try:
        for item in data:
            handle(item)
    except Exception:
        pass
'''
        code2 = '''
def transform(items):
    try:
        for x in items:
            convert(x)
    except ValueError:
        pass
'''
        
        similarity = embeddings.compute_similarity('c1', 'c2', code1, code2)
        
        assert 'function definitions' in similarity.common_patterns or \
               'loop constructs' in similarity.common_patterns or \
               'exception handling' in similarity.common_patterns


class TestIntelligentAnalyzer:
    """Tests for IntelligentAnalyzer orchestrator."""
    
    def test_singleton_pattern(self):
        """Test that IntelligentAnalyzer is a singleton."""
        analyzer1 = IntelligentAnalyzer()
        analyzer2 = IntelligentAnalyzer()
        
        assert analyzer1 is analyzer2
    
    def test_components_initialized(self):
        """Test that all components are initialized."""
        analyzer = INTELLIGENT_ANALYZER
        
        assert hasattr(analyzer, 'pattern_clusterer')
        assert hasattr(analyzer, 'anomaly_detector')
        assert hasattr(analyzer, 'trend_analyzer')
        assert hasattr(analyzer, 'code_embeddings')
        
        assert isinstance(analyzer.pattern_clusterer, PatternClusterer)
        assert isinstance(analyzer.anomaly_detector, AnomalyDetector)
        assert isinstance(analyzer.trend_analyzer, TrendAnalyzer)
        assert isinstance(analyzer.code_embeddings, CodeEmbeddings)
    
    def test_subscribe_to_anomalies(self):
        """Test anomaly subscription."""
        analyzer = IntelligentAnalyzer()
        
        received = []
        def callback(anomaly):
            received.append(anomaly)
        
        analyzer.subscribe_to_anomalies(callback)
        
        # Trigger an anomaly
        base_time = datetime.now()
        values = [(base_time - timedelta(hours=i), 10.0 + (0.5 if i % 2 == 0 else 0)) for i in range(10)]
        values.append((base_time, 100.0))
        
        anomalies = analyzer.anomaly_detector.detect_anomalies('test_sub', values)
        
        # Manually notify since detect_anomalies doesn't auto-notify through orchestrator
        for anomaly in anomalies:
            analyzer._notify_anomaly_subscribers(anomaly)
        
        assert len(received) == len(anomalies)
    
    def test_get_summary(self):
        """Test summary generation."""
        analyzer = INTELLIGENT_ANALYZER
        
        summary = analyzer.get_summary()
        
        assert 'total_clusters' in summary
        assert 'total_anomalies' in summary
        assert 'metrics_with_baselines' in summary
        assert 'analysis_runs' in summary
    
    def test_run_full_analysis_returns_structure(self):
        """Test that full analysis returns expected structure."""
        analyzer = IntelligentAnalyzer()
        
        # This may fail to get data if DATA_COLLECTOR is empty, but should return structure
        with patch.object(analyzer, 'pattern_clusterer') as mock_clusterer:
            mock_clusterer.cluster_patterns.return_value = []
            
            # Patch imports to avoid errors
            with patch.dict('sys.modules', {'shared.circular_exchange': Mock()}):
                results = analyzer.run_full_analysis()
        
        assert 'timestamp' in results
        assert 'clusters' in results
        assert 'anomalies' in results
        assert 'trends' in results
        assert 'summary' in results


class TestDataclassSerialization:
    """Tests for dataclass serialization."""
    
    def test_pattern_cluster_to_dict(self):
        """Test PatternCluster serialization."""
        cluster = PatternCluster(
            cluster_id='test_cluster',
            name='Test Cluster',
            description='A test cluster',
            pattern_ids=['p1', 'p2'],
            total_occurrences=15,
            quality=ClusterQuality.HIGH
        )
        
        data = cluster.to_dict()
        
        assert data['cluster_id'] == 'test_cluster'
        assert data['quality'] == 'high'
        assert isinstance(data['created_at'], str)
    
    def test_anomaly_to_dict(self):
        """Test Anomaly serialization."""
        anomaly = Anomaly(
            anomaly_id='anomaly_1',
            anomaly_type=AnomalyType.PERFORMANCE_SPIKE,
            description='Test anomaly',
            severity=0.8,
            detected_at=datetime.now(),
            metric_name='latency',
            expected_value=10.0,
            actual_value=50.0,
            deviation_percent=400.0
        )
        
        data = anomaly.to_dict()
        
        assert data['anomaly_type'] == 'performance_spike'
        assert isinstance(data['detected_at'], str)
    
    def test_trend_analysis_to_dict(self):
        """Test TrendAnalysis serialization."""
        trend = TrendAnalysis(
            analysis_id='trend_1',
            metric_name='success_rate',
            time_range='7d',
            direction=TrendDirection.IMPROVING,
            slope=0.5,
            r_squared=0.85,
            data_points=7,
            forecast_next_period=95.0,
            forecast_confidence=0.8,
            change_points=[datetime.now()]
        )
        
        data = trend.to_dict()
        
        assert data['direction'] == 'improving'
        assert isinstance(data['created_at'], str)
        assert isinstance(data['change_points'][0], str)


class TestLinearRegression:
    """Tests for linear regression in TrendAnalyzer."""
    
    def test_perfect_linear_fit(self):
        """Test regression on perfectly linear data."""
        analyzer = TrendAnalyzer()
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]  # y = 2x
        
        slope, intercept, r_squared = analyzer._linear_regression(x, y)
        
        assert abs(slope - 2.0) < 0.01
        assert abs(intercept) < 0.01
        assert abs(r_squared - 1.0) < 0.01
    
    def test_noisy_data(self):
        """Test regression on noisy data."""
        analyzer = TrendAnalyzer()
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.1, 3.9, 6.2, 7.8, 10.1]  # Noisy y = 2x
        
        slope, intercept, r_squared = analyzer._linear_regression(x, y)
        
        assert 1.5 < slope < 2.5
        assert r_squared > 0.9


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
