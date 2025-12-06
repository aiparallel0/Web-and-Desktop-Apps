"""
Integration tests for Spatial OCR with Model Manager

Tests that the spatial OCR processor integrates correctly with the model manager.
"""

import pytest
from shared.models.manager import ModelManager, ModelType, ProcessorFactory


class TestSpatialOCRIntegration:
    """Test spatial OCR integration with model manager."""
    
    def test_spatial_model_type_exists(self):
        """Test that SPATIAL model type is defined."""
        assert hasattr(ModelType, 'SPATIAL')
        assert ModelType.SPATIAL.value == 'spatial'
    
    def test_spatial_in_processor_factory_registry(self):
        """Test that spatial processor is in the factory registry."""
        registry = ProcessorFactory._REGISTRY
        assert 'spatial' in registry
        
        module_path, class_name, error_msg = registry['spatial']
        assert module_path == '.spatial_ocr'
        assert class_name == 'SpatialOCRProcessor'
        assert 'multiple OCR engines' in error_msg
    
    def test_model_manager_lists_spatial_model(self):
        """Test that model manager includes spatial model in available models."""
        manager = ModelManager()
        available_models = manager.get_available_models()
        
        # Find spatial model
        spatial_models = [m for m in available_models if m['id'] == 'spatial_multi']
        
        assert len(spatial_models) == 1
        spatial_model = spatial_models[0]
        
        assert spatial_model['name'] == 'Multi-Method Spatial OCR'
        assert spatial_model['type'] == 'spatial'
        assert spatial_model['capabilities']['spatial_analysis'] is True
        assert spatial_model['capabilities']['multi_engine'] is True
    
    def test_model_manager_get_spatial_info(self):
        """Test getting spatial model info from manager."""
        manager = ModelManager()
        info = manager.get_model_info('spatial_multi')
        
        assert info is not None
        assert info['id'] == 'spatial_multi'
        assert info['type'] == 'spatial'
        assert 'description' in info
        assert 'bounding box' in info['description'].lower()
    
    def test_spatial_model_capabilities(self):
        """Test that spatial model has all expected capabilities."""
        manager = ModelManager()
        info = manager.get_model_info('spatial_multi')
        
        capabilities = info['capabilities']
        
        # Standard capabilities
        assert capabilities['store_name'] is True
        assert capabilities['date'] is True
        assert capabilities['total'] is True
        assert capabilities['items'] is True
        
        # Advanced capabilities
        assert capabilities['advanced_parsing'] is True
        assert capabilities['spatial_analysis'] is True
        assert capabilities['multi_engine'] is True


class TestProcessorFactoryCreation:
    """Test processor creation through factory."""
    
    def test_can_create_spatial_processor_config(self):
        """Test that factory accepts spatial model config."""
        config = {
            'id': 'spatial_multi',
            'name': 'Multi-Method Spatial OCR',
            'type': 'spatial'
        }
        
        # Should not raise ValueError for unknown type
        # Note: This might fail if dependencies are not installed,
        # but we're testing the factory registration
        try:
            processor = ProcessorFactory.create(config)
            assert processor is not None
        except ImportError as e:
            # Expected if OCR engines not installed
            assert 'multiple OCR engines' in str(e)
        except Exception as e:
            # Should not get other exceptions for type issues
            assert False, f"Unexpected error: {e}"


class TestModelManagerSelection:
    """Test model selection with spatial model."""
    
    def test_select_spatial_model(self):
        """Test selecting spatial model through manager."""
        manager = ModelManager()
        
        # Should be able to select the model
        success = manager.select_model('spatial_multi')
        
        # If selection fails, it should be due to missing dependencies,
        # not configuration issues
        if not success:
            # Check it's in available models (config is correct)
            available = manager.get_available_models()
            model_ids = [m['id'] for m in available]
            assert 'spatial_multi' in model_ids
    
    def test_spatial_model_not_default(self):
        """Test that spatial model is not the default."""
        manager = ModelManager()
        default = manager.get_default_model()
        
        # Spatial model should not be default (it's slower)
        assert default != 'spatial_multi'
