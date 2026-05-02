"""
=============================================================================
MODEL MANAGER - Enterprise ML Model Orchestration Layer
=============================================================================

This module implements a production-grade ML model management system following
patterns from large-scale machine learning platforms.

Architecture Pattern: Model Registry + Processor Factory

┌─────────────────────────────────────────────────────────────────────────┐
│                          ModelManager                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    Configuration Layer                              │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │ │
│  │  │ Config File │  │  Validator  │  │  GPU Detector              │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                │                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    Processor Management                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │ │
│  │  │ LRU Cache   │  │   Factory   │  │  Health Monitor            │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Features:
- Thread-Safe Operations: All public methods are thread-safe
- LRU Caching: Automatic eviction of least-recently-used models
- Lazy Loading: Models loaded on-demand
- GPU Detection: Automatic CUDA availability detection
- Configuration Validation: Strict config schema validation
- Resource Management: Automatic garbage collection on unload
- Factory Pattern: Dynamic processor instantiation by type

Usage:
    from shared.models import ModelManager
    
    # Initialize with default config
    manager = ModelManager()
    
    # Or with custom config
    manager = ModelManager(config_path='path/to/config.json', max_loaded_models=5)
    
    # Get available models
    models = manager.get_available_models()
    
    # Select and use a model
    manager.select_model('donut_cord')
    processor = manager.get_processor()
    result = processor.extract('receipt.jpg')

Integration with Circular Exchange:
    The ModelManager can be wrapped in a VariablePackage for reactive updates:
    
    from shared.circular_exchange import CircularExchange
    
    exchange = CircularExchange.get_instance()
    model_state = exchange.create_package('model_manager_state', initial_value={
        'current_model': None,
        'loaded_models': [],
        'gpu_available': False
    })

=============================================================================
"""

from __future__ import annotations

import os
import gc
import json
import logging
import threading
import importlib
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, List, Any, Protocol, TypeVar, runtime_checkable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

# Import circular exchange decorator to reduce boilerplate
from shared.utils.decorators import circular_exchange_module
from shared.utils.telemetry import get_tracer, set_span_attributes

logger = logging.getLogger(__name__)

# Register module with Circular Exchange Framework using decorator
@circular_exchange_module(
    module_id="shared.models.model_manager",
    description="Enterprise ML model management with LRU caching and GPU detection",
    dependencies=["shared.circular_exchange"],
    exports=["ModelManager", "ModelType", "GPUInfo", "ModelInfo",
            "ConfigValidator", "GPUDetector", "ProcessorFactory"]
)
def _register_module():
    """Module registration placeholder for decorator."""
    pass

_register_module()


# =============================================================================
# THREAD POOL MANAGEMENT - Added based on CEF Round 2 analysis
# =============================================================================

# CEF Round 2: Configurable thread pool settings to prevent exhaustion
THREAD_POOL_SIZE = int(os.environ.get('MODEL_MANAGER_THREAD_POOL_SIZE', '4'))
THREAD_POOL_TIMEOUT = int(os.environ.get('MODEL_MANAGER_THREAD_POOL_TIMEOUT', '30'))

# Global thread pool for model loading operations
_model_executor: Optional[ThreadPoolExecutor] = None
_executor_lock = threading.Lock()


def get_model_executor() -> ThreadPoolExecutor:
    """
    Get the shared thread pool executor for model loading operations.
    
    CEF Round 2: Added to prevent thread pool exhaustion by using a shared,
    bounded thread pool instead of creating unlimited threads.
    """
    global _model_executor
    
    with _executor_lock:
        if _model_executor is None:
            logger.info(
                f"Initializing model loading thread pool (size: {THREAD_POOL_SIZE}, "
                f"timeout: {THREAD_POOL_TIMEOUT}s)"
            )
            _model_executor = ThreadPoolExecutor(
                max_workers=THREAD_POOL_SIZE,
                thread_name_prefix="model_loader"
            )
    
    return _model_executor


def shutdown_model_executor():
    """
    Shutdown the model loading thread pool gracefully.
    
    CEF Round 2: Added for proper resource cleanup.
    """
    global _model_executor
    
    with _executor_lock:
        if _model_executor is not None:
            logger.info("Shutting down model loading thread pool...")
            _model_executor.shutdown(wait=True, cancel_futures=False)
            _model_executor = None
            logger.info("Model loading thread pool shutdown complete")


# =============================================================================
# Type Definitions
# =============================================================================

class ModelType(Enum):
    """Enumeration of supported model types."""
    DONUT = "donut"
    FLORENCE = "florence"
    OCR = "ocr"
    EASYOCR = "easyocr"
    EASYOCR_SPATIAL = "easyocr_spatial"
    PADDLE = "paddle"
    PADDLE_SPATIAL = "paddle_spatial"
    SPATIAL = "spatial"
    CRAFT = "craft"


@dataclass
class GPUInfo:
    """Value object containing GPU information."""
    available: bool = False
    name: Optional[str] = None
    memory_gb: Optional[float] = None
    cuda_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'available': self.available,
            'name': self.name,
            'memory_gb': self.memory_gb,
            'cuda_version': self.cuda_version
        }


@dataclass
class ModelInfo:
    """Value object containing model information."""
    id: str
    name: str
    type: ModelType
    description: str
    requires_auth: bool = False
    huggingface_id: Optional[str] = None
    task_prompt: Optional[str] = None
    capabilities: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'requires_auth': self.requires_auth,
            'capabilities': self.capabilities
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModelInfo:
        """Create ModelInfo from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            type=ModelType(data['type']),
            description=data['description'],
            requires_auth=data.get('requires_auth', False),
            huggingface_id=data.get('huggingface_id'),
            task_prompt=data.get('task_prompt'),
            capabilities=data.get('capabilities', {}),
            metadata=data.get('metadata', {})
        )


@runtime_checkable
class Processor(Protocol):
    """Protocol defining the processor interface."""
    
    def extract(self, image_path: str) -> Any:
        """Extract data from an image."""
        ...


# =============================================================================
# Configuration Validation
# =============================================================================

class ConfigValidator:
    """Validates model configuration files."""
    
    REQUIRED_FIELDS = ['id', 'name', 'type', 'description']
    VALID_TYPES = [t.value for t in ModelType]
    AI_MODEL_TYPES = [ModelType.DONUT.value, ModelType.FLORENCE.value]
    
    @classmethod
    def validate(cls, config: Dict[str, Any]) -> None:
        """
        Validate the complete configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        if 'available_models' not in config:
            raise ValueError("Missing required field 'available_models' in config")
        
        if 'default_model' not in config:
            raise ValueError("Missing required field 'default_model' in config")
        
        if not isinstance(config['available_models'], dict):
            raise ValueError("'available_models' must be an object/dictionary")
        
        for model_id, model_config in config['available_models'].items():
            cls._validate_model(model_id, model_config)
        
        default = config['default_model']
        if default not in config['available_models']:
            raise ValueError(f"default_model '{default}' not found in available_models")
        
        if 'recommended_model' in config:
            recommended = config['recommended_model']
            if recommended not in config['available_models']:
                raise ValueError(f"recommended_model '{recommended}' not found in available_models")
        
        logger.info("Configuration validation passed")
    
    @classmethod
    def _validate_model(cls, model_id: str, model_config: Dict[str, Any]) -> None:
        """Validate a single model configuration."""
        for field in cls.REQUIRED_FIELDS:
            if field not in model_config:
                raise ValueError(f"Model '{model_id}' missing required field '{field}'")
        
        model_type = model_config['type']
        if model_type not in cls.VALID_TYPES:
            raise ValueError(
                f"Model '{model_id}' has invalid type '{model_type}'. "
                f"Must be one of: {cls.VALID_TYPES}"
            )
        
        if model_type in cls.AI_MODEL_TYPES:
            if 'huggingface_id' not in model_config:
                raise ValueError(
                    f"Model '{model_id}' of type '{model_type}' requires 'huggingface_id'"
                )
            if 'task_prompt' not in model_config:
                raise ValueError(
                    f"Model '{model_id}' of type '{model_type}' requires 'task_prompt'"
                )


# =============================================================================
# GPU Detection
# =============================================================================

class GPUDetector:
    """Handles GPU availability detection and reporting."""
    
    @classmethod
    def detect(cls) -> GPUInfo:
        """
        Detect GPU availability and capabilities.
        
        Returns:
            GPUInfo object with detection results
        """
        try:
            import torch
            
            if torch.cuda.is_available():
                gpu_info = GPUInfo(
                    available=True,
                    name=torch.cuda.get_device_name(0),
                    memory_gb=round(
                        torch.cuda.get_device_properties(0).total_memory / (1024**3), 2
                    ),
                    cuda_version=torch.version.cuda
                )
                
                logger.info("🚀 GPU ACCELERATION ENABLED")
                logger.info(f"   GPU: {gpu_info.name}")
                logger.info(f"   VRAM: {gpu_info.memory_gb} GB")
                logger.info(f"   CUDA: {gpu_info.cuda_version}")
                logger.info("   AI models will run 10-15x faster!")
                
                return gpu_info
            else:
                logger.info("ℹ️  GPU NOT AVAILABLE - Running on CPU")
                logger.info("   AI models will be slower (10-60 seconds per receipt)")
                logger.info("   OCR engines (EasyOCR, Tesseract, PaddleOCR) still work fine on CPU")
                return GPUInfo(available=False)
                
        except ImportError:
            logger.info("ℹ️  PyTorch not installed - advanced AI models disabled")
            logger.info("   Basic OCR models (EasyOCR, Tesseract, PaddleOCR) are available")
            logger.info("   For AI models: pip install torch transformers accelerate sentencepiece")
            return GPUInfo(available=False)
            
        except Exception as e:
            logger.debug(f"GPU check failed: {e}")
            return GPUInfo(available=False)


# =============================================================================
# Processor Factory
# =============================================================================

class ProcessorFactory:
    """
    Factory for creating processor instances using registry pattern.

    Implements the Factory Pattern with a registry-based approach to eliminate code duplication.
    """

    # Registry: {model_type: (module_path, class_name, optional_error_message, enhanced_module, enhanced_class)}
    _REGISTRY = {
        ModelType.DONUT.value: (
            '.ai_models', 'DonutProcessor',
            "Donut models require PyTorch and Transformers. "
            "Install with: pip install torch transformers accelerate sentencepiece.",
            None, None
        ),
        ModelType.FLORENCE.value: (
            '.ai_models', 'FlorenceProcessor',
            "Florence models require PyTorch and Transformers. "
            "Install with: pip install torch transformers accelerate sentencepiece.",
            None, None
        ),
        ModelType.OCR.value: (
            '.ocr_processor', 'OCRProcessor', None,
            '.enhanced_tesseract', 'EnhancedTesseractProcessor'
        ),
        ModelType.EASYOCR.value: (
            '.processors', 'EasyOCRProcessor', None,
            '.enhanced_ocr_engines', 'EnhancedEasyOCRProcessor'
        ),
        ModelType.EASYOCR_SPATIAL.value: (
            '.spatial_ocr', 'EasyOCRSpatialProcessor',
            "Spatial EasyOCR requires EasyOCR and spatial analysis. "
            "Install with: pip install easyocr opencv-python.",
            '.enhanced_spatial', 'EnhancedEasyOCRSpatialProcessor'
        ),
        ModelType.PADDLE.value: (
            '.processors', 'PaddleProcessor', None,
            '.enhanced_ocr_engines', 'EnhancedPaddleOCRProcessor'
        ),
        ModelType.PADDLE_SPATIAL.value: (
            '.spatial_ocr', 'PaddleOCRSpatialProcessor',
            "Spatial PaddleOCR requires PaddleOCR and spatial analysis. "
            "Install with: pip install paddleocr opencv-python.",
            '.enhanced_spatial', 'EnhancedPaddleOCRSpatialProcessor'
        ),
        ModelType.SPATIAL.value: (
            '.spatial_ocr', 'SpatialOCRProcessor',
            "Spatial OCR requires multiple OCR engines. "
            "Install with: pip install pytesseract easyocr paddleocr opencv-python.",
            None, None
        ),
        ModelType.CRAFT.value: (
            '.craft_detector', 'CRAFTProcessor',
            "CRAFT text detector requires craft-text-detector and PyTorch. "
            "Install with: pip install craft-text-detector torch.",
            None, None
        ),
    }

    @classmethod
    def create(cls, model_config: Dict[str, Any]) -> Processor:
        """
        Create a processor instance for the given model configuration.
        
        Uses standard processors only - enhanced processors disabled due to
        signature incompatibility with data structures.

        Args:
            model_config: Model configuration dictionary

        Returns:
            Processor instance

        Raises:
            ImportError: If required dependencies are not installed
            ValueError: If model type is unknown
        """
        model_type = model_config['type']
        model_id = model_config['id']

        logger.info(f"Creating processor for {model_id} (type: {model_type})")

        if model_type not in cls._REGISTRY:
            raise ValueError(f"Unknown model type: {model_type}")

        registry_entry = cls._REGISTRY[model_type]
        module_path, class_name, error_msg = registry_entry[0], registry_entry[1], registry_entry[2]
        
        # DISABLED: Enhanced processors have incompatible signatures
        # Use standard processors only for now
        # enhanced_module = registry_entry[3] if len(registry_entry) > 3 else None
        # enhanced_class = registry_entry[4] if len(registry_entry) > 4 else None
        
        # Use standard processor
        return cls._instantiate(module_path, class_name, model_config, error_msg)

    @classmethod
    def _instantiate(
        cls,
        module_path: str,
        class_name: str,
        config: Dict[str, Any],
        deps_error_msg: Optional[str] = None
    ) -> Processor:
        """
        Instantiate a processor with unified error handling.

        Args:
            module_path: Relative import path (e.g., '.ai_models')
            class_name: Processor class name
            config: Configuration dictionary
            deps_error_msg: Optional dependency error message

        Returns:
            Processor instance

        Raises:
            ImportError: If dependencies are missing
        """
        try:
            module = importlib.import_module(module_path, package='shared.models')
            processor_class = getattr(module, class_name)

            if not callable(processor_class):
                raise ImportError(f"{class_name} is not available")

            return processor_class(config)

        except (ImportError, TypeError) as e:
            if deps_error_msg:
                raise ImportError(f"{deps_error_msg} Error: {e}")
            raise
        except Exception as e:
            # Detect dependency-related errors
            if deps_error_msg:
                error_str = str(e).lower()
                if any(kw in error_str for kw in ['torch', 'transformers', 'cuda']):
                    raise ImportError(f"{deps_error_msg} Error: {e}")
            raise


# =============================================================================
# Model Manager
# =============================================================================

class ModelManager:
    """
    Enterprise-grade ML model management system.
    
    This class provides centralized management of AI/ML models including:
    - Configuration loading and validation
    - Model selection and switching
    - Processor creation and caching
    - Resource management and cleanup
    - GPU detection and optimization
    
    Thread Safety:
        All public methods are thread-safe and can be called concurrently.
    
    Memory Management:
        The manager implements LRU caching with configurable limits.
        When the limit is reached, the least recently used model is evicted.
    
    Attributes:
        config_path: Path to the models configuration file
        max_loaded_models: Maximum number of models to keep in memory
        current_model: Currently selected model ID
        gpu_info: Detected GPU information
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        max_loaded_models: int = 3
    ):
        """
        Initialize the ModelManager.
        
        Args:
            config_path: Path to models configuration JSON file.
                        Defaults to config/models_config.json
            max_loaded_models: Maximum number of models to keep loaded
                              in memory. Older models are evicted using LRU.
        """
        # Set default config path
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "models_config.json"
        
        self.config_path = Path(config_path)
        self.max_loaded_models = max_loaded_models
        
        # Thread synchronization
        self._lock = threading.RLock()
        
        # State
        self.current_model: Optional[str] = None
        self.loaded_processors: Dict[str, Processor] = {}
        self.model_last_used: Dict[str, datetime] = {}
        self.model_load_times: Dict[str, datetime] = {}
        
        # Load and validate configuration
        self.models_config = self._load_config()
        
        # Detect GPU
        self.gpu_info = GPUDetector.detect()
        
        logger.info(
            f"ModelManager initialized with {len(self.models_config['available_models'])} models"
        )
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load and validate the models configuration file.
        
        Returns:
            Validated configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
            FileNotFoundError: If config file doesn't exist
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            ConfigValidator.validate(config)
            
            logger.info(f"Loaded {len(config['available_models'])} model configurations")
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in models config: {e}")
            raise ValueError(f"Models configuration is not valid JSON: {e}") from e
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to load models config: {e}")
            raise
    
    def _check_dependencies(self) -> Dict[str, Dict[str, Any]]:
        """
        Check which model dependencies are available.
        
        Returns:
            Dictionary mapping dependency names to their status and info
        """
        deps = {}
        
        # Check OpenCV (for Tesseract)
        try:
            import cv2
            deps['opencv'] = {'available': True, 'version': cv2.__version__}
        except Exception as e:
            deps['opencv'] = {'available': False, 'error': str(e)}
            logger.warning("OpenCV not available - Tesseract models may not work properly")

        # Check EasyOCR
        try:
            import easyocr
            deps['easyocr'] = {'available': True, 'version': getattr(easyocr, '__version__', 'unknown')}
        except Exception as e:
            deps['easyocr'] = {'available': False, 'error': str(e)}
            logger.warning("EasyOCR not available")

        # Check PaddleOCR
        try:
            import paddleocr
            deps['paddleocr'] = {'available': True, 'version': getattr(paddleocr, '__version__', 'unknown')}
        except Exception as e:
            deps['paddleocr'] = {'available': False, 'error': str(e)}
            logger.warning("PaddleOCR not available: %s", e)

        # Check PyTorch (for Florence-2, DONUT, CRAFT)
        try:
            import torch
            deps['torch'] = {
                'available': True,
                'version': torch.__version__,
                'cuda_available': torch.cuda.is_available()
            }
        except Exception as e:
            deps['torch'] = {'available': False, 'error': str(e)}
            logger.warning("PyTorch not available - AI models will not work")

        # Check Transformers (for Florence-2, DONUT)
        try:
            import transformers
            deps['transformers'] = {'available': True, 'version': transformers.__version__}
        except Exception as e:
            deps['transformers'] = {'available': False, 'error': str(e)}
            logger.warning("Transformers not available - Florence-2 and DONUT models will not work")

        # Check CRAFT detector
        try:
            import craft_text_detector
            deps['craft'] = {'available': True, 'version': getattr(craft_text_detector, '__version__', 'unknown')}
        except Exception as e:
            deps['craft'] = {'available': False, 'error': str(e)}
            logger.warning("CRAFT text detector not available")
        
        # Check Tesseract
        try:
            import pytesseract
            deps['pytesseract'] = {'available': True, 'version': pytesseract.get_tesseract_version().public}
        except Exception as e:
            deps['pytesseract'] = {'available': False, 'error': str(e)}
            logger.warning("Tesseract OCR not available or not properly installed")
        
        return deps
    
    def get_available_models(self, check_availability: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of all available models.
        
        Args:
            check_availability: If True, check dependency availability for each model
        
        Returns:
            List of model information dictionaries with 'available' flag if checked
        """
        models = []
        
        # Get dependency status if checking availability
        deps = self._check_dependencies() if check_availability else {}
        
        for model_id, config in self.models_config['available_models'].items():
            model_info = {
                'id': config['id'],
                'name': config['name'],
                'type': config['type'],
                'description': config['description'],
                'requires_auth': config.get('requires_auth', False),
                'capabilities': config.get('capabilities', {})
            }
            
            # Check dependency availability based on model type
            if check_availability:
                model_type = config.get('type', '')
                available = True
                missing_deps = []
                
                # Check dependencies based on model type
                if model_type == 'ocr' or config.get('requires_tesseract'):
                    if not deps.get('opencv', {}).get('available'):
                        available = False
                        missing_deps.append('opencv-python-headless')
                    if not deps.get('pytesseract', {}).get('available'):
                        available = False
                        missing_deps.append('pytesseract')
                
                elif model_type in ['easyocr', 'easyocr_spatial']:
                    if not deps.get('easyocr', {}).get('available'):
                        available = False
                        missing_deps.append('easyocr')
                
                elif model_type in ['paddle', 'paddle_spatial'] or config.get('requires_paddleocr'):
                    if not deps.get('paddleocr', {}).get('available'):
                        available = False
                        missing_deps.append('paddleocr')
                
                elif model_type in ['florence', 'donut']:
                    if not deps.get('torch', {}).get('available'):
                        available = False
                        missing_deps.append('torch')
                    if not deps.get('transformers', {}).get('available'):
                        available = False
                        missing_deps.append('transformers')
                
                elif model_type == 'craft':
                    if not deps.get('torch', {}).get('available'):
                        available = False
                        missing_deps.append('torch')
                    if not deps.get('craft', {}).get('available'):
                        available = False
                        missing_deps.append('craft-text-detector')
                
                model_info['available'] = available
                model_info['status'] = 'ready' if available else 'missing_dependencies'
                if missing_deps:
                    model_info['missing_dependencies'] = missing_deps
                    model_info['error'] = f"Missing: {', '.join(missing_deps)}"
            
            models.append(model_info)
        return models
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific model.
        
        Args:
            model_id: The model identifier
            
        Returns:
            Model configuration dictionary or None if not found
        """
        return self.models_config['available_models'].get(model_id)
    
    def get_default_model(self) -> str:
        """
        Get the default model ID.
        
        Returns:
            Default model identifier
        """
        return self.models_config.get('default_model', 'donut_sroie')
    
    def select_model(self, model_id: str) -> bool:
        """
        Select a model as the current model.
        
        Args:
            model_id: The model identifier to select
            
        Returns:
            True if selection was successful, False otherwise
        """
        with self._lock:
            if model_id not in self.models_config['available_models']:
                logger.error(f"Model {model_id} not found in available models")
                return False
            
            self.current_model = model_id
            logger.info(f"Selected model: {model_id}")
            return True
    
    def get_current_model(self) -> Optional[str]:
        """
        Get the currently selected model ID.
        
        Returns:
            Current model identifier or None if no model selected
        """
        return self.current_model
    
    def get_processor(self, model_id: Optional[str] = None) -> Processor:
        """
        Get a processor for the specified model.
        
        This method implements lazy loading with LRU caching.
        If the model is already loaded, returns the cached instance.
        If the cache is full, evicts the least recently used model.
        
        Args:
            model_id: Model identifier. If None, uses current or default model.
            
        Returns:
            Processor instance for the model
            
        Raises:
            ValueError: If model is not found
            ImportError: If required dependencies are not installed
        """
        tracer = get_tracer()
        with tracer.start_as_current_span("model_manager.get_processor") as span:
            with self._lock:
                # Resolve model ID
                if model_id is None:
                    model_id = self.current_model
                if model_id is None:
                    model_id = self.get_default_model()
                    self.current_model = model_id
                
                # Set span attributes
                set_span_attributes(span, {
                    "operation.type": "model_loading",
                    "model.id": model_id,
                    "cache.size": len(self.loaded_processors),
                    "cache.max_size": self.max_loaded_models
                })
                
                # Check cache
                if model_id in self.loaded_processors:
                    logger.debug(f"Using cached processor for {model_id}")
                    self.model_last_used[model_id] = datetime.now()
                    set_span_attributes(span, {
                        "cache.hit": True,
                        "model.loaded_from_cache": True
                    })
                    return self.loaded_processors[model_id]
                
                # Cache miss
                set_span_attributes(span, {"cache.hit": False})
                
                # Evict if necessary
                if len(self.loaded_processors) >= self.max_loaded_models:
                    self._evict_least_recently_used()
                
                # Get model config
                model_config = self.get_model_info(model_id)
                if not model_config:
                    span.set_attribute("error", True)
                    raise ValueError(f"Model {model_id} not found")
                
                # Create processor
                try:
                    processor = ProcessorFactory.create(model_config)
                    
                    # Cache processor
                    self.loaded_processors[model_id] = processor
                    self.model_last_used[model_id] = datetime.now()
                    self.model_load_times[model_id] = datetime.now()
                    
                    # Set success attributes
                    set_span_attributes(span, {
                        "model.loaded": True,
                        "model.type": model_config.get('type', 'unknown')
                    })
                    
                    logger.info(f"✓ Loaded and cached processor for {model_id}")
                    return processor
                    
                except ImportError as e:
                    logger.error(f"❌ Failed to load processor {model_id}: {e}")
                    span.record_exception(e)
                    try:
                        from opentelemetry.trace import Status, StatusCode
                        span.set_status(Status(StatusCode.ERROR, f"Import error: {str(e)}"))
                    except ImportError:
                        pass
                    raise
                except Exception as e:
                    logger.error(f"❌ Failed to load processor {model_id}: {e}")
                    span.record_exception(e)
                    try:
                        from opentelemetry.trace import Status, StatusCode
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    except ImportError:
                        pass
                    raise
    
    def _evict_least_recently_used(self) -> None:
        """Evict the least recently used model from cache."""
        if not self.model_last_used:
            return
        
        lru_model = min(
            self.model_last_used.items(),
            key=lambda x: x[1]
        )[0]
        
        logger.info(f"Evicting least recently used model: {lru_model}")
        self.unload_model(lru_model)
    
    def unload_model(self, model_id: str) -> None:
        """
        Unload a specific model from memory.
        
        Args:
            model_id: The model identifier to unload
        """
        with self._lock:
            if model_id in self.loaded_processors:
                del self.loaded_processors[model_id]
                self.model_last_used.pop(model_id, None)
                self.model_load_times.pop(model_id, None)
                
                logger.info(f"Unloaded model: {model_id}")
                gc.collect()
    
    def unload_all_models(self) -> None:
        """Unload all models from memory."""
        with self._lock:
            self.loaded_processors.clear()
            self.model_last_used.clear()
            self.model_load_times.clear()
            
            logger.info("Unloaded all models")
            gc.collect()
    
    def get_model_capabilities(self, model_id: str) -> Dict[str, bool]:
        """
        Get the capabilities of a specific model.
        
        Args:
            model_id: The model identifier
            
        Returns:
            Dictionary of capabilities
        """
        model_info = self.get_model_info(model_id)
        if model_info:
            return model_info.get('capabilities', {})
        return {}
    
    def filter_models_by_capability(self, capability: str) -> List[str]:
        """
        Get models that have a specific capability.
        
        Args:
            capability: The capability to filter by
            
        Returns:
            List of model IDs with the capability
        """
        matching_models = []
        for model_id, config in self.models_config['available_models'].items():
            if config.get('capabilities', {}).get(capability, False):
                matching_models.append(model_id)
        return matching_models
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """
        Get resource usage statistics.
        
        Returns:
            Dictionary containing:
            - loaded_models_count: Number of loaded models
            - max_loaded_models: Maximum allowed models
            - current_model: Currently selected model
            - loaded_models: List of loaded model IDs
            - model_usage: Usage info for each loaded model
            - gpu_info: GPU availability and specs
        """
        with self._lock:
            stats = {
                'loaded_models_count': len(self.loaded_processors),
                'max_loaded_models': self.max_loaded_models,
                'current_model': self.current_model,
                'loaded_models': list(self.loaded_processors.keys()),
                'gpu_info': self.gpu_info.to_dict(),
                'model_usage': {}
            }
            
            for model_id in self.loaded_processors.keys():
                stats['model_usage'][model_id] = {
                    'loaded_at': self.model_load_times.get(model_id, 'unknown'),
                    'last_used': self.model_last_used.get(model_id, 'unknown')
                }
            
            return stats
    
    def is_model_loaded(self, model_id: str) -> bool:
        """
        Check if a model is currently loaded.
        
        Args:
            model_id: The model identifier to check
            
        Returns:
            True if model is loaded, False otherwise
        """
        return model_id in self.loaded_processors
    
    def get_loaded_models(self) -> List[str]:
        """
        Get list of currently loaded model IDs.
        
        Returns:
            List of loaded model identifiers
        """
        return list(self.loaded_processors.keys())
    
    # =========================================================================
    # Backward Compatibility Methods
    # =========================================================================
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Backward compatibility wrapper for ConfigValidator.validate().
        
        Args:
            config: Configuration dictionary to validate
        """
        ConfigValidator.validate(config)
    
    def _validate_model_config(self, model_id: str, model_config: Dict[str, Any]) -> None:
        """
        Backward compatibility wrapper for ConfigValidator._validate_model().
        
        Args:
            model_id: Model identifier
            model_config: Model configuration dictionary
        """
        ConfigValidator._validate_model(model_id, model_config)
    
    def preload_default_model(self) -> None:
        """
        Preload the default OCR model during startup.
        
        This is critical for Railway deployments to avoid cold-start timeouts.
        Only lightweight models (Tesseract) should be preloaded.
        
        Railway startup timeout is 30 seconds, so we only preload one model.
        """
        try:
            default_model = self.get_default_model()
            logger.info(f"🔄 Preloading default model: {default_model}")
            
            # Only preload if it's a lightweight OCR model
            model_config = self.get_model_info(default_model)
            if model_config and model_config.get('type') == 'ocr':
                processor = self.get_processor(default_model)
                logger.info(f"✅ Preloaded model: {default_model}")
            else:
                logger.info(f"⚠️  Skipping preload of heavy model: {default_model}")
                logger.info("   Heavy models (AI transformers) load on first request")
        except Exception as e:
            # Don't fail startup if preload fails
            logger.warning(f"⚠️  Failed to preload model (non-fatal): {e}")
            logger.info("   Model will load on first request instead")
