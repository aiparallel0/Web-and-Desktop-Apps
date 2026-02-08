"""
Error Recovery and Retry Module

Provides comprehensive error handling and recovery strategies:
- Automatic retry with backoff
- Fallback model selection
- Error classification and recovery
- Partial result recovery
- Graceful degradation
"""

import os
import sys
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from functools import wraps
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils.data import ExtractionResult, ReceiptData

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for recovery strategies."""
    TEMPORARY = "temporary"  # Network, timeout - retry immediately
    RESOURCE = "resource"    # Memory, disk - retry with smaller data
    DEPENDENCY = "dependency"  # Missing lib - try alternative
    DATA = "data"            # Invalid input - try preprocessing
    FATAL = "fatal"          # Cannot recover


class RetryStrategy(Enum):
    """Retry strategies for different error types."""
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    WITH_PREPROCESSING = "with_preprocessing"
    WITH_FALLBACK = "with_fallback"
    NO_RETRY = "no_retry"


class ErrorClassifier:
    """Classifies errors into categories for appropriate recovery."""
    
    @staticmethod
    def classify_error(error: Exception) -> ErrorCategory:
        """
        Classify error into category.
        
        Args:
            error: Exception object
            
        Returns:
            ErrorCategory
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Temporary errors
        if any(keyword in error_str for keyword in ['timeout', 'connection', 'network', 'temporary']):
            return ErrorCategory.TEMPORARY
        
        if any(keyword in error_type for keyword in ['timeout', 'connection']):
            return ErrorCategory.TEMPORARY
        
        # Resource errors
        if any(keyword in error_str for keyword in ['memory', 'disk', 'space', 'resource']):
            return ErrorCategory.RESOURCE
        
        if any(keyword in error_type for keyword in ['memory', 'overflow']):
            return ErrorCategory.RESOURCE
        
        # Dependency errors
        if any(keyword in error_str for keyword in ['import', 'module', 'not found', 'no module']):
            return ErrorCategory.DEPENDENCY
        
        if 'importerror' in error_type or 'modulenotfounderror' in error_type:
            return ErrorCategory.DEPENDENCY
        
        # Data errors
        if any(keyword in error_str for keyword in ['invalid', 'corrupt', 'format', 'parse']):
            return ErrorCategory.DATA
        
        if any(keyword in error_type for keyword in ['value', 'type', 'parse']):
            return ErrorCategory.DATA
        
        # Fatal errors
        if any(keyword in error_str for keyword in ['fatal', 'critical', 'unrecoverable']):
            return ErrorCategory.FATAL
        
        # Default to temporary for unknown errors
        return ErrorCategory.TEMPORARY
    
    @staticmethod
    def get_retry_strategy(category: ErrorCategory) -> RetryStrategy:
        """Get retry strategy for error category."""
        strategy_map = {
            ErrorCategory.TEMPORARY: RetryStrategy.EXPONENTIAL_BACKOFF,
            ErrorCategory.RESOURCE: RetryStrategy.WITH_PREPROCESSING,
            ErrorCategory.DEPENDENCY: RetryStrategy.WITH_FALLBACK,
            ErrorCategory.DATA: RetryStrategy.WITH_PREPROCESSING,
            ErrorCategory.FATAL: RetryStrategy.NO_RETRY
        }
        return strategy_map.get(category, RetryStrategy.NO_RETRY)


class RetryManager:
    """Manages retry logic with various strategies."""
    
    @staticmethod
    def retry_with_strategy(
        func: Callable,
        strategy: RetryStrategy,
        max_attempts: int = 3,
        *args,
        **kwargs
    ) -> Tuple[bool, Any, Optional[Exception]]:
        """
        Retry function with specified strategy.
        
        Args:
            func: Function to retry
            strategy: Retry strategy to use
            max_attempts: Maximum number of attempts
            *args: Function args
            **kwargs: Function kwargs
            
        Returns:
            Tuple of (success, result, last_error)
        """
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_attempts} with strategy {strategy.value}")
                
                # Apply strategy-specific logic
                if strategy == RetryStrategy.IMMEDIATE:
                    result = func(*args, **kwargs)
                
                elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                    if attempt > 0:
                        wait_time = 2 ** attempt  # 2, 4, 8 seconds
                        logger.info(f"Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    result = func(*args, **kwargs)
                
                elif strategy == RetryStrategy.LINEAR_BACKOFF:
                    if attempt > 0:
                        wait_time = attempt * 2  # 2, 4, 6 seconds
                        logger.info(f"Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    result = func(*args, **kwargs)
                
                elif strategy == RetryStrategy.WITH_PREPROCESSING:
                    # Try with more aggressive preprocessing
                    if 'preprocessing_level' in kwargs:
                        kwargs['preprocessing_level'] = min(kwargs.get('preprocessing_level', 1) + 1, 3)
                    result = func(*args, **kwargs)
                
                else:
                    result = func(*args, **kwargs)
                
                # Success
                logger.info(f"Attempt {attempt + 1} succeeded")
                return True, result, None
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                # Check if we should stop retrying
                if strategy == RetryStrategy.NO_RETRY:
                    break
                
                # Don't retry on last attempt
                if attempt == max_attempts - 1:
                    break
        
        logger.error(f"All {max_attempts} attempts failed")
        return False, None, last_error


class FallbackManager:
    """Manages fallback to alternative models/methods."""
    
    MODEL_FALLBACK_CHAIN = [
        'ocr_tesseract',
        'ocr_easyocr',
        'ocr_paddle',
        'ocr_easyocr_spatial',
        'ocr_paddle_spatial'
    ]
    
    @staticmethod
    def get_fallback_models(current_model: str) -> List[str]:
        """
        Get list of fallback models to try.
        
        Args:
            current_model: Current model that failed
            
        Returns:
            List of alternative models
        """
        try:
            # Find current model in chain
            current_idx = FallbackManager.MODEL_FALLBACK_CHAIN.index(current_model)
            # Return remaining models in chain
            return FallbackManager.MODEL_FALLBACK_CHAIN[current_idx + 1:]
        except ValueError:
            # Model not in chain, return all models
            return FallbackManager.MODEL_FALLBACK_CHAIN.copy()
    
    @staticmethod
    def try_with_fallback(
        extraction_func: Callable,
        model_id: str,
        *args,
        **kwargs
    ) -> Tuple[bool, Any, str]:
        """
        Try extraction with fallback models.
        
        Args:
            extraction_func: Extraction function
            model_id: Initial model to try
            *args: Function args
            **kwargs: Function kwargs
            
        Returns:
            Tuple of (success, result, model_used)
        """
        # Try primary model
        try:
            logger.info(f"Trying primary model: {model_id}")
            result = extraction_func(model_id, *args, **kwargs)
            
            if result and (not hasattr(result, 'success') or result.success):
                return True, result, model_id
                
        except Exception as e:
            logger.warning(f"Primary model {model_id} failed: {e}")
        
        # Try fallback models
        fallback_models = FallbackManager.get_fallback_models(model_id)
        
        for fallback_model in fallback_models:
            try:
                logger.info(f"Trying fallback model: {fallback_model}")
                result = extraction_func(fallback_model, *args, **kwargs)
                
                if result and (not hasattr(result, 'success') or result.success):
                    logger.info(f"Fallback model {fallback_model} succeeded")
                    return True, result, fallback_model
                    
            except Exception as e:
                logger.warning(f"Fallback model {fallback_model} failed: {e}")
                continue
        
        logger.error("All fallback models failed")
        return False, None, model_id


class PartialResultRecovery:
    """Recovers partial results from failed extractions."""
    
    @staticmethod
    def recover_partial_data(error: Exception, context: Dict[str, Any]) -> Optional[ReceiptData]:
        """
        Attempt to recover partial data from failed extraction.
        
        Args:
            error: Exception that occurred
            context: Context data that may contain partial results
            
        Returns:
            ReceiptData with partial data, or None
        """
        partial_receipt = ReceiptData()
        has_data = False
        
        # Try to extract data from context
        if 'raw_text' in context and context['raw_text']:
            try:
                # Parse raw text for basic info
                text = context['raw_text']
                
                # Try to find total
                import re
                total_match = re.search(r'(?:total|amount).*?\$?(\d+\.\d{2})', text, re.IGNORECASE)
                if total_match:
                    from decimal import Decimal
                    partial_receipt.total = Decimal(total_match.group(1))
                    has_data = True
                
                # Try to find store name (usually first line)
                lines = text.split('\n')
                if lines:
                    partial_receipt.store_name = lines[0].strip()
                    has_data = True
                
            except Exception as e:
                logger.debug(f"Failed to recover from raw text: {e}")
        
        # Try to extract from partial OCR results
        if 'partial_ocr_results' in context:
            try:
                results = context['partial_ocr_results']
                # Process partial results
                # Implementation would depend on OCR engine format
                has_data = True
            except Exception as e:
                logger.debug(f"Failed to recover from partial OCR: {e}")
        
        return partial_receipt if has_data else None


def with_retry_and_recovery(
    max_attempts: int = 3,
    enable_fallback: bool = True,
    enable_partial_recovery: bool = True
):
    """
    Decorator for functions that need retry and recovery.
    
    Args:
        max_attempts: Maximum retry attempts
        enable_fallback: Whether to try fallback models
        enable_partial_recovery: Whether to recover partial results
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            context = {}
            
            for attempt in range(max_attempts):
                try:
                    logger.info(f"[Retry] Attempt {attempt + 1}/{max_attempts}")
                    result = func(*args, **kwargs)
                    
                    # Success
                    return result
                    
                except Exception as e:
                    last_error = e
                    logger.warning(f"[Retry] Attempt {attempt + 1} failed: {e}")
                    
                    # Classify error
                    category = ErrorClassifier.classify_error(e)
                    strategy = ErrorClassifier.get_retry_strategy(category)
                    
                    logger.info(f"[Retry] Error category: {category.value}, strategy: {strategy.value}")
                    
                    # Check if we should stop
                    if strategy == RetryStrategy.NO_RETRY or attempt == max_attempts - 1:
                        break
                    
                    # Apply wait if needed
                    if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                        wait_time = 2 ** attempt
                        logger.info(f"[Retry] Waiting {wait_time}s...")
                        time.sleep(wait_time)
            
            # All attempts failed
            logger.error(f"[Retry] All {max_attempts} attempts failed")
            
            # Try partial recovery if enabled
            if enable_partial_recovery:
                logger.info("[Recovery] Attempting partial result recovery...")
                partial_data = PartialResultRecovery.recover_partial_data(last_error, context)
                
                if partial_data:
                    logger.info("[Recovery] Partial data recovered")
                    return ExtractionResult(
                        success=False,
                        data=partial_data,
                        error=f"Partial extraction after {max_attempts} attempts: {str(last_error)}",
                        confidence_score=0.5
                    )
            
            # Return error result
            return ExtractionResult(
                success=False,
                error=str(last_error),
                confidence_score=0.0
            )
        
        return wrapper
    return decorator


class GracefulDegradation:
    """Implements graceful degradation strategies."""
    
    @staticmethod
    def degrade_quality_settings(current_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reduce quality settings to handle difficult images.
        
        Args:
            current_settings: Current detection settings
            
        Returns:
            Degraded settings
        """
        degraded = current_settings.copy()
        
        # Disable enhancement if enabled
        if degraded.get('enable_enhancement', True):
            degraded['enable_enhancement'] = False
            logger.info("[Degrade] Disabled image enhancement")
        
        # Disable deskew if enabled
        elif degraded.get('enable_deskew', True):
            degraded['enable_deskew'] = False
            logger.info("[Degrade] Disabled deskew")
        
        # Disable column mode if enabled
        elif degraded.get('column_mode', False):
            degraded['column_mode'] = False
            logger.info("[Degrade] Disabled column mode")
        
        # Switch to auto detection mode
        elif degraded.get('detection_mode') != 'auto':
            degraded['detection_mode'] = 'auto'
            logger.info("[Degrade] Switched to auto detection mode")
        
        return degraded
    
    @staticmethod
    def try_with_degradation(
        extraction_func: Callable,
        initial_settings: Dict[str, Any],
        max_degradations: int = 3,
        *args,
        **kwargs
    ) -> Tuple[bool, Any, Dict[str, Any]]:
        """
        Try extraction with progressive quality degradation.
        
        Args:
            extraction_func: Extraction function
            initial_settings: Initial settings
            max_degradations: Maximum degradation attempts
            *args: Function args
            **kwargs: Function kwargs
            
        Returns:
            Tuple of (success, result, final_settings)
        """
        current_settings = initial_settings.copy()
        
        for degradation_level in range(max_degradations + 1):
            try:
                logger.info(f"[Degradation] Level {degradation_level}/{max_degradations}")
                
                # Try extraction with current settings
                result = extraction_func(*args, settings=current_settings, **kwargs)
                
                if result and (not hasattr(result, 'success') or result.success):
                    logger.info(f"[Degradation] Succeeded at level {degradation_level}")
                    return True, result, current_settings
                
            except Exception as e:
                logger.warning(f"[Degradation] Level {degradation_level} failed: {e}")
            
            # Degrade settings for next attempt
            if degradation_level < max_degradations:
                current_settings = GracefulDegradation.degrade_quality_settings(current_settings)
        
        logger.error("[Degradation] All degradation levels failed")
        return False, None, current_settings


# Example usage functions

def extract_with_full_recovery(image_path: str, model_id: str, settings: Dict[str, Any]) -> ExtractionResult:
    """
    Extract with full retry, fallback, and recovery strategies.
    
    Args:
        image_path: Path to image
        model_id: Model to use
        settings: Detection settings
        
    Returns:
        ExtractionResult
    """
    from shared.models.manager import ModelManager
    
    manager = ModelManager()
    
    # Try with retry and recovery
    @with_retry_and_recovery(max_attempts=3, enable_fallback=True, enable_partial_recovery=True)
    def extract_internal():
        processor = manager.get_processor(model_id)
        return processor.extract(image_path)
    
    try:
        return extract_internal()
    except Exception as e:
        logger.error(f"Extraction with recovery failed: {e}")
        return ExtractionResult(
            success=False,
            error=str(e),
            confidence_score=0.0
        )
