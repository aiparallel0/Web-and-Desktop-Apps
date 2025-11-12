"""
Image preprocessing utilities for receipt extraction
Shared across all models and applications
"""
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import logging

logger = logging.getLogger(__name__)

# Quality thresholds
BRIGHTNESS_THRESHOLD = 100
CONTRAST_THRESHOLD = 40


def load_and_validate_image(image_path: str) -> Image.Image:
    """Load and validate image file"""
    try:
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        logger.info(f"Loaded image: {image.size[0]}x{image.size[1]}")
        return image
    except Exception as e:
        logger.error(f"Failed to load image: {e}")
        raise


def enhance_image(image: Image.Image, enhance_contrast: bool = True,
                  enhance_brightness: bool = True, sharpen: bool = True) -> Image.Image:
    """Apply image enhancements for better OCR results"""
    try:
        enhanced = image.copy()

        if enhance_brightness:
            enhancer = ImageEnhance.Brightness(enhanced)
            enhanced = enhancer.enhance(1.2)

        if enhance_contrast:
            enhancer = ImageEnhance.Contrast(enhanced)
            enhanced = enhancer.enhance(1.3)

        if sharpen:
            enhanced = enhanced.filter(ImageFilter.SHARPEN)

        logger.info("Image enhancement applied")
        return enhanced
    except Exception as e:
        logger.warning(f"Enhancement failed, using original: {e}")
        return image


def assess_image_quality(image: Image.Image) -> dict:
    """Assess image quality for OCR processing"""
    try:
        img_array = np.array(image.convert('L'))
        brightness = np.mean(img_array)
        contrast = np.std(img_array)

        quality = {
            'brightness': float(brightness),
            'contrast': float(contrast),
            'is_bright_enough': brightness > BRIGHTNESS_THRESHOLD,
            'has_good_contrast': contrast > CONTRAST_THRESHOLD,
            'overall_quality': 'good' if (brightness > BRIGHTNESS_THRESHOLD and
                                         contrast > CONTRAST_THRESHOLD) else 'poor'
        }

        logger.info(f"Image quality: brightness={brightness:.1f}, contrast={contrast:.1f}")
        return quality
    except Exception as e:
        logger.error(f"Quality assessment failed: {e}")
        return {'overall_quality': 'unknown'}


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """Preprocess image specifically for OCR"""
    import cv2

    try:
        # Convert to numpy array
        img_array = np.array(image)

        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Denoise
        denoised = cv2.fastNlMeansDenoising(binary)

        # Convert back to PIL Image
        result = Image.fromarray(denoised)
        logger.info("OCR preprocessing complete")
        return result
    except Exception as e:
        logger.warning(f"OCR preprocessing failed, using enhanced image: {e}")
        return enhance_image(image)


def resize_if_needed(image: Image.Image, max_size: int = 2048) -> Image.Image:
    """Resize image if it exceeds max dimension"""
    width, height = image.size
    if max(width, height) > max_size:
        ratio = max_size / max(width, height)
        new_size = (int(width * ratio), int(height * ratio))
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        logger.info(f"Resized image from {image.size} to {new_size}")
        return resized
    return image
