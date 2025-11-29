"""
Test suite for shared.models.__init__.py
Tests the _get_processor_class lazy import functionality
"""
import pytest
from pathlib import Path
import sys

# Add shared to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'shared'))

from models import ModelManager, _get_processor_class


class TestModelManager:
    """Test ModelManager export"""

    def test_model_manager_import(self):
        """Test that ModelManager is exported"""
        assert ModelManager is not None


class TestGetProcessorClass:
    """Test _get_processor_class lazy import function"""

    def test_get_processor_class_invalid_type(self):
        """Test that invalid processor type raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            _get_processor_class('invalid_type')
        
        assert 'Unknown processor type' in str(exc_info.value)

    def test_get_processor_class_donut(self):
        """Test getting donut processor class"""
        try:
            processor_class = _get_processor_class('donut')
            assert processor_class is not None
            assert processor_class.__name__ == 'DonutProcessor'
        except ImportError:
            # torch not installed - expected in test environment
            pytest.skip("torch not installed")

    def test_get_processor_class_florence(self):
        """Test getting florence processor class"""
        try:
            processor_class = _get_processor_class('florence')
            assert processor_class is not None
            assert processor_class.__name__ == 'FlorenceProcessor'
        except ImportError:
            pytest.skip("torch not installed")

    def test_get_processor_class_ocr(self):
        """Test getting OCR processor class"""
        try:
            processor_class = _get_processor_class('ocr')
            assert processor_class is not None
            assert processor_class.__name__ == 'OCRProcessor'
        except ImportError:
            pytest.skip("pytesseract not installed")

    def test_get_processor_class_paddle(self):
        """Test getting paddle processor class"""
        try:
            processor_class = _get_processor_class('paddle')
            assert processor_class is not None
            assert processor_class.__name__ == 'PaddleProcessor'
        except ImportError:
            pytest.skip("paddleocr not installed")

    def test_get_processor_class_easyocr(self):
        """Test getting easyocr processor class"""
        try:
            processor_class = _get_processor_class('easyocr')
            assert processor_class is not None
            assert processor_class.__name__ == 'EasyOCRProcessor'
        except ImportError:
            pytest.skip("easyocr not installed")
