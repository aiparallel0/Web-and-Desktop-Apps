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
    formats = ['JPEG', 'PNG', 'BMP', 'TIFF']
    for fmt in formats:
        img = Image.new('RGB', (100, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format=fmt)
        buffer.seek(0)
        loaded_img = Image.open(buffer)
        assert loaded_img.size == (100, 100), f"{fmt} image should be loadable"

@pytest.mark.unit
def test_image_validation():
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    invalid_extensions = ['.pdf', '.txt', '.doc', '.exe']
    for ext in valid_extensions:
        filename = f"test{ext}"
        assert any(filename.endswith(valid_ext) for valid_ext in valid_extensions)
    for ext in invalid_extensions:
        filename = f"test{ext}"
        assert not any(filename.endswith(valid_ext) for valid_ext in valid_extensions)

@pytest.mark.unit
def test_load_and_validate_image():
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        img = Image.new('RGB', (200, 150), color='blue')
        img.save(tmp_file.name)
        tmp_path = tmp_file.name
    loaded_img = load_and_validate_image(tmp_path)
    assert loaded_img.size == (200, 150)
    assert loaded_img.mode == 'RGB'
    loaded_img.close()
    import os
    os.unlink(tmp_path)

@pytest.mark.unit
def test_enhance_image():
    img = Image.new('RGB', (100, 100), color='gray')
    enhanced = enhance_image(img, enhance_contrast=True, enhance_brightness=True, sharpen=True)
    assert enhanced.size == img.size
    assert enhanced.mode == 'RGB'
    enhanced_contrast = enhance_image(img, enhance_contrast=True, enhance_brightness=False, sharpen=False)
    assert enhanced_contrast.size == img.size

@pytest.mark.unit
def test_assess_image_quality():
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
    small_img = Image.new('RGB', (100, 100), color='red')
    resized = resize_if_needed(small_img, max_size=2048)
    assert resized.size == (100, 100)
    large_img = Image.new('RGB', (3000, 2000), color='green')
    resized = resize_if_needed(large_img, max_size=2048)
    assert max(resized.size) == 2048
    assert resized.size[0] / resized.size[1] == pytest.approx(3000 / 2000, rel=0.01)

@pytest.mark.unit
def test_brightness_and_contrast_thresholds():
    assert BRIGHTNESS_THRESHOLD > 0
    assert CONTRAST_THRESHOLD > 0

@pytest.mark.unit
def test_load_and_validate_image_not_found():
    """Test loading non-existent image raises FileNotFoundError"""
    with pytest.raises(FileNotFoundError):
        load_and_validate_image('/nonexistent/path/image.png')

@pytest.mark.unit
def test_load_and_validate_image_rgba():
    """Test loading RGBA image converts to RGB"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        img.save(tmp_file.name)
        tmp_path = tmp_file.name
    loaded_img = load_and_validate_image(tmp_path)
    assert loaded_img.mode == 'RGB'
    loaded_img.close()
    import os
    os.unlink(tmp_path)

@pytest.mark.unit
def test_load_and_validate_image_grayscale():
    """Test loading grayscale image (L mode)"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        img = Image.new('L', (100, 100), color=128)
        img.save(tmp_file.name)
        tmp_path = tmp_file.name
    loaded_img = load_and_validate_image(tmp_path)
    assert loaded_img.mode in ('L', 'RGB')
    loaded_img.close()
    import os
    os.unlink(tmp_path)

@pytest.mark.unit
def test_enhance_image_no_changes():
    """Test enhance_image with all options disabled"""
    img = Image.new('RGB', (100, 100), color='gray')
    enhanced = enhance_image(img, enhance_contrast=False, enhance_brightness=False, sharpen=False)
    assert enhanced.size == img.size

@pytest.mark.unit
def test_assess_image_quality_dark_image():
    """Test quality assessment for dark image"""
    img = Image.new('RGB', (100, 100), color='black')
    quality = assess_image_quality(img)
    assert quality['brightness'] < BRIGHTNESS_THRESHOLD
    assert quality['is_bright_enough'] == False

@pytest.mark.unit
def test_assess_image_quality_low_contrast():
    """Test quality assessment for low contrast image"""
    img = Image.new('RGB', (100, 100), color=(128, 128, 128))
    quality = assess_image_quality(img)
    assert quality['contrast'] < CONTRAST_THRESHOLD
    assert quality['has_good_contrast'] == False

@pytest.mark.unit
def test_resize_if_needed_width_larger():
    """Test resize when width is larger dimension"""
    large_img = Image.new('RGB', (4000, 2000), color='blue')
    resized = resize_if_needed(large_img, max_size=2048)
    assert resized.size[0] == 2048
    assert resized.size[1] == 1024

@pytest.mark.unit
def test_resize_if_needed_height_larger():
    """Test resize when height is larger dimension"""
    large_img = Image.new('RGB', (2000, 4000), color='blue')
    resized = resize_if_needed(large_img, max_size=2048)
    assert resized.size[0] == 1024
    assert resized.size[1] == 2048
