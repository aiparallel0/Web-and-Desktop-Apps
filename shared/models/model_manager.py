"""
Model Manager - Central hub for managing and switching between different receipt extraction models
Allows easy model switching like changing disks/sockets
"""
import os
import json
import logging
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages available models and provides interface for model selection"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "models_config.json"

        self.config_path = config_path
        self.models_config = self._load_config()
        self.current_model = None
        self.loaded_processors = {}

    def _load_config(self) -> dict:
        """Load models configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded {len(config['available_models'])} model configurations")
            return config
        except Exception as e:
            logger.error(f"Failed to load models config: {e}")
            return {"available_models": {}, "default_model": None}

    def get_available_models(self) -> List[Dict]:
        """Get list of all available models with their details"""
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

    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """Get detailed information about a specific model"""
        return self.models_config['available_models'].get(model_id)

    def get_default_model(self) -> str:
        """Get the default model ID"""
        return self.models_config.get('default_model', 'donut_sroie')

    def select_model(self, model_id: str) -> bool:
        """Select a model for use"""
        if model_id not in self.models_config['available_models']:
            logger.error(f"Model {model_id} not found in available models")
            return False

        self.current_model = model_id
        logger.info(f"Selected model: {model_id}")
        return True

    def get_current_model(self) -> Optional[str]:
        """Get currently selected model ID"""
        return self.current_model

    def get_processor(self, model_id: Optional[str] = None):
        """Get processor instance for the specified model"""
        if model_id is None:
            model_id = self.current_model

        if model_id is None:
            model_id = self.get_default_model()
            self.current_model = model_id

        # Check if processor is already loaded
        if model_id in self.loaded_processors:
            logger.info(f"Using cached processor for {model_id}")
            return self.loaded_processors[model_id]

        # Load the appropriate processor
        model_config = self.get_model_info(model_id)
        if not model_config:
            raise ValueError(f"Model {model_id} not found")

        model_type = model_config['type']

        if model_type == 'donut':
            from .donut_processor import DonutProcessor
            processor = DonutProcessor(model_config)
        elif model_type == 'florence':
            from .donut_processor import FlorenceProcessor
            processor = FlorenceProcessor(model_config)
        elif model_type == 'ocr':
            from .ocr_processor import OCRProcessor
            processor = OCRProcessor(model_config)
        elif model_type == 'paddle':
            from .paddle_processor import PaddleProcessor
            processor = PaddleProcessor(model_config)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        # Cache the processor
        self.loaded_processors[model_id] = processor
        logger.info(f"Loaded and cached processor for {model_id}")

        return processor

    def unload_model(self, model_id: str):
        """Unload a model from memory"""
        if model_id in self.loaded_processors:
            del self.loaded_processors[model_id]
            logger.info(f"Unloaded model: {model_id}")

    def unload_all_models(self):
        """Unload all models from memory"""
        self.loaded_processors.clear()
        logger.info("Unloaded all models")

    def get_model_capabilities(self, model_id: str) -> Dict:
        """Get capabilities of a specific model"""
        model_info = self.get_model_info(model_id)
        if model_info:
            return model_info.get('capabilities', {})
        return {}

    def filter_models_by_capability(self, capability: str) -> List[str]:
        """Get list of models that support a specific capability"""
        matching_models = []
        for model_id, config in self.models_config['available_models'].items():
            if config.get('capabilities', {}).get(capability, False):
                matching_models.append(model_id)
        return matching_models
