"""
Tests for the shared image processing utilities module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from PIL import Image
import tempfile
import os


class TestLoadAndValidateImage:
    """Tests for load_and_validate_image function."""

    def test_load_valid_rgb_image(self, tmp_path):
        from shared.utils.image_processing import load_and_validate_image
        
        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        image_path = tmp_path / "test.png"
        img.save(str(image_path))
        
        result = load_and_validate_image(str(image_path))
        assert isinstance(result, Image.Image)
        assert result.mode == 'RGB'

    def test_load_grayscale_image(self, tmp_path):
        from shared.utils.image_processing import load_and_validate_image
        
        img = Image.new('L', (100, 100), color=128)
        image_path = tmp_path / "test_gray.png"
        img.save(str(image_path))
        
        result = load_and_validate_image(str(image_path))
        assert isinstance(result, Image.Image)
        assert result.mode == 'L'

    def test_load_rgba_converts_to_rgb(self, tmp_path):
        from shared.utils.image_processing import load_and_validate_image
        
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        image_path = tmp_path / "test_rgba.png"
        img.save(str(image_path))
        
        result = load_and_validate_image(str(image_path))
        assert isinstance(result, Image.Image)
        assert result.mode == 'RGB'

    def test_file_not_found_raises_error(self):
        from shared.utils.image_processing import load_and_validate_image
        
        with pytest.raises(FileNotFoundError):
            load_and_validate_image("/nonexistent/path/image.png")

    def test_empty_file_raises_error(self, tmp_path):
        from shared.utils.image_processing import load_and_validate_image
        
        empty_file = tmp_path / "empty.png"
        empty_file.touch()
        
        with pytest.raises(ValueError):
            load_and_validate_image(str(empty_file))


class TestEnhanceImage:
    """Tests for enhance_image function."""

    def test_enhance_with_defaults(self):
        from shared.utils.image_processing import enhance_image
        
        img = Image.new('RGB', (100, 100), color='gray')
        result = enhance_image(img)
        
        assert isinstance(result, Image.Image)
        assert result.size == img.size

    def test_enhance_brightness_only(self):
        from shared.utils.image_processing import enhance_image
        
        img = Image.new('RGB', (100, 100), color='gray')
        result = enhance_image(img, enhance_brightness=True, enhance_contrast=False, sharpen=False)
        
        assert isinstance(result, Image.Image)

    def test_enhance_contrast_only(self):
        from shared.utils.image_processing import enhance_image
        
        img = Image.new('RGB', (100, 100), color='gray')
        result = enhance_image(img, enhance_brightness=False, enhance_contrast=True, sharpen=False)
        
        assert isinstance(result, Image.Image)

    def test_enhance_sharpen_only(self):
        from shared.utils.image_processing import enhance_image
        
        img = Image.new('RGB', (100, 100), color='gray')
        result = enhance_image(img, enhance_brightness=False, enhance_contrast=False, sharpen=True)
        
        assert isinstance(result, Image.Image)

    def test_enhance_no_enhancement(self):
        from shared.utils.image_processing import enhance_image
        
        img = Image.new('RGB', (100, 100), color='red')
        result = enhance_image(img, enhance_brightness=False, enhance_contrast=False, sharpen=False)
        
        assert isinstance(result, Image.Image)


class TestAssessImageQuality:
    """Tests for assess_image_quality function."""

    @patch('shared.utils.image_processing._estimate_blur')
    @patch('shared.utils.image_processing._estimate_noise')
    def test_assess_bright_image(self, mock_noise, mock_blur):
        from shared.utils.image_processing import assess_image_quality
        
        mock_blur.return_value = 150.0
        mock_noise.return_value = 10.0
        
        img = Image.new('RGB', (100, 100), color='white')
        result = assess_image_quality(img)
        
        assert 'brightness' in result
        assert 'contrast' in result
        assert 'is_bright_enough' in result
        assert result['brightness'] > 200  # White image should be bright

    @patch('shared.utils.image_processing._estimate_blur')
    @patch('shared.utils.image_processing._estimate_noise')
    def test_assess_dark_image(self, mock_noise, mock_blur):
        from shared.utils.image_processing import assess_image_quality
        
        mock_blur.return_value = 150.0
        mock_noise.return_value = 10.0
        
        img = Image.new('RGB', (100, 100), color='black')
        result = assess_image_quality(img)
        
        assert result['brightness'] < 10  # Black image should be dark
        assert result['is_bright_enough'] == False

    @patch('shared.utils.image_processing._estimate_blur')
    @patch('shared.utils.image_processing._estimate_noise')
    def test_quality_overall_good(self, mock_noise, mock_blur):
        from shared.utils.image_processing import assess_image_quality
        
        mock_blur.return_value = 150.0
        mock_noise.return_value = 10.0
        
        # Create an image with good brightness and varied content for contrast
        img = Image.new('RGB', (100, 100))
        pixels = img.load()
        for i in range(100):
            for j in range(100):
                gray = 150 + (i % 50)  # Creates variation
                pixels[i, j] = (gray, gray, gray)
        
        result = assess_image_quality(img)
        assert 'overall_quality' in result


class TestPreprocessForOcr:
    """Tests for preprocess_for_ocr function."""

    @patch('cv2.Laplacian')
    @patch('cv2.cvtColor')
    @patch('cv2.adaptiveThreshold')
    @patch('cv2.fastNlMeansDenoising')
    def test_non_aggressive_mode(self, mock_denoise, mock_thresh, mock_cvt, mock_lap):
        from shared.utils.image_processing import preprocess_for_ocr
        
        img = Image.new('RGB', (100, 100), color='white')
        mock_cvt.return_value = np.ones((100, 100), dtype=np.uint8) * 255
        mock_thresh.return_value = np.ones((100, 100), dtype=np.uint8) * 255
        mock_denoise.return_value = np.ones((100, 100), dtype=np.uint8) * 255
        
        result = preprocess_for_ocr(img, aggressive=False)
        assert isinstance(result, Image.Image)


class TestBrightnessThreshold:
    """Tests for brightness threshold constant."""

    def test_brightness_threshold_defined(self):
        from shared.utils.image_processing import BRIGHTNESS_THRESHOLD
        assert BRIGHTNESS_THRESHOLD == 100


class TestContrastThreshold:
    """Tests for contrast threshold constant."""

    def test_contrast_threshold_defined(self):
        from shared.utils.image_processing import CONTRAST_THRESHOLD
        assert CONTRAST_THRESHOLD == 40
