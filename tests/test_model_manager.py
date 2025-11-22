"""
Tests for ModelManager - thread safety, memory management, and initialization
"""
import pytest
import threading
import time
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.models.model_manager import ModelManager


class TestModelManagerInitialization:
    """Test ModelManager initialization and configuration"""

    def test_initialization(self):
        """Test basic ModelManager initialization"""
        manager = ModelManager()
        assert manager is not None
        assert manager.models_config is not None
        assert 'available_models' in manager.models_config

    def test_config_validation(self):
        """Test configuration validation"""
        manager = ModelManager()
        assert manager.models_config['default_model'] is not None
        assert manager.models_config['default_model'] in manager.models_config['available_models']

    def test_get_available_models(self):
        """Test getting available models list"""
        manager = ModelManager()
        models = manager.get_available_models()
        assert len(models) > 0
        assert all('id' in model for model in models)
        assert all('name' in model for model in models)
        assert all('type' in model for model in models)

    def test_get_model_info(self):
        """Test getting individual model info"""
        manager = ModelManager()
        models = manager.get_available_models()
        for model in models:
            info = manager.get_model_info(model['id'])
            assert info is not None
            assert info['id'] == model['id']

    def test_default_model(self):
        """Test default model selection"""
        manager = ModelManager()
        default = manager.get_default_model()
        assert default is not None
        assert default in manager.models_config['available_models']


class TestModelManagerThreadSafety:
    """Test thread safety of ModelManager operations"""

    def test_concurrent_model_selection(self):
        """Test concurrent model selection from multiple threads"""
        manager = ModelManager()
        models = manager.get_available_models()
        errors = []

        def select_random_model():
            try:
                for _ in range(10):
                    model_id = models[0]['id']  # Use first model
                    success = manager.select_model(model_id)
                    assert success
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        # Run 5 threads concurrently
        threads = [threading.Thread(target=select_random_model) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread safety errors: {errors}"

    def test_concurrent_resource_stats(self):
        """Test concurrent access to resource stats"""
        manager = ModelManager()
        errors = []

        def get_stats():
            try:
                for _ in range(20):
                    stats = manager.get_resource_stats()
                    assert 'loaded_models_count' in stats
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_stats) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestModelManagerMemoryManagement:
    """Test memory management and LRU eviction"""

    def test_max_loaded_models_limit(self):
        """Test that max_loaded_models limit is enforced"""
        # Create manager with limit of 2 models
        manager = ModelManager(max_loaded_models=2)

        stats = manager.get_resource_stats()
        assert stats['max_loaded_models'] == 2

    def test_resource_stats(self):
        """Test resource statistics reporting"""
        manager = ModelManager()

        stats = manager.get_resource_stats()
        assert 'loaded_models_count' in stats
        assert 'max_loaded_models' in stats
        assert 'current_model' in stats
        assert 'loaded_models' in stats
        assert isinstance(stats['loaded_models'], list)

    def test_unload_all_models(self):
        """Test unloading all models"""
        manager = ModelManager()

        # Unload all models
        manager.unload_all_models()

        stats = manager.get_resource_stats()
        assert stats['loaded_models_count'] == 0
        assert len(stats['loaded_models']) == 0


class TestModelManagerErrorHandling:
    """Test error handling in ModelManager"""

    def test_select_invalid_model(self):
        """Test selecting non-existent model"""
        manager = ModelManager()
        success = manager.select_model('nonexistent_model')
        assert not success

    def test_get_invalid_model_info(self):
        """Test getting info for non-existent model"""
        manager = ModelManager()
        info = manager.get_model_info('nonexistent_model')
        assert info is None

    def test_get_processor_with_invalid_model(self):
        """Test getting processor for invalid model"""
        manager = ModelManager()
        with pytest.raises(ValueError):
            manager.get_processor('nonexistent_model')


class TestConfigurationValidation:
    """Test configuration validation"""

    def test_valid_config(self):
        """Test that default config is valid"""
        manager = ModelManager()
        # If initialization succeeded, config is valid
        assert manager.models_config is not None

    def test_model_type_validation(self):
        """Test that all models have valid types"""
        manager = ModelManager()
        valid_types = ['donut', 'florence', 'ocr', 'easyocr', 'paddle']

        for model_id, config in manager.models_config['available_models'].items():
            assert config['type'] in valid_types, f"Model {model_id} has invalid type"

    def test_model_required_fields(self):
        """Test that all models have required fields"""
        manager = ModelManager()
        required_fields = ['id', 'name', 'type', 'description']

        for model_id, config in manager.models_config['available_models'].items():
            for field in required_fields:
                assert field in config, f"Model {model_id} missing field {field}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
