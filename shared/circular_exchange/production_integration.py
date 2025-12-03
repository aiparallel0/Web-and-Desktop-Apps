"""
=============================================================================
CEFR PRODUCTION INTEGRATION - Live System Integration
=============================================================================

Integrates the Circular Exchange Framework with production systems for:
- Real-time performance monitoring
- Automated model performance analysis
- User feedback collection for improvement

This module bridges the CEFR analysis capabilities with live application data.

=============================================================================
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Import CEFR components
try:
    from .analysis.metrics_analyzer import METRICS_ANALYZER, ModelPerformanceReport
    from .analysis.data_collector import DATA_COLLECTOR, DataCategory
    from .refactor.feedback_loop import FEEDBACK_LOOP, FeedbackType
    CEFR_AVAILABLE = True
except ImportError:
    CEFR_AVAILABLE = False
    logger.warning("CEFR components not fully available")


@dataclass
class ProductionMetrics:
    """Metrics collected from production system."""
    timestamp: datetime
    extractions_total: int
    extractions_success: int
    extractions_failed: int
    avg_processing_time: float
    model_performance: Dict[str, Dict[str, float]]
    error_distribution: Dict[str, int]
    user_feedback_positive: int
    user_feedback_negative: int


@dataclass
class ModelImprovement:
    """Suggested improvement for a model."""
    model_id: str
    improvement_type: str
    description: str
    estimated_impact: str
    priority: int  # 1-5
    data_requirements: Dict[str, Any]


class ProductionCEFRIntegration:
    """
    Integrates CEFR with production systems for continuous improvement.
    
    Responsibilities:
    - Collect metrics from production
    - Analyze model performance
    - Generate improvement suggestions
    - Track feedback for model training
    """
    
    def __init__(self):
        """Initialize production integration."""
        self._metrics_history: List[ProductionMetrics] = []
        self._improvements: List[ModelImprovement] = []
        self._feedback_queue: List[Dict[str, Any]] = []
        
        logger.info("ProductionCEFRIntegration initialized")
    
    def collect_metrics(
        self,
        extractions_total: int,
        extractions_success: int,
        extractions_failed: int,
        avg_processing_time: float,
        model_performance: Dict[str, Dict[str, float]],
        error_distribution: Dict[str, int]
    ) -> ProductionMetrics:
        """
        Collect and store production metrics.
        
        Args:
            extractions_total: Total extractions in period
            extractions_success: Successful extractions
            extractions_failed: Failed extractions
            avg_processing_time: Average processing time in seconds
            model_performance: Per-model performance metrics
            error_distribution: Distribution of error types
            
        Returns:
            ProductionMetrics object
        """
        metrics = ProductionMetrics(
            timestamp=datetime.utcnow(),
            extractions_total=extractions_total,
            extractions_success=extractions_success,
            extractions_failed=extractions_failed,
            avg_processing_time=avg_processing_time,
            model_performance=model_performance,
            error_distribution=error_distribution,
            user_feedback_positive=0,
            user_feedback_negative=0
        )
        
        self._metrics_history.append(metrics)
        
        # Keep only last 30 days of metrics
        cutoff = datetime.utcnow() - timedelta(days=30)
        self._metrics_history = [
            m for m in self._metrics_history
            if m.timestamp > cutoff
        ]
        
        # Integrate with CEFR if available
        if CEFR_AVAILABLE:
            self._send_to_cefr(metrics)
        
        logger.info(f"Collected metrics: {extractions_total} extractions, {avg_processing_time:.2f}s avg")
        
        return metrics
    
    def _send_to_cefr(self, metrics: ProductionMetrics):
        """Send metrics to CEFR for analysis."""
        try:
            DATA_COLLECTOR.log_metrics({
                'category': DataCategory.MODEL_PERFORMANCE,
                'timestamp': metrics.timestamp.isoformat(),
                'data': {
                    'extractions_total': metrics.extractions_total,
                    'success_rate': metrics.extractions_success / max(metrics.extractions_total, 1),
                    'avg_processing_time': metrics.avg_processing_time,
                    'model_performance': metrics.model_performance
                }
            })
        except Exception as e:
            logger.error(f"Failed to send metrics to CEFR: {e}")
    
    def record_user_feedback(
        self,
        extraction_id: str,
        model_id: str,
        is_correct: bool,
        corrections: Dict[str, Any] = None,
        user_id: str = None
    ):
        """
        Record user feedback on extraction quality.
        
        Args:
            extraction_id: ID of the extraction
            model_id: Model used for extraction
            is_correct: Whether extraction was correct
            corrections: User corrections if any
            user_id: User who provided feedback
        """
        feedback = {
            'timestamp': datetime.utcnow().isoformat(),
            'extraction_id': extraction_id,
            'model_id': model_id,
            'is_correct': is_correct,
            'corrections': corrections or {},
            'user_id': user_id
        }
        
        self._feedback_queue.append(feedback)
        
        # Send to CEFR if available
        if CEFR_AVAILABLE:
            try:
                FEEDBACK_LOOP.record_feedback(
                    feedback_type=FeedbackType.USER_CORRECTION,
                    model_id=model_id,
                    data=feedback
                )
            except Exception as e:
                logger.error(f"Failed to record feedback in CEFR: {e}")
        
        logger.debug(f"Recorded feedback for extraction {extraction_id}: correct={is_correct}")
    
    def analyze_model_performance(
        self,
        model_id: str,
        time_period_days: int = 7
    ) -> Dict[str, Any]:
        """
        Analyze performance of a specific model over time.
        
        Args:
            model_id: Model to analyze
            time_period_days: Analysis period in days
            
        Returns:
            Performance analysis results
        """
        cutoff = datetime.utcnow() - timedelta(days=time_period_days)
        
        relevant_metrics = [
            m for m in self._metrics_history
            if m.timestamp > cutoff and model_id in m.model_performance
        ]
        
        if not relevant_metrics:
            return {
                'model_id': model_id,
                'status': 'no_data',
                'message': 'Insufficient data for analysis'
            }
        
        # Calculate aggregated metrics
        total_extractions = 0
        total_success = 0
        total_time = 0.0
        
        for m in relevant_metrics:
            model_data = m.model_performance.get(model_id, {})
            total_extractions += model_data.get('extractions', 0)
            total_success += model_data.get('success', 0)
            total_time += model_data.get('avg_time', 0)
        
        success_rate = total_success / max(total_extractions, 1)
        avg_time = total_time / max(len(relevant_metrics), 1)
        
        # Analyze feedback
        model_feedback = [
            f for f in self._feedback_queue
            if f['model_id'] == model_id
        ]
        
        positive_feedback = sum(1 for f in model_feedback if f['is_correct'])
        negative_feedback = len(model_feedback) - positive_feedback
        
        feedback_rate = positive_feedback / max(len(model_feedback), 1)
        
        # Determine health status
        if success_rate > 0.95 and feedback_rate > 0.9:
            health = 'excellent'
        elif success_rate > 0.85 and feedback_rate > 0.8:
            health = 'good'
        elif success_rate > 0.7 and feedback_rate > 0.6:
            health = 'fair'
        else:
            health = 'needs_attention'
        
        return {
            'model_id': model_id,
            'period_days': time_period_days,
            'total_extractions': total_extractions,
            'success_rate': round(success_rate, 4),
            'avg_processing_time': round(avg_time, 3),
            'feedback_count': len(model_feedback),
            'feedback_positive_rate': round(feedback_rate, 4),
            'health_status': health,
            'analyzed_at': datetime.utcnow().isoformat()
        }
    
    def generate_improvement_suggestions(self) -> List[ModelImprovement]:
        """
        Generate improvement suggestions based on collected data.
        
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Analyze each model's performance
        model_ids = set()
        for m in self._metrics_history:
            model_ids.update(m.model_performance.keys())
        
        for model_id in model_ids:
            analysis = self.analyze_model_performance(model_id)
            
            if analysis.get('health_status') == 'needs_attention':
                suggestions.append(ModelImprovement(
                    model_id=model_id,
                    improvement_type='finetuning',
                    description=f"Model {model_id} has low success rate ({analysis['success_rate']:.1%}). Consider finetuning with recent successful extractions.",
                    estimated_impact='High - could improve success rate by 10-20%',
                    priority=1,
                    data_requirements={
                        'samples_needed': 50,
                        'sample_type': 'corrected_extractions'
                    }
                ))
            
            if analysis.get('avg_processing_time', 0) > 5.0:
                suggestions.append(ModelImprovement(
                    model_id=model_id,
                    improvement_type='optimization',
                    description=f"Model {model_id} is slow ({analysis['avg_processing_time']:.2f}s avg). Consider optimization or model quantization.",
                    estimated_impact='Medium - could reduce processing time by 30-50%',
                    priority=2,
                    data_requirements={}
                ))
        
        # Analyze error patterns
        error_counts = {}
        for m in self._metrics_history:
            for error_type, count in m.error_distribution.items():
                error_counts[error_type] = error_counts.get(error_type, 0) + count
        
        if error_counts:
            most_common_error = max(error_counts, key=error_counts.get)
            if error_counts[most_common_error] > 100:
                suggestions.append(ModelImprovement(
                    model_id='all',
                    improvement_type='error_handling',
                    description=f"Error '{most_common_error}' is occurring frequently ({error_counts[most_common_error]} times). Consider adding specific handling.",
                    estimated_impact='Medium - could reduce errors by 20-30%',
                    priority=2,
                    data_requirements={}
                ))
        
        self._improvements = suggestions
        return suggestions
    
    def get_training_data_recommendations(
        self,
        model_id: str,
        max_samples: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recommendations for training data based on feedback.
        
        Args:
            model_id: Model to get recommendations for
            max_samples: Maximum number of samples
            
        Returns:
            List of recommended training samples
        """
        # Get feedback with corrections
        training_candidates = [
            f for f in self._feedback_queue
            if f['model_id'] == model_id and f.get('corrections')
        ]
        
        # Sort by recency
        training_candidates.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Return recommendations
        return [
            {
                'extraction_id': f['extraction_id'],
                'corrections': f['corrections'],
                'timestamp': f['timestamp']
            }
            for f in training_candidates[:max_samples]
        ]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get data for CEFR integration dashboard.
        
        Returns:
            Dashboard data including metrics and suggestions
        """
        recent_metrics = [
            m for m in self._metrics_history
            if m.timestamp > datetime.utcnow() - timedelta(days=7)
        ]
        
        # Calculate totals
        total_extractions = sum(m.extractions_total for m in recent_metrics)
        total_success = sum(m.extractions_success for m in recent_metrics)
        avg_time = sum(m.avg_processing_time for m in recent_metrics) / max(len(recent_metrics), 1)
        
        return {
            'period': '7_days',
            'summary': {
                'total_extractions': total_extractions,
                'success_rate': round(total_success / max(total_extractions, 1), 4),
                'avg_processing_time': round(avg_time, 3),
                'feedback_count': len(self._feedback_queue)
            },
            'improvements': [
                {
                    'model_id': i.model_id,
                    'type': i.improvement_type,
                    'description': i.description,
                    'priority': i.priority
                }
                for i in self._improvements
            ],
            'model_health': {
                model_id: self.analyze_model_performance(model_id)
                for model_id in set(
                    m for metrics in recent_metrics
                    for m in metrics.model_performance.keys()
                )
            }
        }


# Global instance
_integration: Optional[ProductionCEFRIntegration] = None


def get_production_integration() -> ProductionCEFRIntegration:
    """Get or create the production integration instance."""
    global _integration
    
    if _integration is None:
        _integration = ProductionCEFRIntegration()
    
    return _integration


def collect_production_metrics(**kwargs) -> ProductionMetrics:
    """Convenience function to collect production metrics."""
    return get_production_integration().collect_metrics(**kwargs)


def record_extraction_feedback(
    extraction_id: str,
    model_id: str,
    is_correct: bool,
    corrections: Dict[str, Any] = None
):
    """Convenience function to record feedback."""
    get_production_integration().record_user_feedback(
        extraction_id=extraction_id,
        model_id=model_id,
        is_correct=is_correct,
        corrections=corrections
    )
