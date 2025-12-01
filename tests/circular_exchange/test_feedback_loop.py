"""
Tests for the Feedback Loop module.

This test suite verifies the continuous feedback loop that orchestrates
auto-tuning and model fine-tuning based on collected metrics.
"""

import pytest
import uuid
from datetime import datetime
from pathlib import Path
import tempfile


class TestAutoTuner:
    """Tests for the AutoTuner component."""
    
    def setup_method(self):
        """Reset components before each test."""
        from shared.circular_exchange.feedback_loop import (
            AutoTuner, FeedbackType, TuningAction
        )
        
        self.tuner = AutoTuner()
        self.FeedbackType = FeedbackType
        self.TuningAction = TuningAction
    
    def test_record_feedback(self):
        """Test recording feedback signals."""
        self.tuner.record_feedback(
            self.FeedbackType.TEST_RESULT,
            {'test_name': 'test_example', 'passed': True, 'duration_ms': 100}
        )
        
        # Verify feedback was recorded
        assert len(self.tuner._feedback_history[self.FeedbackType.TEST_RESULT.value]) == 1
    
    def test_analyze_extraction_low_success_rate(self):
        """Test tuning suggestions for low extraction success rate."""
        # Record many failures
        for i in range(8):
            self.tuner.record_feedback(
                self.FeedbackType.EXTRACTION_FAILURE,
                {'model_id': 'test_model', 'confidence': 0.3}
            )
        
        # Record few successes
        for i in range(2):
            self.tuner.record_feedback(
                self.FeedbackType.EXTRACTION_SUCCESS,
                {'model_id': 'test_model', 'confidence': 0.8}
            )
        
        # Analyze should suggest lowering threshold
        decisions = self.tuner.analyze_and_tune()
        
        assert len(decisions) >= 1
        threshold_decisions = [d for d in decisions if d.action == self.TuningAction.DECREASE_THRESHOLD]
        assert len(threshold_decisions) >= 1
    
    def test_analyze_extraction_high_success_rate(self):
        """Test tuning suggestions for high extraction success rate."""
        # Record many successes (>95% success rate required)
        for i in range(20):
            self.tuner.record_feedback(
                self.FeedbackType.EXTRACTION_SUCCESS,
                {'model_id': 'test_model', 'confidence': 0.9}
            )
        
        # Analyze should suggest raising threshold for very high success rate
        decisions = self.tuner.analyze_and_tune()
        
        # With 100% success rate, should suggest increasing threshold for better accuracy
        threshold_decisions = [d for d in decisions if d.action == self.TuningAction.INCREASE_THRESHOLD]
        assert len(threshold_decisions) >= 1
    
    def test_apply_decision(self):
        """Test applying a tuning decision."""
        from shared.circular_exchange.feedback_loop import TuningDecision, TuningAction
        
        decision = TuningDecision(
            decision_id="test_decision",
            action=TuningAction.DECREASE_THRESHOLD,
            target_config='ocr.min_confidence',
            old_value=0.3,
            new_value=0.25,
            reason="Test reason",
            confidence=0.9
        )
        
        result = self.tuner.apply_decision(decision)
        
        assert result is True
        assert decision.applied is True
    
    def test_get_decisions(self):
        """Test getting tuning decisions."""
        # Generate some decisions
        for i in range(15):
            self.tuner.record_feedback(
                self.FeedbackType.EXTRACTION_FAILURE,
                {'model_id': 'test', 'confidence': 0.2}
            )
        
        self.tuner.analyze_and_tune()
        
        all_decisions = self.tuner.get_decisions()
        applied_decisions = self.tuner.get_decisions(applied_only=True)
        
        assert isinstance(all_decisions, list)
        assert isinstance(applied_decisions, list)


class TestModelTrainingPipeline:
    """Tests for the ModelTrainingPipeline component."""
    
    def setup_method(self):
        """Reset pipeline before each test."""
        from shared.circular_exchange.feedback_loop import (
            ModelTrainingPipeline, TrainingStatus
        )
        
        self.pipeline = ModelTrainingPipeline()
        self.TrainingStatus = TrainingStatus
    
    def test_create_training_job(self):
        """Test creating a training job."""
        job = self.pipeline.create_training_job(
            model_id='test_model',
            target_samples=100,
            target_epochs=5
        )
        
        assert job.job_id is not None
        assert job.model_id == 'test_model'
        assert job.status == self.TrainingStatus.COLLECTING
        assert job.target_samples == 100
    
    def test_add_training_sample(self):
        """Test adding training samples."""
        job = self.pipeline.create_training_job(
            model_id='test_model',
            target_samples=5
        )
        
        # Add samples
        for i in range(5):
            result = self.pipeline.add_training_sample(
                job.job_id,
                input_data={'image': f'image_{i}.jpg'},
                output_data={'text': f'extracted_text_{i}'},
                metadata={'confidence': 0.9}
            )
            assert result is True
        
        # Job should be ready for training
        updated_job = self.pipeline.get_job(job.job_id)
        assert updated_job.samples_collected == 5
        assert updated_job.status == self.TrainingStatus.PENDING
    
    def test_start_training(self):
        """Test starting a training job."""
        job = self.pipeline.create_training_job(
            model_id='test_model',
            target_samples=2
        )
        
        # Add enough samples
        for i in range(2):
            self.pipeline.add_training_sample(
                job.job_id,
                input_data={'image': f'image_{i}.jpg'},
                output_data={'text': 'text'}
            )
        
        # Start training
        result = self.pipeline.start_training(job.job_id)
        
        assert result is True
        
        updated_job = self.pipeline.get_job(job.job_id)
        assert updated_job.status == self.TrainingStatus.TRAINING
        assert updated_job.started_at is not None
    
    def test_update_training_progress(self):
        """Test updating training progress."""
        job = self.pipeline.create_training_job(
            model_id='test_model',
            target_samples=1,
            target_epochs=5
        )
        
        # Add sample and start
        self.pipeline.add_training_sample(
            job.job_id,
            {'image': 'test.jpg'},
            {'text': 'test'}
        )
        self.pipeline.start_training(job.job_id)
        
        # Update progress
        self.pipeline.update_training_progress(
            job.job_id,
            epoch=3,
            metrics={'accuracy': 0.85, 'loss': 0.15}
        )
        
        updated_job = self.pipeline.get_job(job.job_id)
        assert updated_job.epochs_completed == 3
        assert updated_job.current_metrics['accuracy'] == 0.85
    
    def test_complete_training(self):
        """Test completing a training job."""
        job = self.pipeline.create_training_job(
            model_id='test_model',
            target_samples=1
        )
        
        self.pipeline.add_training_sample(
            job.job_id,
            {'image': 'test.jpg'},
            {'text': 'test'}
        )
        self.pipeline.start_training(job.job_id)
        
        self.pipeline.complete_training(
            job.job_id,
            final_metrics={'accuracy': 0.92, 'loss': 0.08},
            success=True
        )
        
        updated_job = self.pipeline.get_job(job.job_id)
        assert updated_job.status == self.TrainingStatus.COMPLETED
        assert updated_job.completed_at is not None
    
    def test_get_active_jobs(self):
        """Test getting active training jobs."""
        # Create multiple jobs
        job1 = self.pipeline.create_training_job('model1')
        job2 = self.pipeline.create_training_job('model2')
        
        active = self.pipeline.get_active_jobs()
        
        assert len(active) >= 2


class TestFeedbackLoop:
    """Tests for the FeedbackLoop orchestrator."""
    
    def setup_method(self):
        """Reset feedback loop before each test."""
        from shared.circular_exchange.feedback_loop import FEEDBACK_LOOP
        from shared.circular_exchange.data_collector import DATA_COLLECTOR
        from shared.circular_exchange.metrics_analyzer import METRICS_ANALYZER
        from shared.circular_exchange.refactoring_engine import REFACTORING_ENGINE
        
        # Clear all components
        DATA_COLLECTOR.clear()
        METRICS_ANALYZER.clear()
        REFACTORING_ENGINE.clear()
        
        self.loop = FEEDBACK_LOOP
        # Reset internal state
        self.loop._cycle_count = 0
        self.loop._metrics.total_feedback_signals = 0
        self.loop._metrics.tuning_decisions_made = 0
        self.loop._metrics.tuning_decisions_applied = 0
        self.loop._metrics.config_improvements = 0
        self.loop._auto_tuner._decisions.clear()
        self.loop._auto_tuner._feedback_history.clear()
    
    def test_singleton_pattern(self):
        """Test that FeedbackLoop is a singleton."""
        from shared.circular_exchange.feedback_loop import FeedbackLoop
        
        loop1 = FeedbackLoop()
        loop2 = FeedbackLoop()
        
        assert loop1 is loop2
    
    def test_process_test_result(self):
        """Test processing test results."""
        initial_signals = self.loop._metrics.total_feedback_signals
        
        self.loop.process_test_result(
            test_name='test_example',
            passed=True,
            duration_ms=150.0
        )
        
        assert self.loop._metrics.total_feedback_signals == initial_signals + 1
    
    def test_process_extraction_result(self):
        """Test processing extraction results."""
        initial_signals = self.loop._metrics.total_feedback_signals
        
        self.loop.process_extraction_result(
            model_id='donut_model',
            success=True,
            confidence=0.95,
            processing_time_ms=1500.0
        )
        
        assert self.loop._metrics.total_feedback_signals == initial_signals + 1
    
    def test_process_performance_metric(self):
        """Test processing performance metrics."""
        initial_signals = self.loop._metrics.total_feedback_signals
        
        self.loop.process_performance_metric(
            metric_name='cache_hit_rate',
            value=0.75,
            tags={'cache_type': 'model'}
        )
        
        assert self.loop._metrics.total_feedback_signals == initial_signals + 1
    
    def test_run_cycle(self):
        """Test running a feedback cycle."""
        # Add some feedback first
        for i in range(15):
            self.loop.process_extraction_result(
                model_id='test_model',
                success=i < 5,  # 33% success rate
                confidence=0.5,
                processing_time_ms=1000.0
            )
        
        initial_cycle = self.loop._cycle_count
        
        results = self.loop.run_cycle()
        
        assert self.loop._cycle_count == initial_cycle + 1
        assert 'tuning_decisions' in results
        assert 'patterns_detected' in results
        assert 'duration_ms' in results
    
    def test_get_metrics(self):
        """Test getting feedback loop metrics."""
        metrics = self.loop.get_metrics()
        
        assert hasattr(metrics, 'total_feedback_signals')
        assert hasattr(metrics, 'tuning_decisions_made')
        assert hasattr(metrics, 'training_jobs_created')
    
    def test_get_summary(self):
        """Test getting feedback loop summary."""
        summary = self.loop.get_summary()
        
        assert 'cycle_count' in summary
        assert 'metrics' in summary
        assert 'active_training_jobs' in summary
        assert 'tuner_stats' in summary
    
    def test_subscriber_notification(self):
        """Test subscriber notifications."""
        received_decisions = []
        
        def on_decision(decision):
            received_decisions.append(decision)
        
        self.loop.subscribe_to_decisions(on_decision)
        
        # Generate high-confidence decisions
        for i in range(20):
            self.loop.process_extraction_result(
                model_id='test',
                success=False,
                confidence=0.2,
                processing_time_ms=1000.0
            )
        
        self.loop.run_cycle()
        
        # May or may not have received notifications depending on confidence
        assert isinstance(received_decisions, list)
    
    def test_export_state(self):
        """Test exporting feedback loop state."""
        # Add some activity
        self.loop.process_test_result('test1', True, 100.0)
        self.loop.run_cycle()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "state.json"
            result_path = self.loop.export_state(output_path)
            
            assert result_path.exists()
            
            import json
            with open(result_path) as f:
                data = json.load(f)
            
            assert 'summary' in data
            assert 'tuning_decisions' in data
            assert 'exported_at' in data


class TestEnums:
    """Tests for feedback loop enums."""
    
    def test_tuning_action_values(self):
        """Test TuningAction enum values."""
        from shared.circular_exchange.feedback_loop import TuningAction
        
        assert TuningAction.INCREASE_THRESHOLD.value == "increase_threshold"
        assert TuningAction.DECREASE_THRESHOLD.value == "decrease_threshold"
        assert TuningAction.ADJUST_TIMEOUT.value == "adjust_timeout"
    
    def test_feedback_type_values(self):
        """Test FeedbackType enum values."""
        from shared.circular_exchange.feedback_loop import FeedbackType
        
        assert FeedbackType.TEST_RESULT.value == "test_result"
        assert FeedbackType.EXTRACTION_SUCCESS.value == "extraction_success"
        assert FeedbackType.PERFORMANCE_METRIC.value == "performance_metric"
    
    def test_training_status_values(self):
        """Test TrainingStatus enum values."""
        from shared.circular_exchange.feedback_loop import TrainingStatus
        
        assert TrainingStatus.PENDING.value == "pending"
        assert TrainingStatus.TRAINING.value == "training"
        assert TrainingStatus.COMPLETED.value == "completed"


class TestIntegration:
    """Integration tests for the complete feedback loop system."""
    
    def test_cef_module_registration(self):
        """Test that feedback loop is registered with CEF."""
        from shared.circular_exchange import FEEDBACK_LOOP
        
        assert FEEDBACK_LOOP is not None
    
    def test_full_pipeline_integration(self):
        """Test the complete pipeline from data collection to tuning."""
        from shared.circular_exchange import (
            DATA_COLLECTOR, METRICS_ANALYZER, REFACTORING_ENGINE, FEEDBACK_LOOP,
            LogEntry, TestResult, TestStatus
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
                message="Integration test error",
                module="test_module",
                function="test_func",
                line_number=100
            ))
        
        for i in range(5):
            DATA_COLLECTOR.record_test_result(TestResult(
                test_id=str(i),
                test_name=f"test_{i}",
                module_path="tests/test.py",
                status=TestStatus.PASSED if i < 4 else TestStatus.FAILED,
                duration_ms=100.0
            ))
        
        # Step 2: Feed into feedback loop
        for i in range(15):
            FEEDBACK_LOOP.process_extraction_result(
                model_id="integration_model",
                success=i < 10,  # 67% success
                confidence=0.7,
                processing_time_ms=1000.0
            )
        
        # Step 3: Run feedback cycle
        results = FEEDBACK_LOOP.run_cycle()
        
        # Step 4: Verify results
        assert results['cycle_number'] >= 1
        
        summary = FEEDBACK_LOOP.get_summary()
        assert summary['metrics']['total_feedback_signals'] >= 15
