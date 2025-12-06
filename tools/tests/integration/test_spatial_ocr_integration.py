"""
Integration tests for Spatial OCR with Model Manager

Tests that the spatial OCR processor integrates correctly with the model manager.
"""

import pytest
from shared.models.manager import ModelManager, ModelType, ProcessorFactory


class TestSpatialOCRIntegration:
    """Test spatial OCR integration with model manager."""
    
    def test_spatial_type_exists(self):
        """Test that spatial OCR processor types are defined."""
        # Check that spatial processor types exist in registry
        registry = ProcessorFactory._REGISTRY
        
        # There should be spatial-related types registered
        spatial_types = [k for k in registry.keys() if 'spatial' in k.lower()]
        assert len(spatial_types) >= 1, "Expected at least one spatial processor type in registry"
    
    def test_spatial_in_processor_factory_registry(self):
        """Test that spatial processors are in the factory registry."""
        registry = ProcessorFactory._REGISTRY
        
        # Check for spatial processor types
        spatial_types = [k for k in registry.keys() if 'spatial' in k.lower()]
        assert len(spatial_types) >= 1, "Expected spatial processors in registry"
        
        # Verify they have proper structure
        for spatial_type in spatial_types:
            module_path, class_name, error_msg = registry[spatial_type]
            assert module_path is not None
            assert class_name is not None
    
    def test_model_manager_lists_spatial_models(self):
        """Test that model manager includes spatial OCR models in available models."""
        manager = ModelManager()
        available_models = manager.get_available_models()
        
        # Find spatial models (EasyOCR and PaddleOCR spatial variants)
        spatial_models = [m for m in available_models if 'spatial' in m.get('type', '').lower() or m.get('capabilities', {}).get('spatial_analysis', False)]
        
        # Should have at least the two spatial variants
        assert len(spatial_models) >= 2
        
        # Check that at least one has spatial_analysis capability
        has_spatial_capability = any(m.get('capabilities', {}).get('spatial_analysis', False) for m in spatial_models)
        assert has_spatial_capability is True
    
    def test_model_manager_get_spatial_info(self):
        """Test getting spatial model info from manager."""
        manager = ModelManager()
        # Test with actual spatial model that exists
        info = manager.get_model_info('ocr_easyocr_spatial')
        
        assert info is not None
        assert info['id'] == 'ocr_easyocr_spatial'
        assert 'spatial' in info['type'].lower()
        assert 'description' in info
        assert 'bounding box' in info['description'].lower() or 'spatial' in info['description'].lower()
    
    def test_spatial_model_capabilities(self):
        """Test that spatial model has all expected capabilities."""
        manager = ModelManager()
        # Test with actual spatial model
        info = manager.get_model_info('ocr_easyocr_spatial')
        
        capabilities = info['capabilities']
        
        # Standard capabilities
        assert capabilities['store_name'] is True
        assert capabilities['date'] is True
        assert capabilities['total'] is True
        assert capabilities['items'] is True
        
        # Spatial capability
        assert capabilities['spatial_analysis'] is True


class TestProcessorFactoryCreation:
    """Test processor creation through factory."""
    
    def test_can_create_spatial_processor_config(self):
        """Test that factory accepts spatial model config."""
        config = {
            'id': 'ocr_easyocr_spatial',
            'name': 'EasyOCR with Spatial Bounding Boxes',
            'type': 'easyocr_spatial'
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
        
        # Should be able to select an actual spatial model
        success = manager.select_model('ocr_easyocr_spatial')
        
        # If selection fails, it should be due to missing dependencies,
        # not configuration issues
        if not success:
            # Check it's in available models (config is correct)
            available = manager.get_available_models()
            model_ids = [m['id'] for m in available]
            assert 'ocr_easyocr_spatial' in model_ids
    
    def test_spatial_model_not_default(self):
        """Test that spatial models are not the default."""
        manager = ModelManager()
        default = manager.get_default_model()
        
        # Spatial models should not be default (they're slower)
        assert default != 'ocr_easyocr_spatial'
        assert default != 'ocr_paddle_spatial'
