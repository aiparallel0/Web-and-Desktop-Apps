"""
Image preprocessing utilities for receipt extraction
Shared across all models and applications
"""
import os
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
        # Check if file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Check if file is readable
        if not os.access(image_path, os.R_OK):
            raise PermissionError(f"Cannot read image file: {image_path}")

        # Check file size
        file_size = os.path.getsize(image_path)
        if file_size == 0:
            raise ValueError(f"Image file is empty: {image_path}")

        logger.info(f"Loading image from: {image_path} (size: {file_size} bytes)")

        image = Image.open(image_path)

        if image is None:
            raise ValueError(f"PIL failed to load image: {image_path}")

        # Convert to RGB if needed, handling alpha channel appropriately
        if image.mode not in ('RGB', 'L'):
            if image.mode == 'RGBA':
                # Create a white background for RGBA images
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
                image = background
            else:
                # For other modes, direct conversion
                image = image.convert('RGB')

        logger.info(f"Loaded image successfully: {image.size[0]}x{image.size[1]}")
        return image
    except Exception as e:
        logger.error(f"Failed to load image from {image_path}: {e}")
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


def preprocess_for_ocr(image: Image.Image, aggressive: bool = True) -> Image.Image:
    """
    Preprocess image specifically for OCR with aggressive thermal receipt optimization

    Args:
        image: Input PIL Image
        aggressive: If True, applies aggressive preprocessing for low-quality receipts

    Returns:
        Preprocessed PIL Image optimized for OCR
    """
    import cv2

    try:
        # Convert to numpy array
        img_array = np.array(image)

        # Validate array
        if img_array is None or img_array.size == 0:
            raise ValueError("Image array is empty or None")

        logger.info(f"Image array shape: {img_array.shape}")

        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        if aggressive:
            # AGGRESSIVE PREPROCESSING FOR THERMAL RECEIPTS

            # Step 1: Upscale if resolution is too low (improves OCR accuracy)
            height, width = gray.shape
            if max(height, width) < 1000:
                scale_factor = 1500 / max(height, width)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                logger.info(f"Upscaled image from {width}x{height} to {new_width}x{new_height}")

            # Step 2: Deskew (fix rotation) - critical for receipts
            gray = _deskew_image(gray)

            # Step 3: Denoise BEFORE contrast enhancement
            gray = cv2.fastNlMeansDenoising(gray, h=10)

            # Step 4: CLAHE (Contrast Limited Adaptive Histogram Equalization)
            # This is CRITICAL for faded thermal receipts
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)

            # Step 5: Bilateral filter to preserve edges while smoothing
            gray = cv2.bilateralFilter(gray, 9, 75, 75)

            # Step 6: Otsu's binarization (better than adaptive for receipts)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Step 7: Morphological operations to clean up noise
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            # Step 8: Invert if background is dark (some receipts)
            if np.mean(binary) < 127:
                binary = cv2.bitwise_not(binary)
                logger.info("Inverted image (dark background detected)")

            result = Image.fromarray(binary)
            logger.info("Aggressive OCR preprocessing complete")

        else:
            # STANDARD PREPROCESSING
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            # Denoise
            denoised = cv2.fastNlMeansDenoising(binary)

            result = Image.fromarray(denoised)
            logger.info("Standard OCR preprocessing complete")

        return result

    except Exception as e:
        logger.warning(f"OCR preprocessing failed, using enhanced image: {e}")
        return enhance_image(image)


def _deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Detect and correct skew in receipt images

    Args:
        image: Grayscale numpy array

    Returns:
        Deskewed image
    """
    import cv2

    try:
        # Compute angle using Hough transform
        coords = np.column_stack(np.where(image > 0))

        if len(coords) < 10:
            logger.warning("Not enough edge points for deskewing")
            return image

        angle = cv2.minAreaRect(coords)[-1]

        # Correct angle range
        if angle < -45:
            angle = 90 + angle
        elif angle > 45:
            angle = angle - 90

        # Only correct if skew is significant (> 0.5 degrees)
        if abs(angle) < 0.5:
            logger.info(f"Skew angle {angle:.2f}° is negligible, skipping correction")
            return image

        # Rotate image
        (h, w) = image.shape
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        logger.info(f"Deskewed image by {angle:.2f} degrees")
        return rotated

    except Exception as e:
        logger.warning(f"Deskew failed: {e}")
        return image


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
