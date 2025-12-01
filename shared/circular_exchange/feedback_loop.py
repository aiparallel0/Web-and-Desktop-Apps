"""
=============================================================================
FEEDBACK LOOP - Continuous Auto-Tuning and Model Fine-Tuning Pipeline
=============================================================================

This module implements the continuous feedback loop that:
- Connects test results to configuration auto-tuning
- Feeds extraction events to model fine-tuning pipelines
- Provides real-time system optimization based on collected metrics
- Orchestrates the entire continuous improvement pipeline

Circular Exchange Framework Integration:
-----------------------------------------
Module ID: shared.circular_exchange.feedback_loop
Description: Continuous feedback loop for auto-tuning and model fine-tuning
Dependencies: [shared.circular_exchange.data_collector, shared.circular_exchange.metrics_analyzer, 
               shared.circular_exchange.refactoring_engine]
Exports: [FeedbackLoop, AutoTuner, ModelTrainingPipeline, FEEDBACK_LOOP]

=============================================================================
"""

import logging
import threading
import json
import os
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class TuningAction(Enum):
    """Types of auto-tuning actions."""
    INCREASE_THRESHOLD = "increase_threshold"
    DECREASE_THRESHOLD = "decrease_threshold"
    ENABLE_FEATURE = "enable_feature"
    DISABLE_FEATURE = "disable_feature"
    ADJUST_TIMEOUT = "adjust_timeout"
    ADJUST_BATCH_SIZE = "adjust_batch_size"
    ADJUST_CACHE_SIZE = "adjust_cache_size"
    RETRY_CONFIGURATION = "retry_configuration"


class FeedbackType(Enum):
    """Types of feedback signals."""
    TEST_RESULT = "test_result"
    EXTRACTION_SUCCESS = "extraction_success"
    EXTRACTION_FAILURE = "extraction_failure"
    PERFORMANCE_METRIC = "performance_metric"
    USER_FEEDBACK = "user_feedback"
    ERROR_RATE = "error_rate"


class TrainingStatus(Enum):
    """Status of a model training job."""
    PENDING = "pending"
    COLLECTING = "collecting"
    TRAINING = "training"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TuningDecision:
    """Represents an auto-tuning decision made by the feedback loop."""
    decision_id: str
    action: TuningAction
    target_config: str  # Configuration key to tune
    old_value: Any
    new_value: Any
    reason: str
    confidence: float  # 0.0 to 1.0
    feedback_signals: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    applied: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['action'] = self.action.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class TrainingJob:
    """Represents a model training/fine-tuning job."""
    job_id: str
    model_id: str
    status: TrainingStatus
    training_data_path: Optional[Path] = None
    samples_collected: int = 0
    target_samples: int = 1000
    epochs_completed: int = 0
    target_epochs: int = 10
    current_metrics: Dict[str, float] = field(default_factory=dict)
    best_metrics: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        data['training_data_path'] = str(self.training_data_path) if self.training_data_path else None
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data


@dataclass
class FeedbackMetrics:
    """Aggregated metrics from the feedback loop."""
    total_feedback_signals: int = 0
    tuning_decisions_made: int = 0
    tuning_decisions_applied: int = 0
    training_jobs_created: int = 0
    training_jobs_completed: int = 0
    config_improvements: int = 0
    last_tuning_cycle: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['last_tuning_cycle'] = self.last_tuning_cycle.isoformat() if self.last_tuning_cycle else None
        return data


class AutoTuner:
    """
    Automatic configuration tuning based on feedback signals.
    
    The AutoTuner analyzes incoming feedback (test results, extraction events,
    performance metrics) and automatically adjusts configuration parameters
    to optimize system performance.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._decisions: List[TuningDecision] = []
        self._feedback_history: Dict[str, List[Any]] = defaultdict(list)
        
        # Tuning thresholds
        self._min_samples_for_tuning = 10
        self._confidence_threshold = 0.7
        self._max_history_per_signal = 100
        
        # Configuration bounds
        self._config_bounds: Dict[str, Dict[str, Any]] = {
            'ocr.min_confidence': {'min': 0.1, 'max': 0.9, 'step': 0.05},
            'ocr.timeout_seconds': {'min': 10, 'max': 120, 'step': 5},
            'model.batch_size': {'min': 1, 'max': 32, 'step': 4},
            'cache.max_size': {'min': 100, 'max': 10000, 'step': 100},
            'retry.max_attempts': {'min': 1, 'max': 5, 'step': 1},
        }
    
    def record_feedback(self, feedback_type: FeedbackType, data: Dict[str, Any]) -> None:
        """Record a feedback signal for analysis."""
        with self._lock:
            key = feedback_type.value
            self._feedback_history[key].append({
                'timestamp': datetime.now().isoformat(),
                'data': data
            })
            
            # Trim history
            if len(self._feedback_history[key]) > self._max_history_per_signal:
                self._feedback_history[key] = self._feedback_history[key][-self._max_history_per_signal:]
    
    def analyze_and_tune(self) -> List[TuningDecision]:
        """
        Analyze feedback signals and generate tuning decisions.
        
        Returns:
            List of tuning decisions
        """
        decisions = []
        
        with self._lock:
            # Analyze extraction success rate
            extraction_decisions = self._analyze_extraction_feedback()
            decisions.extend(extraction_decisions)
            
            # Analyze test results
            test_decisions = self._analyze_test_feedback()
            decisions.extend(test_decisions)
            
            # Analyze performance metrics
            perf_decisions = self._analyze_performance_feedback()
            decisions.extend(perf_decisions)
            
            self._decisions.extend(decisions)
        
        return decisions
    
    def _analyze_extraction_feedback(self) -> List[TuningDecision]:
        """Analyze extraction feedback and suggest confidence tuning."""
        decisions = []
        
        success_signals = self._feedback_history.get(FeedbackType.EXTRACTION_SUCCESS.value, [])
        failure_signals = self._feedback_history.get(FeedbackType.EXTRACTION_FAILURE.value, [])
        
        total = len(success_signals) + len(failure_signals)
        if total < self._min_samples_for_tuning:
            return decisions
        
        success_rate = len(success_signals) / total
        
        # If success rate is low, consider lowering confidence threshold
        if success_rate < 0.7:
            decisions.append(TuningDecision(
                decision_id=f"tune_{datetime.now().strftime('%Y%m%d%H%M%S')}_conf",
                action=TuningAction.DECREASE_THRESHOLD,
                target_config='ocr.min_confidence',
                old_value=0.3,  # Current value (would be fetched from config)
                new_value=0.25,
                reason=f"Low extraction success rate ({success_rate:.1%}). Lowering confidence threshold may help.",
                confidence=min(success_rate + 0.3, 1.0),
                feedback_signals=[FeedbackType.EXTRACTION_SUCCESS.value, FeedbackType.EXTRACTION_FAILURE.value]
            ))
        
        # If success rate is very high, consider raising confidence for better accuracy
        elif success_rate > 0.95:
            decisions.append(TuningDecision(
                decision_id=f"tune_{datetime.now().strftime('%Y%m%d%H%M%S')}_conf_up",
                action=TuningAction.INCREASE_THRESHOLD,
                target_config='ocr.min_confidence',
                old_value=0.3,
                new_value=0.35,
                reason=f"High extraction success rate ({success_rate:.1%}). Raising confidence threshold for better accuracy.",
                confidence=success_rate,
                feedback_signals=[FeedbackType.EXTRACTION_SUCCESS.value]
            ))
        
        return decisions
    
    def _analyze_test_feedback(self) -> List[TuningDecision]:
        """Analyze test feedback and suggest improvements."""
        decisions = []
        
        test_signals = self._feedback_history.get(FeedbackType.TEST_RESULT.value, [])
        
        if len(test_signals) < self._min_samples_for_tuning:
            return decisions
        
        # Analyze test durations
        durations = [s['data'].get('duration_ms', 0) for s in test_signals]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # If tests are consistently slow, suggest timeout adjustment
        if avg_duration > 5000:  # 5 seconds
            decisions.append(TuningDecision(
                decision_id=f"tune_{datetime.now().strftime('%Y%m%d%H%M%S')}_timeout",
                action=TuningAction.ADJUST_TIMEOUT,
                target_config='test.timeout_seconds',
                old_value=30,
                new_value=60,
                reason=f"Average test duration ({avg_duration:.0f}ms) suggests longer timeouts needed.",
                confidence=0.8,
                feedback_signals=[FeedbackType.TEST_RESULT.value]
            ))
        
        return decisions
    
    def _analyze_performance_feedback(self) -> List[TuningDecision]:
        """Analyze performance feedback and suggest optimizations."""
        decisions = []
        
        perf_signals = self._feedback_history.get(FeedbackType.PERFORMANCE_METRIC.value, [])
        
        if len(perf_signals) < self._min_samples_for_tuning:
            return decisions
        
        # Analyze cache hit rates if available
        cache_hits = [s['data'].get('cache_hit_rate', 0) for s in perf_signals if 'cache_hit_rate' in s['data']]
        if cache_hits:
            avg_hit_rate = sum(cache_hits) / len(cache_hits)
            
            if avg_hit_rate < 0.5:
                decisions.append(TuningDecision(
                    decision_id=f"tune_{datetime.now().strftime('%Y%m%d%H%M%S')}_cache",
                    action=TuningAction.ADJUST_CACHE_SIZE,
                    target_config='cache.max_size',
                    old_value=1000,
                    new_value=2000,
                    reason=f"Low cache hit rate ({avg_hit_rate:.1%}). Increasing cache size.",
                    confidence=0.75,
                    feedback_signals=[FeedbackType.PERFORMANCE_METRIC.value]
                ))
        
        return decisions
    
    def apply_decision(self, decision: TuningDecision) -> bool:
        """
        Apply a tuning decision to the configuration.
        
        Args:
            decision: The tuning decision to apply
            
        Returns:
            True if successfully applied
        """
        try:
            # In a real implementation, this would update PROJECT_CONFIG
            # For now, we mark it as applied
            with self._lock:
                decision.applied = True
                logger.info(
                    "Applied tuning decision: %s -> %s = %s (was %s)",
                    decision.action.value,
                    decision.target_config,
                    decision.new_value,
                    decision.old_value
                )
            return True
        except Exception as e:
            logger.error("Failed to apply tuning decision: %s", e)
            return False
    
    def get_decisions(self, applied_only: bool = False) -> List[TuningDecision]:
        """Get tuning decisions."""
        with self._lock:
            if applied_only:
                return [d for d in self._decisions if d.applied]
            return list(self._decisions)


class ModelTrainingPipeline:
    """
    Pipeline for continuous model fine-tuning based on collected data.
    
    This class manages:
    - Training data collection from extraction events
    - Training job creation and monitoring
    - Model performance tracking
    - Automatic retraining triggers
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._jobs: Dict[str, TrainingJob] = {}
        self._data_dir = Path(os.getenv('TRAINING_DATA_DIR', 'data/training'))
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        # Training thresholds
        self._min_samples_for_training = 100
        self._retrain_on_accuracy_drop = 0.05  # 5% accuracy drop triggers retrain
    
    def create_training_job(
        self,
        model_id: str,
        target_samples: int = 1000,
        target_epochs: int = 10
    ) -> TrainingJob:
        """
        Create a new training job for a model.
        
        Args:
            model_id: ID of the model to train
            target_samples: Target number of training samples
            target_epochs: Target number of training epochs
            
        Returns:
            Created TrainingJob
        """
        job_id = f"train_{model_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        job = TrainingJob(
            job_id=job_id,
            model_id=model_id,
            status=TrainingStatus.COLLECTING,
            training_data_path=self._data_dir / f"{job_id}.jsonl",
            target_samples=target_samples,
            target_epochs=target_epochs
        )
        
        with self._lock:
            self._jobs[job_id] = job
        
        logger.info("Created training job %s for model %s", job_id, model_id)
        return job
    
    def add_training_sample(
        self,
        job_id: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a training sample to a job.
        
        Args:
            job_id: ID of the training job
            input_data: Input data for the sample
            output_data: Expected output (ground truth)
            metadata: Optional metadata
            
        Returns:
            True if sample was added
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.status != TrainingStatus.COLLECTING:
                return False
            
            # Write sample to training data file
            sample = {
                'input': input_data,
                'output': output_data,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat()
            }
            
            with open(job.training_data_path, 'a') as f:
                f.write(json.dumps(sample) + '\n')
            
            job.samples_collected += 1
            
            # Check if we have enough samples to start training
            if job.samples_collected >= job.target_samples:
                job.status = TrainingStatus.PENDING
                logger.info("Job %s has enough samples, ready for training", job_id)
            
            return True
    
    def start_training(self, job_id: str) -> bool:
        """
        Start the training process for a job.
        
        Args:
            job_id: ID of the training job
            
        Returns:
            True if training started
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.status != TrainingStatus.PENDING:
                return False
            
            job.status = TrainingStatus.TRAINING
            job.started_at = datetime.now()
            
            # In a real implementation, this would trigger actual model training
            # For now, we simulate by updating status
            logger.info("Started training for job %s with %d samples", 
                       job_id, job.samples_collected)
            
            return True
    
    def update_training_progress(
        self,
        job_id: str,
        epoch: int,
        metrics: Dict[str, float]
    ) -> None:
        """
        Update training progress for a job.
        
        Args:
            job_id: ID of the training job
            epoch: Current epoch number
            metrics: Current training metrics
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            
            job.epochs_completed = epoch
            job.current_metrics = metrics
            
            # Track best metrics
            if 'accuracy' in metrics:
                if 'accuracy' not in job.best_metrics or metrics['accuracy'] > job.best_metrics['accuracy']:
                    job.best_metrics = metrics.copy()
            
            # Check if training is complete
            if epoch >= job.target_epochs:
                job.status = TrainingStatus.EVALUATING
    
    def complete_training(
        self,
        job_id: str,
        final_metrics: Dict[str, float],
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Mark training as complete.
        
        Args:
            job_id: ID of the training job
            final_metrics: Final training metrics
            success: Whether training was successful
            error_message: Error message if failed
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            
            job.completed_at = datetime.now()
            job.current_metrics = final_metrics
            
            if success:
                job.status = TrainingStatus.COMPLETED
                logger.info("Training completed for job %s: %s", job_id, final_metrics)
            else:
                job.status = TrainingStatus.FAILED
                job.error_message = error_message
                logger.error("Training failed for job %s: %s", job_id, error_message)
    
    def get_job(self, job_id: str) -> Optional[TrainingJob]:
        """Get a training job by ID."""
        with self._lock:
            return self._jobs.get(job_id)
    
    def get_active_jobs(self) -> List[TrainingJob]:
        """Get all active training jobs."""
        with self._lock:
            return [
                job for job in self._jobs.values()
                if job.status in (TrainingStatus.COLLECTING, TrainingStatus.PENDING, 
                                 TrainingStatus.TRAINING, TrainingStatus.EVALUATING)
            ]
    
    def get_completed_jobs(self, model_id: Optional[str] = None) -> List[TrainingJob]:
        """Get completed training jobs, optionally filtered by model."""
        with self._lock:
            jobs = [job for job in self._jobs.values() if job.status == TrainingStatus.COMPLETED]
            if model_id:
                jobs = [job for job in jobs if job.model_id == model_id]
            return jobs


class FeedbackLoop:
    """
    Main orchestrator for the continuous feedback loop.
    
    This singleton coordinates:
    - Data collection from all sources
    - Metrics analysis for pattern detection
    - Refactoring suggestions
    - Auto-tuning based on feedback
    - Model fine-tuning pipeline
    
    The feedback loop runs continuously, analyzing incoming data
    and making adjustments to optimize system performance.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global feedback loop."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the feedback loop."""
        if self._initialized:
            return
        
        self._lock = threading.RLock()
        
        # Components
        self._auto_tuner = AutoTuner()
        self._training_pipeline = ModelTrainingPipeline()
        
        # References to other CEF components
        self._data_collector = None
        self._metrics_analyzer = None
        self._refactoring_engine = None
        
        # State
        self._running = False
        self._cycle_count = 0
        self._metrics = FeedbackMetrics()
        
        # Subscribers
        self._decision_subscribers: List[Callable] = []
        self._training_subscribers: List[Callable] = []
        
        self._initialized = True
        logger.info("FeedbackLoop initialized")
    
    def _get_data_collector(self):
        """Lazy-load the data collector."""
        if self._data_collector is None:
            try:
                from shared.circular_exchange.data_collector import DATA_COLLECTOR
                self._data_collector = DATA_COLLECTOR
            except ImportError:
                logger.warning("Could not import DATA_COLLECTOR")
        return self._data_collector
    
    def _get_metrics_analyzer(self):
        """Lazy-load the metrics analyzer."""
        if self._metrics_analyzer is None:
            try:
                from shared.circular_exchange.metrics_analyzer import METRICS_ANALYZER
                self._metrics_analyzer = METRICS_ANALYZER
            except ImportError:
                logger.warning("Could not import METRICS_ANALYZER")
        return self._metrics_analyzer
    
    def _get_refactoring_engine(self):
        """Lazy-load the refactoring engine."""
        if self._refactoring_engine is None:
            try:
                from shared.circular_exchange.refactoring_engine import REFACTORING_ENGINE
                self._refactoring_engine = REFACTORING_ENGINE
            except ImportError:
                logger.warning("Could not import REFACTORING_ENGINE")
        return self._refactoring_engine
    
    @property
    def auto_tuner(self) -> AutoTuner:
        """Get the auto-tuner component."""
        return self._auto_tuner
    
    @property
    def training_pipeline(self) -> ModelTrainingPipeline:
        """Get the training pipeline component."""
        return self._training_pipeline
    
    # =========================================================================
    # FEEDBACK PROCESSING
    # =========================================================================
    
    def process_test_result(self, test_name: str, passed: bool, duration_ms: float) -> None:
        """
        Process a test result and feed it into the loop.
        
        Args:
            test_name: Name of the test
            passed: Whether the test passed
            duration_ms: Test duration in milliseconds
        """
        with self._lock:
            self._metrics.total_feedback_signals += 1
        
        self._auto_tuner.record_feedback(
            FeedbackType.TEST_RESULT,
            {
                'test_name': test_name,
                'passed': passed,
                'duration_ms': duration_ms,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def process_extraction_result(
        self,
        model_id: str,
        success: bool,
        confidence: float,
        processing_time_ms: float,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Process an extraction result and feed it into the loop.
        
        Args:
            model_id: ID of the model used
            success: Whether extraction was successful
            confidence: Confidence score
            processing_time_ms: Processing time in milliseconds
            input_data: Optional input data for training
            output_data: Optional output data (ground truth) for training
        """
        with self._lock:
            self._metrics.total_feedback_signals += 1
        
        feedback_type = FeedbackType.EXTRACTION_SUCCESS if success else FeedbackType.EXTRACTION_FAILURE
        
        self._auto_tuner.record_feedback(
            feedback_type,
            {
                'model_id': model_id,
                'confidence': confidence,
                'processing_time_ms': processing_time_ms,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Add to training pipeline if we have labeled data
        if input_data and output_data:
            active_jobs = self._training_pipeline.get_active_jobs()
            for job in active_jobs:
                if job.model_id == model_id and job.status == TrainingStatus.COLLECTING:
                    self._training_pipeline.add_training_sample(
                        job.job_id,
                        input_data,
                        output_data,
                        {'confidence': confidence, 'processing_time_ms': processing_time_ms}
                    )
    
    def process_performance_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Process a performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags
        """
        with self._lock:
            self._metrics.total_feedback_signals += 1
        
        self._auto_tuner.record_feedback(
            FeedbackType.PERFORMANCE_METRIC,
            {
                'metric_name': metric_name,
                'value': value,
                'tags': tags or {},
                'timestamp': datetime.now().isoformat()
            }
        )
    
    # =========================================================================
    # FEEDBACK CYCLE
    # =========================================================================
    
    def run_cycle(self) -> Dict[str, Any]:
        """
        Run a single feedback cycle.
        
        This method:
        1. Analyzes collected data
        2. Generates tuning decisions
        3. Applies approved decisions
        4. Generates refactoring suggestions
        5. Updates training jobs
        
        Returns:
            Summary of the cycle results
        """
        cycle_start = datetime.now()
        
        with self._lock:
            self._cycle_count += 1
            self._metrics.last_tuning_cycle = cycle_start
        
        results = {
            'cycle_number': self._cycle_count,
            'tuning_decisions': [],
            'training_updates': [],
            'refactoring_suggestions': 0,
            'patterns_detected': 0
        }
        
        # Step 1: Analyze and generate tuning decisions
        tuning_decisions = self._auto_tuner.analyze_and_tune()
        results['tuning_decisions'] = [d.to_dict() for d in tuning_decisions]
        
        with self._lock:
            self._metrics.tuning_decisions_made += len(tuning_decisions)
        
        # Apply high-confidence decisions automatically
        for decision in tuning_decisions:
            if decision.confidence >= 0.8:
                if self._auto_tuner.apply_decision(decision):
                    with self._lock:
                        self._metrics.tuning_decisions_applied += 1
                        self._metrics.config_improvements += 1
                    self._notify_decision_subscribers(decision)
        
        # Step 2: Run metrics analysis
        analyzer = self._get_metrics_analyzer()
        if analyzer:
            patterns = analyzer.analyze_error_patterns()
            results['patterns_detected'] = len(patterns)
            
            # Generate test health report
            analyzer.analyze_test_health()
        
        # Step 3: Generate refactoring suggestions
        engine = self._get_refactoring_engine()
        if engine:
            suggestions = engine.generate_comprehensive_plan()
            results['refactoring_suggestions'] = len(suggestions.suggestions)
        
        # Step 4: Check training jobs
        active_jobs = self._training_pipeline.get_active_jobs()
        for job in active_jobs:
            if job.status == TrainingStatus.PENDING:
                self._training_pipeline.start_training(job.job_id)
                self._notify_training_subscribers(job)
                results['training_updates'].append({
                    'job_id': job.job_id,
                    'action': 'started'
                })
        
        results['duration_ms'] = (datetime.now() - cycle_start).total_seconds() * 1000
        
        logger.info(
            "Feedback cycle %d completed: %d decisions, %d patterns, %d suggestions",
            self._cycle_count,
            len(tuning_decisions),
            results['patterns_detected'],
            results['refactoring_suggestions']
        )
        
        return results
    
    # =========================================================================
    # SUBSCRIPTION MANAGEMENT
    # =========================================================================
    
    def subscribe_to_decisions(self, callback: Callable) -> None:
        """Subscribe to tuning decision notifications."""
        with self._lock:
            if callback not in self._decision_subscribers:
                self._decision_subscribers.append(callback)
    
    def subscribe_to_training(self, callback: Callable) -> None:
        """Subscribe to training job notifications."""
        with self._lock:
            if callback not in self._training_subscribers:
                self._training_subscribers.append(callback)
    
    def _notify_decision_subscribers(self, decision: TuningDecision) -> None:
        """Notify subscribers of a tuning decision."""
        for callback in self._decision_subscribers:
            try:
                callback(decision)
            except Exception as e:
                logger.error("Error notifying decision subscriber: %s", e)
    
    def _notify_training_subscribers(self, job: TrainingJob) -> None:
        """Notify subscribers of a training update."""
        for callback in self._training_subscribers:
            try:
                callback(job)
            except Exception as e:
                logger.error("Error notifying training subscriber: %s", e)
    
    # =========================================================================
    # REPORTING
    # =========================================================================
    
    def get_metrics(self) -> FeedbackMetrics:
        """Get current feedback loop metrics."""
        with self._lock:
            return FeedbackMetrics(
                total_feedback_signals=self._metrics.total_feedback_signals,
                tuning_decisions_made=self._metrics.tuning_decisions_made,
                tuning_decisions_applied=self._metrics.tuning_decisions_applied,
                training_jobs_created=len(self._training_pipeline._jobs),
                training_jobs_completed=len(self._training_pipeline.get_completed_jobs()),
                config_improvements=self._metrics.config_improvements,
                last_tuning_cycle=self._metrics.last_tuning_cycle
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the feedback loop state."""
        metrics = self.get_metrics()
        
        return {
            'cycle_count': self._cycle_count,
            'metrics': metrics.to_dict(),
            'active_training_jobs': len(self._training_pipeline.get_active_jobs()),
            'pending_decisions': len([d for d in self._auto_tuner.get_decisions() if not d.applied]),
            'tuner_stats': {
                'total_decisions': len(self._auto_tuner.get_decisions()),
                'applied_decisions': len(self._auto_tuner.get_decisions(applied_only=True))
            }
        }
    
    def export_state(self, output_path: Optional[Path] = None) -> Path:
        """
        Export the complete feedback loop state.
        
        Args:
            output_path: Optional output path
            
        Returns:
            Path to the exported file
        """
        if output_path is None:
            output_path = Path("data/feedback_loop_state.json")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            'exported_at': datetime.now().isoformat(),
            'summary': self.get_summary(),
            'tuning_decisions': [d.to_dict() for d in self._auto_tuner.get_decisions()],
            'training_jobs': [j.to_dict() for j in self._training_pipeline._jobs.values()]
        }
        
        with open(output_path, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info("Exported feedback loop state to %s", output_path)
        return output_path


# Global singleton instance
FEEDBACK_LOOP = FeedbackLoop()


# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.circular_exchange.feedback_loop",
            file_path=__file__,
            description="Continuous feedback loop for auto-tuning and model fine-tuning",
            dependencies=[
                "shared.circular_exchange.data_collector",
                "shared.circular_exchange.metrics_analyzer",
                "shared.circular_exchange.refactoring_engine"
            ],
            exports=[
                "FeedbackLoop", "AutoTuner", "ModelTrainingPipeline",
                "FEEDBACK_LOOP", "TuningDecision", "TrainingJob",
                "TuningAction", "FeedbackType", "TrainingStatus"
            ]
        ))
    except Exception:
        pass  # Ignore registration errors during import
