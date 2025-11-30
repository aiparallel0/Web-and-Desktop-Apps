"""
OCR Configuration Module with Circular Exchange Integration

This module provides a variable-based configuration system for OCR processing
that integrates with the circular exchange framework. It enables:

- Dynamic parameter adjustment (min_confidence, relaxed_mode, etc.)
- Automatic reliability improvements through change tracking
- Pipeline-like processing with encapsulated stages
- Real-time tuning without code changes

The OCRConfig class uses VariablePackage to make all parameters observable
and automatically adjustable based on detection results.
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from decimal import Decimal
import threading

# Import circular exchange components using relative import
from ..circular_exchange.variable_package import VariablePackage, PackageRegistry, PackageChange

logger = logging.getLogger(__name__)


# Auto-tuning configuration constants
AUTO_TUNE_MIN_SAMPLES = 10  # Minimum extractions before auto-tuning activates
AUTO_TUNE_WINDOW_SIZE = 20  # Number of recent extractions to consider
AUTO_TUNE_SUCCESS_TOLERANCE = 0.1  # Tolerance around target success rate
AUTO_TUNE_CONFIDENCE_MIN = 0.1  # Minimum confidence threshold
AUTO_TUNE_CONFIDENCE_MAX = 0.5  # Maximum confidence threshold
AUTO_TUNE_RELAX_STEP = 0.05  # Step to decrease confidence when relaxing
AUTO_TUNE_TIGHTEN_STEP = 0.02  # Step to increase confidence when tightening


@dataclass
class OCRPipelineStage:
    """Represents a stage in the OCR processing pipeline."""
    name: str
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    success_rate: float = 0.0
    total_runs: int = 0
    successful_runs: int = 0
    
    def record_result(self, success: bool) -> None:
        """Record the result of a pipeline stage execution."""
        self.total_runs += 1
        if success:
            self.successful_runs += 1
        self.success_rate = self.successful_runs / max(self.total_runs, 1)


class OCRConfig:
    """
    Variable-based OCR configuration with circular exchange integration.
    
    This class provides a dynamic configuration system where all OCR parameters
    are stored as VariablePackages, enabling:
    
    1. **Observable Parameters**: Any component can subscribe to parameter changes
    2. **Automatic Tuning**: Parameters can be adjusted based on detection results
    3. **Change History**: Track how parameters evolved over time
    4. **Pipeline Stages**: Encapsulated processing stages with individual configs
    
    Example:
        config = OCRConfig()
        
        # Subscribe to confidence changes
        def on_confidence_change(change):
            print(f"Confidence changed: {change.old_value} -> {change.new_value}")
        
        config.get_package('min_confidence').subscribe(on_confidence_change)
        
        # Update confidence dynamically
        config.set_min_confidence(0.25)
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global OCR configuration."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize OCR configuration with default parameters."""
        if self._initialized:
            return
            
        self._registry = PackageRegistry()
        self._lock = threading.RLock()
        self._pipeline_stages: Dict[str, OCRPipelineStage] = {}
        self._extraction_history: List[Dict] = []
        self._max_history = 100
        
        # Initialize default parameter packages
        self._init_parameters()
        
        # Initialize pipeline stages
        self._init_pipeline()
        
        self._initialized = True
        logger.info("OCRConfig initialized with circular exchange integration")
    
    def _init_parameters(self) -> None:
        """Initialize all OCR parameter packages with defaults."""
        # Confidence thresholds
        self._registry.create_package(
            name='ocr.min_confidence',
            initial_value=0.3,
            source_module='ocr_config',
            validator=lambda v: 0.0 <= v <= 1.0
        )
        
        self._registry.create_package(
            name='ocr.relaxed_confidence',
            initial_value=0.2,
            source_module='ocr_config',
            validator=lambda v: 0.0 <= v <= 1.0
        )
        
        # Mode flags
        self._registry.create_package(
            name='ocr.relaxed_mode',
            initial_value=False,
            source_module='ocr_config'
        )
        
        self._registry.create_package(
            name='ocr.auto_fallback',
            initial_value=True,
            source_module='ocr_config'
        )
        
        # Item validation thresholds
        self._registry.create_package(
            name='ocr.min_name_length',
            initial_value=2,
            source_module='ocr_config',
            validator=lambda v: v >= 1
        )
        
        self._registry.create_package(
            name='ocr.max_price',
            initial_value=1000.0,
            source_module='ocr_config',
            validator=lambda v: v > 0
        )
        
        self._registry.create_package(
            name='ocr.min_price',
            initial_value=0.01,
            source_module='ocr_config',
            validator=lambda v: v >= 0
        )
        
        # Digit/alpha ratio threshold (reject if digits exceed this ratio of alphas)
        self._registry.create_package(
            name='ocr.max_digit_ratio',
            initial_value=2.0,
            source_module='ocr_config',
            validator=lambda v: v > 0
        )
        
        # Retry configuration
        self._registry.create_package(
            name='ocr.max_retries',
            initial_value=2,
            source_module='ocr_config',
            validator=lambda v: v >= 0
        )
        
        # Auto-tuning enabled
        self._registry.create_package(
            name='ocr.auto_tune',
            initial_value=True,
            source_module='ocr_config'
        )
        
        # Target success rate for auto-tuning
        self._registry.create_package(
            name='ocr.target_success_rate',
            initial_value=0.8,
            source_module='ocr_config',
            validator=lambda v: 0.0 <= v <= 1.0
        )
        
        logger.debug("OCR parameter packages initialized")
    
    def _init_pipeline(self) -> None:
        """Initialize the OCR processing pipeline stages."""
        self._pipeline_stages = {
            'preprocessing': OCRPipelineStage(
                name='preprocessing',
                parameters={
                    'enhance_contrast': True,
                    'deskew': True,
                    'denoise': True
                }
            ),
            'text_detection': OCRPipelineStage(
                name='text_detection',
                parameters={
                    'confidence_threshold': 0.3,
                    'min_text_height': 10
                }
            ),
            'line_extraction': OCRPipelineStage(
                name='line_extraction',
                parameters={
                    'merge_lines': True,
                    'sort_by_position': True
                }
            ),
            'item_parsing': OCRPipelineStage(
                name='item_parsing',
                parameters={
                    'use_patterns': True,
                    'fallback_enabled': True
                }
            ),
            'validation': OCRPipelineStage(
                name='validation',
                parameters={
                    'validate_totals': True,
                    'validate_items': True
                }
            )
        }
        logger.debug("OCR pipeline stages initialized")
    
    # =====================================================================
    # Parameter Accessors
    # =====================================================================
    
    def get_package(self, name: str) -> Optional[VariablePackage]:
        """Get a parameter package by name."""
        return self._registry.get_package(name)
    
    @property
    def min_confidence(self) -> float:
        """Get the minimum confidence threshold."""
        pkg = self._registry.get_package('ocr.min_confidence')
        return pkg.get() if pkg else 0.3
    
    def set_min_confidence(self, value: float) -> bool:
        """Set the minimum confidence threshold."""
        pkg = self._registry.get_package('ocr.min_confidence')
        return pkg.set(value) if pkg else False
    
    @property
    def relaxed_confidence(self) -> float:
        """Get the relaxed mode confidence threshold."""
        pkg = self._registry.get_package('ocr.relaxed_confidence')
        return pkg.get() if pkg else 0.2
    
    def set_relaxed_confidence(self, value: float) -> bool:
        """Set the relaxed mode confidence threshold."""
        pkg = self._registry.get_package('ocr.relaxed_confidence')
        return pkg.set(value) if pkg else False
    
    @property
    def relaxed_mode(self) -> bool:
        """Get the relaxed mode flag."""
        pkg = self._registry.get_package('ocr.relaxed_mode')
        return pkg.get() if pkg else False
    
    def set_relaxed_mode(self, value: bool) -> bool:
        """Set the relaxed mode flag."""
        pkg = self._registry.get_package('ocr.relaxed_mode')
        return pkg.set(value) if pkg else False
    
    @property
    def auto_fallback(self) -> bool:
        """Get the auto fallback flag."""
        pkg = self._registry.get_package('ocr.auto_fallback')
        return pkg.get() if pkg else True
    
    def set_auto_fallback(self, value: bool) -> bool:
        """Set the auto fallback flag."""
        pkg = self._registry.get_package('ocr.auto_fallback')
        return pkg.set(value) if pkg else False
    
    @property
    def min_name_length(self) -> int:
        """Get the minimum item name length."""
        pkg = self._registry.get_package('ocr.min_name_length')
        return pkg.get() if pkg else 2
    
    @property
    def max_price(self) -> float:
        """Get the maximum allowed price."""
        pkg = self._registry.get_package('ocr.max_price')
        return pkg.get() if pkg else 1000.0
    
    @property
    def max_digit_ratio(self) -> float:
        """Get the maximum digit/alpha ratio for item names."""
        pkg = self._registry.get_package('ocr.max_digit_ratio')
        return pkg.get() if pkg else 2.0
    
    @property
    def auto_tune(self) -> bool:
        """Check if auto-tuning is enabled."""
        pkg = self._registry.get_package('ocr.auto_tune')
        return pkg.get() if pkg else True
    
    # =====================================================================
    # Pipeline Management
    # =====================================================================
    
    def get_pipeline_stage(self, name: str) -> Optional[OCRPipelineStage]:
        """Get a pipeline stage by name."""
        return self._pipeline_stages.get(name)
    
    def enable_stage(self, name: str) -> bool:
        """Enable a pipeline stage."""
        if name in self._pipeline_stages:
            self._pipeline_stages[name].enabled = True
            logger.info(f"Enabled pipeline stage: {name}")
            return True
        return False
    
    def disable_stage(self, name: str) -> bool:
        """Disable a pipeline stage."""
        if name in self._pipeline_stages:
            self._pipeline_stages[name].enabled = False
            logger.info(f"Disabled pipeline stage: {name}")
            return True
        return False
    
    def set_stage_parameter(self, stage_name: str, param_name: str, value: Any) -> bool:
        """Set a parameter for a pipeline stage."""
        if stage_name in self._pipeline_stages:
            self._pipeline_stages[stage_name].parameters[param_name] = value
            logger.debug(f"Set {stage_name}.{param_name} = {value}")
            return True
        return False
    
    def get_enabled_stages(self) -> List[str]:
        """Get list of enabled pipeline stages in order."""
        return [name for name, stage in self._pipeline_stages.items() if stage.enabled]
    
    # =====================================================================
    # Extraction Results & Auto-Tuning
    # =====================================================================
    
    def record_extraction_result(
        self,
        items_count: int,
        total_detected: Optional[Decimal],
        confidence_avg: float,
        success: bool,
        used_relaxed: bool = False
    ) -> None:
        """
        Record an extraction result for auto-tuning.
        
        This method tracks extraction results to enable automatic parameter
        adjustment based on detection success rates.
        """
        with self._lock:
            result = {
                'items_count': items_count,
                'total_detected': float(total_detected) if total_detected else None,
                'confidence_avg': confidence_avg,
                'success': success,
                'used_relaxed': used_relaxed,
                'min_confidence': self.min_confidence,
                'relaxed_mode': self.relaxed_mode
            }
            
            self._extraction_history.append(result)
            if len(self._extraction_history) > self._max_history:
                self._extraction_history.pop(0)
            
            # Auto-tune if enabled
            if self.auto_tune:
                self._auto_tune_parameters()
    
    def _auto_tune_parameters(self) -> None:
        """
        Automatically tune parameters based on extraction history.
        
        This implements a simple adaptive algorithm:
        - If success rate is below target, relax constraints
        - If success rate is above target, tighten constraints slightly
        """
        if len(self._extraction_history) < AUTO_TUNE_MIN_SAMPLES:
            return  # Need minimum data
        
        recent = self._extraction_history[-AUTO_TUNE_WINDOW_SIZE:]
        success_rate = sum(1 for r in recent if r['success']) / len(recent)
        
        target = self._registry.get_package('ocr.target_success_rate')
        target_rate = target.get() if target else 0.8
        
        # Only adjust if significantly below target
        if success_rate < target_rate - AUTO_TUNE_SUCCESS_TOLERANCE:
            # Relax constraints
            current_conf = self.min_confidence
            if current_conf > AUTO_TUNE_CONFIDENCE_MIN:
                new_conf = max(AUTO_TUNE_CONFIDENCE_MIN, current_conf - AUTO_TUNE_RELAX_STEP)
                self.set_min_confidence(new_conf)
                logger.info(f"Auto-tuned min_confidence: {current_conf:.2f} -> {new_conf:.2f} "
                           f"(success_rate: {success_rate:.2%})")
        
        elif success_rate > target_rate + AUTO_TUNE_SUCCESS_TOLERANCE:
            # Tighten constraints slightly for better precision
            current_conf = self.min_confidence
            if current_conf < AUTO_TUNE_CONFIDENCE_MAX:
                new_conf = min(AUTO_TUNE_CONFIDENCE_MAX, current_conf + AUTO_TUNE_TIGHTEN_STEP)
                self.set_min_confidence(new_conf)
                logger.debug(f"Auto-tuned min_confidence: {current_conf:.2f} -> {new_conf:.2f} "
                            f"(success_rate: {success_rate:.2%})")
    
    def get_extraction_stats(self) -> Dict:
        """Get statistics about extraction history."""
        with self._lock:
            if not self._extraction_history:
                return {'total': 0, 'success_rate': 0.0}
            
            total = len(self._extraction_history)
            successful = sum(1 for r in self._extraction_history if r['success'])
            relaxed_used = sum(1 for r in self._extraction_history if r.get('used_relaxed'))
            avg_items = sum(r['items_count'] for r in self._extraction_history) / total
            
            return {
                'total': total,
                'successful': successful,
                'success_rate': successful / total,
                'relaxed_used_count': relaxed_used,
                'average_items': avg_items,
                'current_min_confidence': self.min_confidence,
                'current_relaxed_mode': self.relaxed_mode
            }
    
    # =====================================================================
    # Configuration Export/Import
    # =====================================================================
    
    def export_config(self) -> Dict:
        """Export current configuration as a dictionary."""
        return {
            'parameters': {
                'min_confidence': self.min_confidence,
                'relaxed_confidence': self.relaxed_confidence,
                'relaxed_mode': self.relaxed_mode,
                'auto_fallback': self.auto_fallback,
                'min_name_length': self.min_name_length,
                'max_price': self.max_price,
                'max_digit_ratio': self.max_digit_ratio,
                'auto_tune': self.auto_tune
            },
            'pipeline': {
                name: {
                    'enabled': stage.enabled,
                    'parameters': stage.parameters,
                    'success_rate': stage.success_rate
                }
                for name, stage in self._pipeline_stages.items()
            },
            'stats': self.get_extraction_stats()
        }
    
    def import_config(self, config: Dict) -> bool:
        """Import configuration from a dictionary."""
        try:
            params = config.get('parameters', {})
            
            if 'min_confidence' in params:
                self.set_min_confidence(params['min_confidence'])
            if 'relaxed_confidence' in params:
                self.set_relaxed_confidence(params['relaxed_confidence'])
            if 'relaxed_mode' in params:
                self.set_relaxed_mode(params['relaxed_mode'])
            if 'auto_fallback' in params:
                self.set_auto_fallback(params['auto_fallback'])
            
            # Import pipeline configuration
            pipeline_config = config.get('pipeline', {})
            for name, stage_config in pipeline_config.items():
                if name in self._pipeline_stages:
                    if 'enabled' in stage_config:
                        self._pipeline_stages[name].enabled = stage_config['enabled']
                    if 'parameters' in stage_config:
                        self._pipeline_stages[name].parameters.update(stage_config['parameters'])
            
            logger.info("Configuration imported successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """Reset all parameters to their defaults."""
        self.set_min_confidence(0.3)
        self.set_relaxed_confidence(0.2)
        self.set_relaxed_mode(False)
        self.set_auto_fallback(True)
        
        # Reset pipeline stages
        self._init_pipeline()
        
        # Clear history
        self._extraction_history.clear()
        
        logger.info("OCRConfig reset to defaults")


# Global configuration instance
_ocr_config: Optional[OCRConfig] = None


def get_ocr_config() -> OCRConfig:
    """Get the global OCR configuration instance."""
    global _ocr_config
    if _ocr_config is None:
        _ocr_config = OCRConfig()
    return _ocr_config
