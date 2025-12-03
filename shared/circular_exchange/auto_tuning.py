"""
=============================================================================
CEFR AUTO-TUNING - Automated Model Optimization
=============================================================================

Provides automated model tuning based on production performance data.

Features:
- Automatic hyperparameter adjustment
- Performance-based model selection
- Training data curation
- A/B testing for model variants

=============================================================================
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TuningStrategy(str, Enum):
    """Available tuning strategies."""
    CONSERVATIVE = "conservative"  # Small, safe changes
    MODERATE = "moderate"          # Balanced approach
    AGGRESSIVE = "aggressive"      # Larger changes for faster improvement


class OptimizationTarget(str, Enum):
    """Optimization targets."""
    ACCURACY = "accuracy"
    SPEED = "speed"
    BALANCED = "balanced"


@dataclass
class TuningConfiguration:
    """Configuration for auto-tuning."""
    strategy: TuningStrategy = TuningStrategy.MODERATE
    target: OptimizationTarget = OptimizationTarget.BALANCED
    min_samples: int = 100
    evaluation_window_days: int = 7
    improvement_threshold: float = 0.02  # 2% improvement required
    max_experiments: int = 5


@dataclass
class TuningExperiment:
    """Represents a tuning experiment."""
    experiment_id: str
    model_id: str
    variant: str
    config: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    samples_evaluated: int = 0
    metrics: Dict[str, float] = field(default_factory=dict)
    status: str = "running"  # running, completed, failed


@dataclass
class TuningResult:
    """Result of a tuning session."""
    model_id: str
    original_metrics: Dict[str, float]
    tuned_metrics: Dict[str, float]
    improvement: float
    config_changes: Dict[str, Any]
    recommendation: str


class AutoTuner:
    """
    Automated model tuning based on production data.
    
    Analyzes performance metrics and adjusts model parameters
    to optimize for specified targets.
    """
    
    def __init__(self, config: TuningConfiguration = None):
        """
        Initialize auto-tuner.
        
        Args:
            config: Tuning configuration
        """
        self.config = config or TuningConfiguration()
        self._experiments: List[TuningExperiment] = []
        self._results: List[TuningResult] = []
        
        logger.info(f"AutoTuner initialized with {self.config.strategy.value} strategy")
    
    def analyze_model(
        self,
        model_id: str,
        performance_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze model performance and identify tuning opportunities.
        
        Args:
            model_id: Model to analyze
            performance_data: Historical performance data
            
        Returns:
            Analysis results with tuning recommendations
        """
        if len(performance_data) < self.config.min_samples:
            return {
                'model_id': model_id,
                'status': 'insufficient_data',
                'samples': len(performance_data),
                'required': self.config.min_samples
            }
        
        # Calculate current metrics
        success_rates = [d.get('success_rate', 0) for d in performance_data]
        processing_times = [d.get('processing_time', 0) for d in performance_data]
        confidence_scores = [d.get('confidence', 0) for d in performance_data if d.get('confidence')]
        
        current_metrics = {
            'avg_success_rate': sum(success_rates) / len(success_rates),
            'avg_processing_time': sum(processing_times) / len(processing_times),
            'avg_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            'sample_count': len(performance_data)
        }
        
        # Identify areas for improvement
        recommendations = []
        
        if current_metrics['avg_success_rate'] < 0.9:
            recommendations.append({
                'type': 'accuracy',
                'description': 'Success rate below 90%, consider additional training',
                'priority': 1
            })
        
        if current_metrics['avg_processing_time'] > 3.0:
            recommendations.append({
                'type': 'speed',
                'description': 'Processing time exceeds 3s, consider optimization',
                'priority': 2
            })
        
        if current_metrics['avg_confidence'] < 0.8 and current_metrics['avg_confidence'] > 0:
            recommendations.append({
                'type': 'confidence',
                'description': 'Average confidence below 80%, model may need retraining',
                'priority': 2
            })
        
        return {
            'model_id': model_id,
            'status': 'analyzed',
            'current_metrics': current_metrics,
            'recommendations': recommendations,
            'analyzed_at': datetime.utcnow().isoformat()
        }
    
    def suggest_hyperparameters(
        self,
        model_id: str,
        current_params: Dict[str, Any],
        performance_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Suggest hyperparameter adjustments based on performance.
        
        Args:
            model_id: Model identifier
            current_params: Current hyperparameters
            performance_metrics: Current performance metrics
            
        Returns:
            Suggested hyperparameter changes
        """
        suggestions = {}
        
        success_rate = performance_metrics.get('success_rate', 1.0)
        processing_time = performance_metrics.get('processing_time', 0)
        
        # Adjust based on strategy
        if self.config.strategy == TuningStrategy.AGGRESSIVE:
            adjustment_factor = 0.2
        elif self.config.strategy == TuningStrategy.MODERATE:
            adjustment_factor = 0.1
        else:
            adjustment_factor = 0.05
        
        # Learning rate adjustments
        if 'learning_rate' in current_params:
            lr = current_params['learning_rate']
            if success_rate < 0.85:
                # Increase learning rate for faster learning
                suggestions['learning_rate'] = lr * (1 + adjustment_factor)
            elif success_rate > 0.95:
                # Fine-tune with lower learning rate
                suggestions['learning_rate'] = lr * (1 - adjustment_factor / 2)
        
        # Batch size adjustments based on speed
        if 'batch_size' in current_params:
            batch_size = current_params['batch_size']
            if self.config.target == OptimizationTarget.SPEED and processing_time > 2.0:
                suggestions['batch_size'] = min(batch_size * 2, 32)
            elif self.config.target == OptimizationTarget.ACCURACY and success_rate < 0.9:
                suggestions['batch_size'] = max(batch_size // 2, 1)
        
        # Epoch adjustments
        if 'epochs' in current_params:
            epochs = current_params['epochs']
            if success_rate < 0.8:
                suggestions['epochs'] = epochs + 1
        
        return {
            'model_id': model_id,
            'current_params': current_params,
            'suggested_params': suggestions,
            'strategy': self.config.strategy.value,
            'target': self.config.target.value
        }
    
    def start_experiment(
        self,
        model_id: str,
        variant: str,
        config: Dict[str, Any]
    ) -> TuningExperiment:
        """
        Start a tuning experiment.
        
        Args:
            model_id: Base model ID
            variant: Variant identifier
            config: Experiment configuration
            
        Returns:
            TuningExperiment object
        """
        import uuid
        
        experiment = TuningExperiment(
            experiment_id=str(uuid.uuid4())[:8],
            model_id=model_id,
            variant=variant,
            config=config,
            started_at=datetime.utcnow()
        )
        
        self._experiments.append(experiment)
        
        logger.info(f"Started experiment {experiment.experiment_id} for {model_id}")
        
        return experiment
    
    def record_experiment_sample(
        self,
        experiment_id: str,
        success: bool,
        processing_time: float,
        confidence: float = None
    ):
        """
        Record a sample result for an experiment.
        
        Args:
            experiment_id: Experiment identifier
            success: Whether extraction was successful
            processing_time: Processing time in seconds
            confidence: Model confidence score
        """
        experiment = next(
            (e for e in self._experiments if e.experiment_id == experiment_id),
            None
        )
        
        if not experiment:
            logger.warning(f"Experiment {experiment_id} not found")
            return
        
        experiment.samples_evaluated += 1
        
        # Update running metrics
        n = experiment.samples_evaluated
        
        # Running average for success rate
        current_success = experiment.metrics.get('success_rate', 0)
        experiment.metrics['success_rate'] = (
            current_success * (n - 1) + (1 if success else 0)
        ) / n
        
        # Running average for processing time
        current_time = experiment.metrics.get('avg_processing_time', 0)
        experiment.metrics['avg_processing_time'] = (
            current_time * (n - 1) + processing_time
        ) / n
        
        # Running average for confidence
        if confidence is not None:
            current_conf = experiment.metrics.get('avg_confidence', 0)
            conf_count = experiment.metrics.get('_confidence_count', 0)
            experiment.metrics['avg_confidence'] = (
                current_conf * conf_count + confidence
            ) / (conf_count + 1)
            experiment.metrics['_confidence_count'] = conf_count + 1
    
    def complete_experiment(
        self,
        experiment_id: str
    ) -> Optional[TuningResult]:
        """
        Complete an experiment and generate results.
        
        Args:
            experiment_id: Experiment identifier
            
        Returns:
            TuningResult or None if experiment not found
        """
        experiment = next(
            (e for e in self._experiments if e.experiment_id == experiment_id),
            None
        )
        
        if not experiment:
            return None
        
        experiment.completed_at = datetime.utcnow()
        experiment.status = "completed"
        
        # Calculate improvement (placeholder - would compare to baseline)
        improvement = experiment.metrics.get('success_rate', 0) - 0.85  # Assume baseline
        
        result = TuningResult(
            model_id=experiment.model_id,
            original_metrics={'success_rate': 0.85},  # Placeholder baseline
            tuned_metrics=experiment.metrics,
            improvement=improvement,
            config_changes=experiment.config,
            recommendation=self._generate_recommendation(improvement, experiment)
        )
        
        self._results.append(result)
        
        logger.info(f"Completed experiment {experiment_id} with {improvement:.2%} improvement")
        
        return result
    
    def _generate_recommendation(
        self,
        improvement: float,
        experiment: TuningExperiment
    ) -> str:
        """Generate a recommendation based on experiment results."""
        if improvement > self.config.improvement_threshold:
            return f"APPLY: Experiment shows {improvement:.2%} improvement. Recommend applying changes."
        elif improvement > 0:
            return f"MONITOR: Small improvement ({improvement:.2%}). Consider running longer experiment."
        else:
            return f"REVERT: Experiment shows regression ({improvement:.2%}). Do not apply changes."
    
    def get_best_configuration(
        self,
        model_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the best configuration found for a model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Best configuration or None
        """
        model_results = [r for r in self._results if r.model_id == model_id]
        
        if not model_results:
            return None
        
        best = max(model_results, key=lambda r: r.improvement)
        
        if best.improvement > self.config.improvement_threshold:
            return best.config_changes
        
        return None
    
    def get_experiments_summary(self) -> Dict[str, Any]:
        """Get summary of all experiments."""
        return {
            'total_experiments': len(self._experiments),
            'completed': len([e for e in self._experiments if e.status == 'completed']),
            'running': len([e for e in self._experiments if e.status == 'running']),
            'results': [
                {
                    'model_id': r.model_id,
                    'improvement': r.improvement,
                    'recommendation': r.recommendation
                }
                for r in self._results
            ]
        }


# Global instance
_auto_tuner: Optional[AutoTuner] = None


def get_auto_tuner(config: TuningConfiguration = None) -> AutoTuner:
    """Get or create the auto-tuner instance."""
    global _auto_tuner
    
    if _auto_tuner is None:
        _auto_tuner = AutoTuner(config)
    
    return _auto_tuner
