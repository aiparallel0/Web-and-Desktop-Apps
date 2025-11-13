"""
Unit tests for image processing utilities.
"""

import pytest
from PIL import Image
import io
import numpy as np
from shared.utils.image_processing import (
    load_and_validate_image,
    enhance_image,
    assess_image_quality,
    resize_if_needed,
    BRIGHTNESS_THRESHOLD,
    CONTRAST_THRESHOLD
)
import tempfile


@pytest.mark.unit
def test_image_formats_supported():
    """Test that common image formats can be processed."""
    # Create test images in different formats
    formats = ['JPEG', 'PNG', 'BMP', 'TIFF']

    for fmt in formats:
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format=fmt)
        buffer.seek(0)

        # Try to open it
        loaded_img = Image.open(buffer)
        assert loaded_img.size == (100, 100), f"{fmt} image should be loadable"


@pytest.mark.unit
def test_image_validation():
    """Test image file validation logic."""
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    invalid_extensions = ['.pdf', '.txt', '.doc', '.exe']

    for ext in valid_extensions:
        # These should be considered valid
        filename = f"test{ext}"
        assert any(filename.endswith(valid_ext) for valid_ext in valid_extensions)

    for ext in invalid_extensions:
        # These should not match valid extensions
        filename = f"test{ext}"
        assert not any(filename.endswith(valid_ext) for valid_ext in valid_extensions)


@pytest.mark.unit
def test_load_and_validate_image():
    """Test loading and validating image files."""
    # Create a temporary test image
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        img = Image.new('RGB', (200, 150), color='blue')
        img.save(tmp_file.name)
        tmp_path = tmp_file.name

    # Test loading the image
    loaded_img = load_and_validate_image(tmp_path)
    assert loaded_img.size == (200, 150)
    assert loaded_img.mode == 'RGB'

    # Close the image to release the file handle (important for Windows)
    loaded_img.close()

    # Clean up
    import os
    os.unlink(tmp_path)


@pytest.mark.unit
def test_enhance_image():
    """Test image enhancement for better OCR."""
    # Create a test image
    img = Image.new('RGB', (100, 100), color='gray')

    # Test enhancement with all options
    enhanced = enhance_image(img, enhance_contrast=True, enhance_brightness=True, sharpen=True)
    assert enhanced.size == img.size
    assert enhanced.mode == 'RGB'

    # Test enhancement with only contrast
    enhanced_contrast = enhance_image(img, enhance_contrast=True, enhance_brightness=False, sharpen=False)
    assert enhanced_contrast.size == img.size


@pytest.mark.unit
def test_assess_image_quality():
    """Test image quality assessment."""
    # Create a bright, high-contrast test image
    img = Image.new('RGB', (100, 100), color='white')
    quality = assess_image_quality(img)

    assert 'brightness' in quality
    assert 'contrast' in quality
    assert 'is_bright_enough' in quality
    assert 'has_good_contrast' in quality
    assert 'overall_quality' in quality
    assert isinstance(quality['brightness'], float)
    assert isinstance(quality['contrast'], float)


@pytest.mark.unit
def test_resize_if_needed():
    """Test image resizing functionality."""
    # Test image that doesn't need resizing
    small_img = Image.new('RGB', (100, 100), color='red')
    resized = resize_if_needed(small_img, max_size=2048)
    assert resized.size == (100, 100)

    # Test image that needs resizing
    large_img = Image.new('RGB', (3000, 2000), color='green')
    resized = resize_if_needed(large_img, max_size=2048)
    assert max(resized.size) == 2048
    assert resized.size[0] / resized.size[1] == pytest.approx(3000 / 2000, rel=0.01)


@pytest.mark.unit
def test_brightness_and_contrast_thresholds():
    """Test that quality thresholds are properly defined."""
    assert BRIGHTNESS_THRESHOLD > 0
    assert CONTRAST_THRESHOLD > 0
