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
