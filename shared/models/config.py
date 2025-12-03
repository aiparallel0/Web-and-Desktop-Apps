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

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    from shared.circular_exchange.variable_package import VariablePackage, PackageRegistry, PackageChange
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    try:
        # Fallback to relative imports when running as a package
        from ..circular_exchange import PROJECT_CONFIG, ModuleRegistration
        from ..circular_exchange.variable_package import VariablePackage, PackageRegistry, PackageChange
        CIRCULAR_EXCHANGE_AVAILABLE = True
    except ImportError:
        CIRCULAR_EXCHANGE_AVAILABLE = False
        # Define stubs for when circular exchange is not available
        VariablePackage = None
        PackageRegistry = None
        PackageChange = None

logger = logging.getLogger(__name__)

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.models.ocr_config",
            file_path=__file__,
            description="Variable-based OCR configuration with auto-tuning and pipeline stages",
            dependencies=["shared.circular_exchange"],
            exports=["OCRConfig", "OCRPipelineStage", "get_ocr_config", "reset_ocr_config"]
        ))
    except Exception:
        pass  # Ignore registration errors during import


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
        
        # =====================================================================
        # Text Detection Parameters - Circular Exchange Integration
        # These parameters control the text detection phase with dynamic tuning
        # =====================================================================
        
        # Detection confidence threshold (lowered default for better detection)
        self._registry.create_package(
            name='ocr.detection.min_confidence',
            initial_value=0.25,  # Lowered default for improved text detection
            source_module='ocr_config',
            validator=lambda v: 0.0 <= v <= 1.0
        )
        
        # Detection box threshold for text region detection
        self._registry.create_package(
            name='ocr.detection.box_threshold',
            initial_value=0.3,
            source_module='ocr_config',
            validator=lambda v: 0.0 <= v <= 1.0
        )
        
        # Minimum text height in pixels
        self._registry.create_package(
            name='ocr.detection.min_text_height',
            initial_value=8,  # Lowered to catch smaller text
            source_module='ocr_config',
            validator=lambda v: v >= 1
        )
        
        # Maximum text height in pixels (to filter out noise)
        self._registry.create_package(
            name='ocr.detection.max_text_height',
            initial_value=500,
            source_module='ocr_config',
            validator=lambda v: v >= 10
        )
        
        # Text angle detection enabled
        self._registry.create_package(
            name='ocr.detection.use_angle_cls',
            initial_value=True,
            source_module='ocr_config'
        )
        
        # Multi-scale detection for better accuracy
        self._registry.create_package(
            name='ocr.detection.multi_scale',
            initial_value=True,
            source_module='ocr_config'
        )
        
        # Detection retry on failure
        self._registry.create_package(
            name='ocr.detection.auto_retry',
            initial_value=True,
            source_module='ocr_config'
        )
        
        # Preprocessing parameters for detection
        self._registry.create_package(
            name='ocr.detection.enhance_contrast',
            initial_value=True,
            source_module='ocr_config'
        )
        
        self._registry.create_package(
            name='ocr.detection.denoise_strength',
            initial_value=10,  # h parameter for fastNlMeansDenoising
            source_module='ocr_config',
            validator=lambda v: 0 <= v <= 50
        )
        
        self._registry.create_package(
            name='ocr.detection.binarization_threshold',
            initial_value=0,  # 0 means use Otsu's method
            source_module='ocr_config',
            validator=lambda v: 0 <= v <= 255
        )
        
        logger.debug("OCR parameter packages initialized (including detection parameters)")
    
    def _init_pipeline(self) -> None:
        """Initialize the OCR processing pipeline stages with circular exchange integration."""
        self._pipeline_stages = {
            # Image preprocessing stage
            'preprocessing': OCRPipelineStage(
                name='preprocessing',
                parameters={
                    'enhance_contrast': True,
                    'deskew': True,
                    'denoise': True,
                    'upscale_factor': 2.0,
                    'adaptive_threshold': True
                }
            ),
            # Text detection stage - core detection parameters
            'text_detection': OCRPipelineStage(
                name='text_detection',
                parameters={
                    'confidence_threshold': 0.25,  # Lowered for better detection
                    'min_text_height': 8,
                    'max_text_height': 500,
                    'use_angle_cls': True,
                    'multi_scale': True,
                    'detection_db_thresh': 0.2,
                    'detection_db_box_thresh': 0.3
                }
            ),
            # Character recognition stage
            'text_recognition': OCRPipelineStage(
                name='text_recognition',
                parameters={
                    'recognition_confidence': 0.3,
                    'language': 'eng',
                    'use_space_char': True,
                    'max_text_length': 256
                }
            ),
            # Line merging and extraction
            'line_extraction': OCRPipelineStage(
                name='line_extraction',
                parameters={
                    'merge_lines': True,
                    'sort_by_position': True,
                    'merge_threshold': 10,
                    'line_height_tolerance': 0.5
                }
            ),
            # Item parsing stage
            'item_parsing': OCRPipelineStage(
                name='item_parsing',
                parameters={
                    'use_patterns': True,
                    'fallback_enabled': True,
                    'relaxed_matching': False,
                    'min_item_confidence': 0.3
                }
            ),
            # Validation stage
            'validation': OCRPipelineStage(
                name='validation',
                parameters={
                    'validate_totals': True,
                    'validate_items': True,
                    'validate_math': True,
                    'tolerance': 0.10
                }
            ),
            # Post-processing stage for cleanup
            'post_processing': OCRPipelineStage(
                name='post_processing',
                parameters={
                    'apply_corrections': True,
                    'normalize_prices': True,
                    'clean_item_names': True
                }
            )
        }
        logger.debug("OCR pipeline stages initialized with detection configuration")
    
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
    # Text Detection Parameters - Circular Exchange Accessors
    # =====================================================================
    
    @property
    def detection_min_confidence(self) -> float:
        """Get the minimum detection confidence threshold (lowered default)."""
        pkg = self._registry.get_package('ocr.detection.min_confidence')
        return pkg.get() if pkg else 0.25
    
    def set_detection_min_confidence(self, value: float) -> bool:
        """Set the minimum detection confidence threshold."""
        pkg = self._registry.get_package('ocr.detection.min_confidence')
        return pkg.set(value) if pkg else False
    
    @property
    def detection_box_threshold(self) -> float:
        """Get the detection box threshold."""
        pkg = self._registry.get_package('ocr.detection.box_threshold')
        return pkg.get() if pkg else 0.3
    
    def set_detection_box_threshold(self, value: float) -> bool:
        """Set the detection box threshold."""
        pkg = self._registry.get_package('ocr.detection.box_threshold')
        return pkg.set(value) if pkg else False
    
    @property
    def detection_min_text_height(self) -> int:
        """Get the minimum text height for detection."""
        pkg = self._registry.get_package('ocr.detection.min_text_height')
        return pkg.get() if pkg else 8
    
    def set_detection_min_text_height(self, value: int) -> bool:
        """Set the minimum text height for detection."""
        pkg = self._registry.get_package('ocr.detection.min_text_height')
        return pkg.set(value) if pkg else False
    
    @property
    def detection_use_angle_cls(self) -> bool:
        """Check if angle classification is enabled for detection."""
        pkg = self._registry.get_package('ocr.detection.use_angle_cls')
        return pkg.get() if pkg else True
    
    @property
    def detection_multi_scale(self) -> bool:
        """Check if multi-scale detection is enabled."""
        pkg = self._registry.get_package('ocr.detection.multi_scale')
        return pkg.get() if pkg else True
    
    @property
    def detection_auto_retry(self) -> bool:
        """Check if auto-retry on detection failure is enabled."""
        pkg = self._registry.get_package('ocr.detection.auto_retry')
        return pkg.get() if pkg else True
    
    @property
    def detection_enhance_contrast(self) -> bool:
        """Check if contrast enhancement is enabled for detection."""
        pkg = self._registry.get_package('ocr.detection.enhance_contrast')
        return pkg.get() if pkg else True
    
    @property
    def detection_denoise_strength(self) -> int:
        """Get the denoise strength parameter."""
        pkg = self._registry.get_package('ocr.detection.denoise_strength')
        return pkg.get() if pkg else 10
    
    def set_detection_denoise_strength(self, value: int) -> bool:
        """Set the denoise strength parameter."""
        pkg = self._registry.get_package('ocr.detection.denoise_strength')
        return pkg.set(value) if pkg else False
    
    def get_detection_config(self) -> Dict[str, Any]:
        """
        Get all detection parameters as a dictionary.
        
        This method provides a convenient way to get all detection parameters
        at once for use by OCR processors. The parameters are dynamically
        managed via the circular exchange framework.
        
        Returns:
            Dictionary containing all detection parameters
        """
        return {
            'min_confidence': self.detection_min_confidence,
            'box_threshold': self.detection_box_threshold,
            'min_text_height': self.detection_min_text_height,
            'use_angle_cls': self.detection_use_angle_cls,
            'multi_scale': self.detection_multi_scale,
            'auto_retry': self.detection_auto_retry,
            'enhance_contrast': self.detection_enhance_contrast,
            'denoise_strength': self.detection_denoise_strength
        }
    
    def record_detection_result(
        self,
        text_regions_count: int,
        avg_confidence: float,
        success: bool,
        processing_time: float = 0.0
    ) -> None:
        """
        Record a text detection result for auto-tuning.
        
        This method tracks detection results to enable automatic parameter
        adjustment based on detection success rates.
        
        Args:
            text_regions_count: Number of text regions detected
            avg_confidence: Average confidence of detected regions
            success: Whether detection was successful
            processing_time: Time taken for detection in seconds
        """
        with self._lock:
            result = {
                'text_regions_count': text_regions_count,
                'avg_confidence': avg_confidence,
                'success': success,
                'processing_time': processing_time,
                'detection_min_confidence': self.detection_min_confidence,
                'detection_box_threshold': self.detection_box_threshold
            }
            
            # Store in detection-specific history
            if not hasattr(self, '_detection_history'):
                self._detection_history: List[Dict] = []
            
            self._detection_history.append(result)
            if len(self._detection_history) > self._max_history:
                self._detection_history.pop(0)
            
            # Auto-tune detection parameters if enabled
            if self.auto_tune:
                self._auto_tune_detection_parameters()
    
    def _auto_tune_detection_parameters(self) -> None:
        """
        Automatically tune detection parameters based on detection history.
        
        This implements an adaptive algorithm:
        - If detection success rate is low, lower the confidence threshold
        - If detection is returning too many false positives, increase threshold
        """
        if not hasattr(self, '_detection_history'):
            return
        
        if len(self._detection_history) < AUTO_TUNE_MIN_SAMPLES:
            return
        
        recent = self._detection_history[-AUTO_TUNE_WINDOW_SIZE:]
        success_rate = sum(1 for r in recent if r['success']) / len(recent)
        avg_regions = sum(r['text_regions_count'] for r in recent) / len(recent)
        
        # Target: 80% success rate with reasonable region count
        target_rate = 0.8
        
        if success_rate < target_rate - AUTO_TUNE_SUCCESS_TOLERANCE:
            # Lower threshold to detect more text
            current = self.detection_min_confidence
            if current > AUTO_TUNE_CONFIDENCE_MIN:
                new_val = max(AUTO_TUNE_CONFIDENCE_MIN, current - AUTO_TUNE_RELAX_STEP)
                self.set_detection_min_confidence(new_val)
                logger.info(f"Auto-tuned detection_min_confidence: {current:.2f} -> {new_val:.2f} "
                           f"(success_rate: {success_rate:.2%})")
        elif success_rate > target_rate + AUTO_TUNE_SUCCESS_TOLERANCE and avg_regions > 50:
            # Too many regions might mean low quality detection, tighten threshold
            current = self.detection_min_confidence
            if current < AUTO_TUNE_CONFIDENCE_MAX:
                new_val = min(AUTO_TUNE_CONFIDENCE_MAX, current + AUTO_TUNE_TIGHTEN_STEP)
                self.set_detection_min_confidence(new_val)
                logger.debug(f"Auto-tuned detection_min_confidence: {current:.2f} -> {new_val:.2f}")
    
    def get_detection_stats(self) -> Dict:
        """Get statistics about detection history."""
        with self._lock:
            if not hasattr(self, '_detection_history') or not self._detection_history:
                return {'total': 0, 'success_rate': 0.0, 'avg_regions': 0.0}
            
            total = len(self._detection_history)
            successful = sum(1 for r in self._detection_history if r['success'])
            avg_regions = sum(r['text_regions_count'] for r in self._detection_history) / total
            avg_confidence = sum(r['avg_confidence'] for r in self._detection_history) / total
            
            return {
                'total': total,
                'successful': successful,
                'success_rate': successful / total,
                'avg_regions': avg_regions,
                'avg_confidence': avg_confidence,
                'current_detection_min_confidence': self.detection_min_confidence,
                'current_detection_box_threshold': self.detection_box_threshold
            }
    
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
            'detection': self.get_detection_config(),
            'pipeline': {
                name: {
                    'enabled': stage.enabled,
                    'parameters': stage.parameters,
                    'success_rate': stage.success_rate
                }
                for name, stage in self._pipeline_stages.items()
            },
            'stats': self.get_extraction_stats(),
            'detection_stats': self.get_detection_stats()
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
            
            # Import detection parameters
            detection_config = config.get('detection', {})
            if 'min_confidence' in detection_config:
                self.set_detection_min_confidence(detection_config['min_confidence'])
            if 'box_threshold' in detection_config:
                self.set_detection_box_threshold(detection_config['box_threshold'])
            if 'min_text_height' in detection_config:
                self.set_detection_min_text_height(detection_config['min_text_height'])
            if 'denoise_strength' in detection_config:
                self.set_detection_denoise_strength(detection_config['denoise_strength'])
            
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
        # Reset general OCR parameters
        self.set_min_confidence(0.3)
        self.set_relaxed_confidence(0.2)
        self.set_relaxed_mode(False)
        self.set_auto_fallback(True)
        
        # Reset detection parameters (with lowered defaults for better detection)
        self.set_detection_min_confidence(0.25)
        self.set_detection_box_threshold(0.3)
        self.set_detection_min_text_height(8)
        self.set_detection_denoise_strength(10)
        
        # Reset pipeline stages
        self._init_pipeline()
        
        # Clear histories
        self._extraction_history.clear()
        if hasattr(self, '_detection_history'):
            self._detection_history.clear()
        
        logger.info("OCRConfig reset to defaults (including detection parameters)")
    
    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance for clean test isolation.
        
        This method should be used in test setup/teardown to ensure
        clean state between tests. Not intended for production use.
        """
        with cls._lock:
            cls._instance = None
        logger.debug("OCRConfig singleton instance reset")


# Global configuration instance
_ocr_config: Optional[OCRConfig] = None


def get_ocr_config() -> OCRConfig:
    """Get the global OCR configuration instance."""
    global _ocr_config
    if _ocr_config is None:
        _ocr_config = OCRConfig()
    return _ocr_config


def reset_ocr_config() -> None:
    """
    Reset the global OCR configuration instance for clean test isolation.
    
    This function resets both the global instance and the singleton
    to ensure clean state between tests.
    """
    global _ocr_config
    _ocr_config = None
    OCRConfig.reset_instance()
"""
OCR Processor Module with Circular Exchange Integration

This module provides Tesseract OCR-based receipt data extraction with:
- Dynamic parameter configuration via circular exchange framework
- Early-exit optimization for faster processing
- Multi-pass extraction for challenging images
- Auto-tuning based on detection results

The OCRProcessor class integrates with the circular exchange framework for
runtime parameter tuning and automatic optimization.
"""
import os,sys,re,logging,time,subprocess
from decimal import Decimal
from typing import Dict,List,Optional
from PIL import Image,ImageEnhance,ImageFilter
import cv2,numpy as np

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

from shared.utils.data import LineItem, ReceiptData, ExtractionResult
from shared.utils.image import load_and_validate_image, preprocess_for_ocr
from .ocr_common import (
    SKIP_KEYWORDS, PRICE_MIN, PRICE_MAX, normalize_price,
    extract_date, extract_total, extract_phone, extract_address,
    should_skip_line, should_skip_item_name, extract_store_name, 
    LINE_ITEM_PATTERNS, clean_item_name, extract_subtotal, extract_tax,
    validate_receipt_totals, extract_sku,
    extract_line_items as _extract_line_items_shared,
    parse_receipt_text as _parse_receipt_text_shared,
    get_detection_config, record_detection_result
)
try:
    import pytesseract
except ImportError:
    raise ImportError("pytesseract required: pip install pytesseract")
logger=logging.getLogger(__name__)

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.models.ocr_processor",
            file_path=__file__,
            description="Tesseract OCR-based receipt data extraction with early-exit optimization",
            dependencies=["shared.utils.image_processing", "shared.models.ocr_common", "shared.models.ocr_config"],
            exports=["OCRProcessor"]
        ))
    except Exception:
        pass

# Score thresholds for early-exit optimization in OCR extraction
# Good quality threshold: has total + some other data (avoid aggressive preprocessing)
GOOD_QUALITY_SCORE_THRESHOLD = 40
# Excellent quality threshold: high confidence result (stop searching immediately)
EXCELLENT_QUALITY_SCORE_THRESHOLD = 80

class OCRProcessor:

    def __init__(self,model_config:Dict):
        self.model_config=model_config
        self.model_name=model_config['name']
        self.tesseract_path=self._find_tesseract()
        if self.tesseract_path is None:
            raise EnvironmentError("Tesseract not installed. Install: https://github.com/UB-Mannheim/tesseract/wiki")
        if self.tesseract_path and self.tesseract_path!='tesseract':
            pytesseract.pytesseract.tesseract_cmd=self.tesseract_path
            logger.info(f"Tesseract: {self.tesseract_path}")
        self._verify_tesseract()

    def _verify_tesseract(self):
        try:
            version=pytesseract.get_tesseract_version()
            logger.info(f"Tesseract v{version}")
        except Exception as e:
            raise EnvironmentError(f"Tesseract not working: {e}") from e

    def _find_tesseract(self)->Optional[str]:
        logger.info("Searching Tesseract...")
        try:
            result=subprocess.run(['tesseract','--version'],capture_output=True,text=True,timeout=5)
            if result.returncode==0:return 'tesseract'
        except (subprocess.TimeoutExpired,FileNotFoundError):pass
        if sys.platform=='win32':
            paths=[r'C:\Program Files\Tesseract-OCR\tesseract.exe',r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe']
            for p in paths:
                if os.path.exists(p):return p
        elif sys.platform=='darwin':
            paths=['/usr/local/bin/tesseract','/opt/homebrew/bin/tesseract']
            for p in paths:
                if os.path.exists(p):return p
        else:
            paths=['/usr/bin/tesseract','/usr/local/bin/tesseract']
            for p in paths:
                if os.path.exists(p):return p
        return None

    def _aggressive_preprocess(self,image:Image.Image)->List[Image.Image]:
        preprocessed=[]
        img_np=np.array(image)
        upscaled=cv2.resize(img_np,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
        gray1=cv2.cvtColor(upscaled,cv2.COLOR_RGB2GRAY)
        denoised1=cv2.fastNlMeansDenoising(gray1,h=10)
        _,thresh1=cv2.threshold(denoised1,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        preprocessed.append(Image.fromarray(thresh1))
        gray2=cv2.cvtColor(img_np,cv2.COLOR_RGB2GRAY)
        adaptive=cv2.adaptiveThreshold(gray2,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
        preprocessed.append(Image.fromarray(adaptive))
        gray3=cv2.cvtColor(img_np,cv2.COLOR_RGB2GRAY)
        enhanced=Image.fromarray(gray3)
        enhancer=ImageEnhance.Contrast(enhanced)
        preprocessed.append(enhancer.enhance(2.0))
        return preprocessed

    def extract(self,image_path:str)->ExtractionResult:
        """Extract receipt data from image using Tesseract OCR.
        
        Uses early-exit strategy to avoid unnecessary OCR calls. Only performs
        aggressive multi-pass extraction when initial results are poor quality.
        Detection configuration is managed via the circular exchange framework
        with lowered default thresholds for improved text detection rates.
        
        Args:
            image_path: Path to the image file to process.
            
        Returns:
            ExtractionResult containing the extracted receipt data on success,
            or error information on failure.
        """
        start_time=time.time()
        if not self.tesseract_path:
            return ExtractionResult(success=False,error="Tesseract not installed")
        try:
            # Get detection configuration from circular exchange framework
            detection_config = get_detection_config()
            min_confidence = detection_config.get('min_confidence', 0.25)
            auto_retry = detection_config.get('auto_retry', True)
            
            image=load_and_validate_image(image_path)
            processed=preprocess_for_ocr(image,aggressive=True)
            
            # First pass: Try 2 PSM modes on preprocessed image
            # Score each result based on extraction quality, not just text length
            # Each result is a tuple: (mode_name, raw_text, parsed_receipt, quality_score)
            ocr_results=[]
            config1=r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$.,:/\-#@()&% '
            text1=pytesseract.image_to_string(processed,lang='eng',config=config1)
            receipt1=self._parse_receipt_text(text1)
            score1=self._score_result(receipt1,text1)
            ocr_results.append(('PSM 6',text1,receipt1,score1))
            
            config2=r'--oem 3 --psm 4'
            text2=pytesseract.image_to_string(processed,lang='eng',config=config2)
            receipt2=self._parse_receipt_text(text2)
            score2=self._score_result(receipt2,text2)
            ocr_results.append(('PSM 4',text2,receipt2,score2))
            
            # Select best result by score (quality) rather than just length
            best_mode,best_text,receipt,initial_score=max(ocr_results,key=lambda x:x[3])
            
            # Log both results for debugging
            logger.info(f"OCR complete: {best_mode}, len={len(best_text)}, score={initial_score} (threshold: {min_confidence})")
            
            # Early exit if initial result is good (has total and reasonable score)
            if initial_score >= GOOD_QUALITY_SCORE_THRESHOLD:
                receipt.processing_time=time.time()-start_time
                receipt.model_used=f"{self.model_name} ({best_mode})"
                receipt.confidence_score=min(1.0,initial_score/95)
                logger.info(f"Early exit with good score: {initial_score}")
                return ExtractionResult(success=True,data=receipt)
            
            # Low quality result - try aggressive multi-pass extraction
            if len(best_text.strip())<50:
                logger.info("Low OCR output - trying aggressive preprocessing")
            
            preprocessed_versions=self._aggressive_preprocess(image)
            psm_modes=[6,4,11,3]
            best_result,best_score=receipt,initial_score
            
            for v_idx,proc_img in enumerate(preprocessed_versions):
                for psm in psm_modes:
                    try:
                        config=f'--oem 3 --psm {psm}'
                        text=pytesseract.image_to_string(proc_img,lang='eng',config=config)
                        if not text or len(text.strip())<10:continue
                        rec=self._parse_receipt_text(text)
                        score=self._score_result(rec,text)
                        if score>best_score:
                            best_score=score
                            best_result=rec
                            # Early exit if we find an excellent result
                            if score >= EXCELLENT_QUALITY_SCORE_THRESHOLD:
                                logger.info(f"Found excellent result with score {score}, stopping search")
                                break
                    except:continue
                # Break outer loop too if excellent result found
                if best_score >= EXCELLENT_QUALITY_SCORE_THRESHOLD:
                    break
            
            # Record detection result for auto-tuning via circular exchange
            text_regions = len(best_text.strip().split('\n')) if best_text else 0
            record_detection_result(
                text_regions_count=text_regions,
                avg_confidence=min(1.0, best_score / 100) if best_score else 0.0,
                success=best_result is not None and best_score > 0,
                processing_time=time.time() - start_time
            )
            
            if best_result is None or best_score==0:
                return ExtractionResult(success=False,error="No readable text. Try EasyOCR.")
            best_result.processing_time=time.time()-start_time
            best_result.model_used=self.model_name
            best_result.confidence_score=min(1.0,best_score/95)
            return ExtractionResult(success=True,data=best_result)
        except Exception as e:
            logger.error(f"OCR failed: {e}",exc_info=True)
            return ExtractionResult(success=False,error=str(e))

    def _score_result(self,receipt:ReceiptData,text:str)->int:
        score=0
        # Known store names get higher score
        known_stores = ['WALMART', "TRADER JOE'S", 'COSTCO', 'TARGET', 'WHOLE FOODS', 'KROGER', 'SAFEWAY', 'PUBLIX', 'CVS', 'WALGREENS']
        if receipt.store_name:
            if receipt.store_name.upper() in known_stores:
                score+=40  # Bonus for recognized store
            elif len(receipt.store_name)>2:
                score+=10
        if receipt.transaction_date:score+=15
        if receipt.total and receipt.total>0:score+=30
        if receipt.items:score+=10*len(receipt.items)
        if receipt.store_address:score+=10
        if receipt.store_phone:score+=10
        # Validate math: subtotal + tax should equal total
        if receipt.subtotal and receipt.tax and receipt.total:
            expected = receipt.subtotal + receipt.tax
            if abs(expected - receipt.total) < Decimal('0.10'):
                score += 50  # Big bonus for valid math
            else:
                score -= 30  # Penalty for invalid math
        special_ratio=sum(1 for c in text if not c.isalnum() and not c.isspace())/max(len(text),1)
        if special_ratio>0.3:score-=20
        return max(0,score)

    def _parse_receipt_text(self,text:str)->ReceiptData:
        receipt=ReceiptData()
        lines=[line.strip() for line in text.split('\n') if line.strip()]
        if not lines:return receipt
        # Use shared implementation
        parsed = _parse_receipt_text_shared(lines)
        receipt.store_name = parsed['store_name']
        receipt.transaction_date = parsed['transaction_date']
        receipt.total = parsed['total']
        receipt.subtotal = parsed['subtotal']
        receipt.tax = parsed['tax']
        # Convert tuples to LineItem objects
        receipt.items = [LineItem(name=name, total_price=price, quantity=qty) for name, price, qty in parsed['items']]
        receipt.store_address = parsed['store_address']
        receipt.store_phone = parsed['store_phone']
        receipt.extraction_notes = parsed['extraction_notes']
        return receipt

    def _extract_line_items(self,lines:List[str])->List[LineItem]:
        # Use shared implementation and convert tuples to LineItem objects
        items_data = _extract_line_items_shared(lines)
        return [LineItem(name=name, total_price=price, quantity=qty) for name, price, qty in items_data]
