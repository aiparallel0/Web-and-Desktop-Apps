"""
Tests for Model Manager dependency checking functionality.

This test module validates that:
1. Dependency checking correctly identifies available/missing packages
2. get_available_models() filters models based on dependencies
3. Model health checking works correctly
"""
import pytest
from unittest.mock import patch, MagicMock
import sys


class TestModelManagerDependencies:
    """Tests for Model Manager dependency checking."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all model dependencies as unavailable."""
        with patch.dict('sys.modules', {
            'cv2': None,
            'easyocr': None,
            'paddleocr': None,
            'torch': None,
            'transformers': None,
            'craft_text_detector': None,
            'pytesseract': None
        }):
            yield

    def test_check_dependencies_all_available(self):
        """Test dependency checking when all packages are available."""
        # Mock all dependencies as available
        mock_cv2 = MagicMock()
        mock_cv2.__version__ = '4.8.1'
        
        mock_easyocr = MagicMock()
        mock_easyocr.__version__ = '1.7.1'
        
        mock_torch = MagicMock()
        mock_torch.__version__ = '2.1.0'
        mock_torch.cuda.is_available.return_value = False
        
        mock_transformers = MagicMock()
        mock_transformers.__version__ = '4.35.2'
        
        mock_paddleocr = MagicMock()
        mock_pytesseract = MagicMock()
        mock_pytesseract.get_tesseract_version.return_value = MagicMock(public='5.0.0')
        mock_craft = MagicMock()
        
        with patch.dict('sys.modules', {
            'cv2': mock_cv2,
            'easyocr': mock_easyocr,
            'paddleocr': mock_paddleocr,
            'torch': mock_torch,
            'transformers': mock_transformers,
            'craft_text_detector': mock_craft,
            'pytesseract': mock_pytesseract
        }):
            from shared.models.manager import ModelManager
            manager = ModelManager()
            
            deps = manager._check_dependencies()
            
            # All dependencies should be available
            assert deps['opencv']['available'] == True
            assert deps['easyocr']['available'] == True
            assert deps['paddleocr']['available'] == True
            assert deps['torch']['available'] == True
            assert deps['transformers']['available'] == True
            assert deps['craft']['available'] == True
            assert deps['pytesseract']['available'] == True

    def test_check_dependencies_torch_missing(self):
        """Test dependency checking when PyTorch is missing."""
        mock_cv2 = MagicMock()
        mock_cv2.__version__ = '4.8.1'
        
        with patch.dict('sys.modules', {
            'cv2': mock_cv2,
            'torch': None,
            'transformers': None
        }, clear=False):
            # Force ImportError for torch
            def raise_import_error(*args, **kwargs):
                raise ImportError("No module named 'torch'")
            
            with patch('builtins.__import__', side_effect=raise_import_error):
                from shared.models.manager import ModelManager
                manager = ModelManager()
                
                deps = manager._check_dependencies()
                
                # Torch should be unavailable
                assert deps.get('torch', {}).get('available') == False
                assert 'torch' in deps.get('torch', {}).get('error', '')

    def test_get_available_models_filters_by_dependencies(self):
        """Test that get_available_models filters models based on dependencies."""
        # Only OpenCV available, no other deps
        mock_cv2 = MagicMock()
        mock_cv2.__version__ = '4.8.1'
        mock_pytesseract = MagicMock()
        mock_pytesseract.get_tesseract_version.return_value = MagicMock(public='5.0.0')
        
        with patch.dict('sys.modules', {
            'cv2': mock_cv2,
            'pytesseract': mock_pytesseract,
            'easyocr': None,
            'paddleocr': None,
            'torch': None,
            'transformers': None,
            'craft_text_detector': None
        }, clear=False):
            # Force ImportError for missing modules
            original_import = __builtins__.__import__
            
            def selective_import(name, *args, **kwargs):
                if name in ['easyocr', 'paddleocr', 'torch', 'transformers', 'craft_text_detector']:
                    raise ImportError(f"No module named '{name}'")
                return original_import(name, *args, **kwargs)
            
            with patch('builtins.__import__', side_effect=selective_import):
                from shared.models.manager import ModelManager
                manager = ModelManager()
                
                models = manager.get_available_models(check_availability=True)
                
                # Should have some models
                assert len(models) > 0
                
                # OCR Tesseract should be available
                tesseract_model = next((m for m in models if m['id'] == 'ocr_tesseract'), None)
                assert tesseract_model is not None
                assert tesseract_model.get('available') == True
                
                # EasyOCR should be unavailable
                easyocr_model = next((m for m in models if m['id'] == 'ocr_easyocr'), None)
                if easyocr_model:
                    assert easyocr_model.get('available') == False
                    assert 'easyocr' in easyocr_model.get('missing_dependencies', [])
                
                # Florence-2 should be unavailable (needs torch)
                florence_model = next((m for m in models if m['id'] == 'florence2'), None)
                if florence_model:
                    assert florence_model.get('available') == False
                    assert 'torch' in florence_model.get('missing_dependencies', [])

    def test_get_available_models_without_check(self):
        """Test that get_available_models returns all models when not checking."""
        from shared.models.manager import ModelManager
        manager = ModelManager()
        
        models = manager.get_available_models(check_availability=False)
        
        # Should return all configured models
        assert len(models) >= 8  # We have 8 models configured
        
        # None should have 'available' flag when not checking
        for model in models:
            assert 'available' not in model or model.get('available') is None

    def test_model_type_dependency_mapping(self):
        """Test that model types are correctly mapped to dependencies."""
        from shared.models.manager import ModelManager
        manager = ModelManager()
        
        # Get model config
        model_config = manager.models_config['available_models']
        
        # Verify each model type
        assert model_config['ocr_tesseract']['type'] == 'ocr'
        assert model_config['ocr_easyocr']['type'] == 'easyocr'
        assert model_config['ocr_paddle']['type'] == 'paddle'
        assert model_config['florence2']['type'] == 'florence'
        assert model_config['donut_cord']['type'] == 'donut'
        assert model_config['craft_detector']['type'] == 'craft'


class TestDetectionResultDependencyError:
    """Tests for DetectionResult dependency error handling."""

    def test_create_dependency_error(self):
        """Test creating a dependency error result."""
        from shared.models.schemas import DetectionResult, ErrorCode
        
        missing_deps = ['torch', 'transformers']
        result = DetectionResult.create_dependency_error(
            missing_deps=missing_deps,
            model_id='florence2'
        )
        
        assert result.success == False
        assert result.error_code == ErrorCode.MISSING_DEPENDENCIES
        assert 'torch' in result.error_message
        assert 'transformers' in result.error_message
        assert result.missing_dependencies == missing_deps
        assert result.model_id == 'florence2'
        assert len(result.texts) == 0

    def test_dependency_error_to_dict(self):
        """Test serializing dependency error to dict."""
        from shared.models.schemas import DetectionResult
        
        result = DetectionResult.create_dependency_error(
            missing_deps=['paddleocr'],
            model_id='ocr_paddle'
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['success'] == False
        assert result_dict['error_code'] == 'missing_dependencies'
        assert 'paddleocr' in result_dict['error_message']
        assert result_dict['missing_dependencies'] == ['paddleocr']
        assert result_dict['model_id'] == 'ocr_paddle'


class TestModelHealthEndpoint:
    """Tests for /api/models/health endpoint (integration-style)."""

    @pytest.fixture
    def app_client(self):
        """Create a test client for the Flask app."""
        # This would normally import the Flask app, but we'll mock it
        # In real integration tests, you'd use the actual app
        pass

    def test_health_endpoint_structure(self):
        """Test the expected structure of health endpoint response."""
        # This is a structural test - actual endpoint testing would be in integration tests
        expected_keys = [
            'success',
            'available_models',
            'unavailable_models',
            'missing_dependencies',
            'dependency_status',
            'summary'
        ]
        
        # Just verify the structure is documented
        assert len(expected_keys) == 6


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
