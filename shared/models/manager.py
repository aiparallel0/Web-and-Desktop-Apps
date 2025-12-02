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
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, List, Any, Protocol, TypeVar, runtime_checkable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.models.model_manager",
            file_path=__file__,
            description="Enterprise ML model management with LRU caching and GPU detection",
            dependencies=["shared.circular_exchange"],
            exports=["ModelManager", "ModelType", "GPUInfo", "ModelInfo", 
                    "ConfigValidator", "GPUDetector", "ProcessorFactory"]
        ))
    except Exception:
        pass  # Ignore registration errors during import


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
    PADDLE = "paddle"


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
    Factory for creating processor instances based on model type.
    
    Implements the Factory Pattern for dynamic processor instantiation.
    """
    
    @classmethod
    def create(cls, model_config: Dict[str, Any]) -> Processor:
        """
        Create a processor instance for the given model configuration.
        
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
        
        if model_type == ModelType.DONUT.value:
            return cls._create_donut_processor(model_config)
        elif model_type == ModelType.FLORENCE.value:
            return cls._create_florence_processor(model_config)
        elif model_type == ModelType.OCR.value:
            return cls._create_ocr_processor(model_config)
        elif model_type == ModelType.EASYOCR.value:
            return cls._create_easyocr_processor(model_config)
        elif model_type == ModelType.PADDLE.value:
            return cls._create_paddle_processor(model_config)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    @classmethod
    def _create_donut_processor(cls, config: Dict[str, Any]) -> Processor:
        """Create a Donut processor."""
        try:
            from .ai_models import DonutProcessor
            # Handle case where import succeeds but class is None due to lazy loading
            if not callable(DonutProcessor):
                raise ImportError("DonutProcessor is not available")
            return DonutProcessor(config)
        except ImportError as e:
            raise ImportError(
                "Donut models require PyTorch and Transformers. "
                "Install with: pip install torch transformers accelerate sentencepiece. "
                f"Error: {e}"
            )
        except TypeError as e:
            # Handle case where processor class is None or not callable
            if 'NoneType' in str(e) or 'not callable' in str(e):
                raise ImportError(
                    "Donut models require PyTorch and Transformers. "
                    "Install with: pip install torch transformers accelerate sentencepiece. "
                    f"Error: {e}"
                )
            raise
        except Exception as e:
            # Catch any other initialization errors that indicate missing dependencies
            error_msg = str(e).lower()
            if 'torch' in error_msg or 'transformers' in error_msg or 'cuda' in error_msg:
                raise ImportError(
                    "Donut models require PyTorch and Transformers. "
                    "Install with: pip install torch transformers accelerate sentencepiece. "
                    f"Error: {e}"
                )
            raise
    
    @classmethod
    def _create_florence_processor(cls, config: Dict[str, Any]) -> Processor:
        """Create a Florence processor."""
        try:
            from .ai_models import FlorenceProcessor
            # Handle case where import succeeds but class is None due to lazy loading
            if not callable(FlorenceProcessor):
                raise ImportError("FlorenceProcessor is not available")
            return FlorenceProcessor(config)
        except ImportError as e:
            raise ImportError(
                "Florence models require PyTorch and Transformers. "
                "Install with: pip install torch transformers accelerate sentencepiece. "
                f"Error: {e}"
            )
        except TypeError as e:
            # Handle case where processor class is None or not callable
            if 'NoneType' in str(e) or 'not callable' in str(e):
                raise ImportError(
                    "Florence models require PyTorch and Transformers. "
                    "Install with: pip install torch transformers accelerate sentencepiece. "
                    f"Error: {e}"
                )
            raise
        except Exception as e:
            # Catch any other initialization errors that indicate missing dependencies
            error_msg = str(e).lower()
            if 'torch' in error_msg or 'transformers' in error_msg or 'cuda' in error_msg:
                raise ImportError(
                    "Florence models require PyTorch and Transformers. "
                    "Install with: pip install torch transformers accelerate sentencepiece. "
                    f"Error: {e}"
                )
            raise
    
    @classmethod
    def _create_ocr_processor(cls, config: Dict[str, Any]) -> Processor:
        """Create an OCR processor."""
        from .ocr_processor import OCRProcessor
        return OCRProcessor(config)
    
    @classmethod
    def _create_easyocr_processor(cls, config: Dict[str, Any]) -> Processor:
        """Create an EasyOCR processor."""
        from .processors import EasyOCRProcessor
        return EasyOCRProcessor(config)
    
    @classmethod
    def _create_paddle_processor(cls, config: Dict[str, Any]) -> Processor:
        """Create a PaddleOCR processor."""
        from .processors import PaddleProcessor
        return PaddleProcessor(config)


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
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of all available models.
        
        Returns:
            List of model information dictionaries
        """
        models = []
        for model_id, config in self.models_config['available_models'].items():
            models.append({
                'id': config['id'],
                'name': config['name'],
                'type': config['type'],
                'description': config['description'],
                'requires_auth': config.get('requires_auth', False),
                'capabilities': config.get('capabilities', {})
            })
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
        with self._lock:
            # Resolve model ID
            if model_id is None:
                model_id = self.current_model
            if model_id is None:
                model_id = self.get_default_model()
                self.current_model = model_id
            
            # Check cache
            if model_id in self.loaded_processors:
                logger.debug(f"Using cached processor for {model_id}")
                self.model_last_used[model_id] = datetime.now()
                return self.loaded_processors[model_id]
            
            # Evict if necessary
            if len(self.loaded_processors) >= self.max_loaded_models:
                self._evict_least_recently_used()
            
            # Get model config
            model_config = self.get_model_info(model_id)
            if not model_config:
                raise ValueError(f"Model {model_id} not found")
            
            # Create processor
            try:
                processor = ProcessorFactory.create(model_config)
                
                # Cache processor
                self.loaded_processors[model_id] = processor
                self.model_last_used[model_id] = datetime.now()
                self.model_load_times[model_id] = datetime.now()
                
                logger.info(f"✓ Loaded and cached processor for {model_id}")
                return processor
                
            except ImportError as e:
                logger.error(f"❌ Failed to load processor {model_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"❌ Failed to load processor {model_id}: {e}")
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
