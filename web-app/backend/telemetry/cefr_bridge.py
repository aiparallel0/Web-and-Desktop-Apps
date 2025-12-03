"""
=============================================================================
CEFR BRIDGE - Integrates Telemetry with Circular Exchange Framework
=============================================================================

This module bridges the web telemetry system with the Circular Exchange
Framework (CEFR) for continuous improvement based on production data.

Features:
- Connects analytics events to CEFR data collectors
- Feeds production metrics to auto-tuning systems
- Enables feedback loops for model improvement

=============================================================================
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Import CEFR components
CEFR_AVAILABLE = False
try:
    from shared.circular_exchange.production_integration import (
        get_production_integration,
        record_extraction_feedback,
        ProductionCEFRIntegration
    )
    from shared.circular_exchange.auto_tuning import (
        get_auto_tuner,
        AutoTuner,
        TuningConfiguration
    )
    CEFR_AVAILABLE = True
    logger.info("CEFR integration available")
except ImportError as e:
    logger.info(f"CEFR components not available: {e}")


class CEFRBridge:
    """
    Bridge between web telemetry and CEFR systems.
    
    Automatically sends relevant events and metrics to CEFR for analysis
    and model improvement.
    """
    
    def __init__(self):
        """Initialize the CEFR bridge."""
        self._enabled = CEFR_AVAILABLE
        self._production_integration = None
        self._auto_tuner = None
        
        if self._enabled:
            try:
                self._production_integration = get_production_integration()
                self._auto_tuner = get_auto_tuner()
                logger.info("CEFR bridge initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize CEFR bridge: {e}")
                self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if CEFR bridge is enabled."""
        return self._enabled
    
    def report_extraction(
        self,
        extraction_id: str,
        model_id: str,
        success: bool,
        processing_time: float,
        confidence: float = None,
        items_count: int = 0,
        user_id: str = None
    ):
        """
        Report an extraction result to CEFR.
        
        Args:
            extraction_id: Unique ID of the extraction
            model_id: Model used for extraction
            success: Whether extraction was successful
            processing_time: Time taken in seconds
            confidence: Model confidence score
            items_count: Number of items extracted
            user_id: User who performed extraction
        """
        if not self._enabled:
            return
        
        try:
            # Send to production integration for metrics collection
            if self._production_integration:
                # Collect metrics (aggregated)
                model_performance = {
                    model_id: {
                        'extractions': 1,
                        'success': 1 if success else 0,
                        'avg_time': processing_time,
                        'avg_confidence': confidence or 0
                    }
                }
                
                self._production_integration.collect_metrics(
                    extractions_total=1,
                    extractions_success=1 if success else 0,
                    extractions_failed=0 if success else 1,
                    avg_processing_time=processing_time,
                    model_performance=model_performance,
                    error_distribution={}
                )
            
            # Record for auto-tuner
            if self._auto_tuner:
                self._auto_tuner.record_experiment_sample(
                    experiment_id=f"production_{model_id}",
                    success=success,
                    processing_time=processing_time,
                    confidence=confidence
                )
            
            logger.debug(f"Extraction reported to CEFR: {extraction_id}")
            
        except Exception as e:
            logger.error(f"Failed to report extraction to CEFR: {e}")
    
    def report_feedback(
        self,
        extraction_id: str,
        model_id: str,
        is_correct: bool,
        corrections: Dict[str, Any] = None,
        user_id: str = None
    ):
        """
        Report user feedback on extraction to CEFR.
        
        Args:
            extraction_id: ID of the extraction
            model_id: Model used
            is_correct: Whether extraction was correct
            corrections: User's corrections
            user_id: User providing feedback
        """
        if not self._enabled:
            return
        
        try:
            if self._production_integration:
                self._production_integration.record_user_feedback(
                    extraction_id=extraction_id,
                    model_id=model_id,
                    is_correct=is_correct,
                    corrections=corrections,
                    user_id=user_id
                )
            
            logger.debug(f"Feedback reported to CEFR: {extraction_id}")
            
        except Exception as e:
            logger.error(f"Failed to report feedback to CEFR: {e}")
    
    def report_error(
        self,
        error_type: str,
        error_message: str,
        model_id: str = None,
        context: Dict[str, Any] = None
    ):
        """
        Report an error to CEFR for pattern analysis.
        
        Args:
            error_type: Type of error
            error_message: Error message
            model_id: Model involved (if any)
            context: Additional context
        """
        if not self._enabled:
            return
        
        try:
            if self._production_integration:
                error_distribution = {error_type: 1}
                
                self._production_integration.collect_metrics(
                    extractions_total=0,
                    extractions_success=0,
                    extractions_failed=0,
                    avg_processing_time=0,
                    model_performance={},
                    error_distribution=error_distribution
                )
            
            logger.debug(f"Error reported to CEFR: {error_type}")
            
        except Exception as e:
            logger.error(f"Failed to report error to CEFR: {e}")
    
    def get_model_health(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get health status for a model from CEFR.
        
        Args:
            model_id: Model to check
            
        Returns:
            Health status dict or None
        """
        if not self._enabled or not self._production_integration:
            return None
        
        try:
            return self._production_integration.analyze_model_performance(model_id)
        except Exception as e:
            logger.error(f"Failed to get model health: {e}")
            return None
    
    def get_improvement_suggestions(self) -> list:
        """
        Get improvement suggestions from CEFR.
        
        Returns:
            List of improvement suggestions
        """
        if not self._enabled or not self._production_integration:
            return []
        
        try:
            return self._production_integration.generate_improvement_suggestions()
        except Exception as e:
            logger.error(f"Failed to get suggestions: {e}")
            return []
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get dashboard data from CEFR.
        
        Returns:
            Dashboard data dict
        """
        if not self._enabled or not self._production_integration:
            return {"enabled": False, "message": "CEFR not available"}
        
        try:
            data = self._production_integration.get_dashboard_data()
            data["enabled"] = True
            return data
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {"enabled": True, "error": str(e)}


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_bridge: Optional[CEFRBridge] = None


def get_cefr_bridge() -> CEFRBridge:
    """Get or create the global CEFR bridge instance."""
    global _bridge
    
    if _bridge is None:
        _bridge = CEFRBridge()
    
    return _bridge


def report_to_cefr(
    extraction_id: str,
    model_id: str,
    success: bool,
    processing_time: float,
    confidence: float = None
):
    """
    Convenience function to report extraction to CEFR.
    
    Args:
        extraction_id: Unique ID
        model_id: Model used
        success: Success status
        processing_time: Duration in seconds
        confidence: Model confidence
    """
    get_cefr_bridge().report_extraction(
        extraction_id=extraction_id,
        model_id=model_id,
        success=success,
        processing_time=processing_time,
        confidence=confidence
    )


def report_feedback_to_cefr(
    extraction_id: str,
    model_id: str,
    is_correct: bool,
    corrections: Dict[str, Any] = None
):
    """
    Convenience function to report feedback to CEFR.
    
    Args:
        extraction_id: Extraction ID
        model_id: Model used
        is_correct: Whether correct
        corrections: User corrections
    """
    get_cefr_bridge().report_feedback(
        extraction_id=extraction_id,
        model_id=model_id,
        is_correct=is_correct,
        corrections=corrections
    )
