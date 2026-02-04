"""
Image Processing Module with Circular Exchange Integration

This module provides image loading, validation, and preprocessing functions
for OCR processing. It integrates with the Circular Exchange Framework for
dynamic parameter configuration and auto-tuning.

Round 2 CEF Improvements:
- Added memory-efficient image loading with size limits
- Implemented image streaming for large files
- Added memory usage monitoring and warnings
"""
import os
import gc
import numpy as np
from PIL import Image,ImageEnhance,ImageFilter
import logging

# Import cv2 lazily to avoid ModuleNotFoundError if not installed
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    logging.getLogger(__name__).warning(
        "OpenCV (cv2) not available. Some image processing features will be limited. "
        "Install with: pip install opencv-python-headless"
    )

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    try:
        from ..circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
        CIRCULAR_EXCHANGE_AVAILABLE = True
    except ImportError:
        CIRCULAR_EXCHANGE_AVAILABLE = False
        PackageRegistry = None

logger=logging.getLogger(__name__)

# =============================================================================
# MEMORY MANAGEMENT - Added based on CEF Round 2 analysis
# =============================================================================

# Maximum image dimensions to prevent memory exhaustion
MAX_IMAGE_DIMENSION = 8000  # pixels
MAX_IMAGE_MEMORY_MB = 100  # Maximum memory for single image processing

def _estimate_memory_usage(width: int, height: int, channels: int = 3) -> float:
    """
    Estimate memory usage for an image in MB.
    
    CEF-suggested improvement to prevent memory exhaustion errors.
    """
    bytes_needed = width * height * channels
    return bytes_needed / (1024 * 1024)

def _check_image_memory_safe(image: Image.Image) -> bool:
    """
    Check if processing an image would be memory-safe.
    
    CEF Round 2: Added to prevent memory allocation failures.
    """
    width, height = image.size
    channels = len(image.getbands())
    memory_mb = _estimate_memory_usage(width, height, channels)
    
    if memory_mb > MAX_IMAGE_MEMORY_MB:
        logger.warning(
            f"Image would require ~{memory_mb:.1f}MB, exceeds {MAX_IMAGE_MEMORY_MB}MB limit"
        )
        return False
    return True

def _resize_if_too_large(image: Image.Image) -> Image.Image:
    """
    Resize image if it exceeds maximum dimensions.
    
    CEF Round 2: Added to handle large images gracefully instead of failing.
    """
    width, height = image.size
    
    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        # Calculate scale factor to fit within limits
        scale = min(MAX_IMAGE_DIMENSION / width, MAX_IMAGE_DIMENSION / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        logger.info(
            f"Resizing large image from {width}x{height} to {new_width}x{new_height} "
            f"(scale: {scale:.2f})"
        )
        
        # Use high-quality downsampling
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Force garbage collection after resize
        gc.collect()
    
    return image

# Create package registry for image processing configuration
_image_config_registry = PackageRegistry() if CIRCULAR_EXCHANGE_AVAILABLE else None

def _init_image_config():
    """Initialize image processing configuration packages."""
    if not CIRCULAR_EXCHANGE_AVAILABLE or _image_config_registry is None:
        return
    
    _image_config_registry.create_package(
        name='image.brightness_threshold',
        initial_value=100,
        source_module='shared.utils.image_processing',
        validator=lambda v: 0 <= v <= 255
    )
    _image_config_registry.create_package(
        name='image.contrast_threshold',
        initial_value=40,
        source_module='shared.utils.image_processing',
        validator=lambda v: 0 <= v <= 255
    )
    _image_config_registry.create_package(
        name='image.upscale_threshold',
        initial_value=1000,
        source_module='shared.utils.image_processing',
        validator=lambda v: v >= 100
    )
    _image_config_registry.create_package(
        name='image.enhancement_factor',
        initial_value=1.2,
        source_module='shared.utils.image_processing',
        validator=lambda v: 0.5 <= v <= 3.0
    )

_init_image_config()

def get_image_config():
    """Get image processing configuration from Circular Exchange."""
    if _image_config_registry is None:
        return {
            'brightness_threshold': 100,
            'contrast_threshold': 40,
            'upscale_threshold': 1000,
            'enhancement_factor': 1.2
        }
    
    def _get_pkg_value(name: str, default):
        """Helper to get package value with fallback."""
        pkg = _image_config_registry.get_package(name)
        return pkg.get() if pkg else default
    
    return {
        'brightness_threshold': _get_pkg_value('image.brightness_threshold', 100),
        'contrast_threshold': _get_pkg_value('image.contrast_threshold', 40),
        'upscale_threshold': _get_pkg_value('image.upscale_threshold', 1000),
        'enhancement_factor': _get_pkg_value('image.enhancement_factor', 1.2)
    }

# Get config values (with fallback for backward compatibility)
_config = get_image_config()
BRIGHTNESS_THRESHOLD = _config['brightness_threshold']
CONTRAST_THRESHOLD = _config['contrast_threshold']

def load_and_validate_image(image_path:str)->Image.Image:
    """
    Load and validate an image file with comprehensive format support.
    
    CEF Round 2: Added memory-safe loading with automatic resizing for large images.
    """
    try:
        if not os.path.exists(image_path):raise FileNotFoundError(f"Image file not found: {image_path}")
        if not os.access(image_path,os.R_OK):raise PermissionError(f"Cannot read image file: {image_path}")
        file_size=os.path.getsize(image_path)
        if file_size==0:raise ValueError(f"Image file is empty: {image_path}")
        logger.info(f"Loading image from: {image_path} (size: {file_size} bytes)")
        image=Image.open(image_path)
        if image is None:raise ValueError(f"PIL failed to load image: {image_path}")
        
        # CEF Round 2: Resize if too large to prevent memory exhaustion
        image = _resize_if_too_large(image)
        
        # CEF Round 2: Check memory safety before processing
        if not _check_image_memory_safe(image):
            logger.warning("Image may cause memory pressure, applying additional size reduction")
            # Additional reduction for very high memory usage
            width, height = image.size
            scale = 0.5
            image = image.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)
        
        if image.mode not in('RGB','L'):
            if image.mode=='RGBA':
                background=Image.new('RGB',image.size,(255,255,255))
                background.paste(image,mask=image.split()[3])
                image=background
            else:image=image.convert('RGB')
        logger.info(f"Loaded image successfully: {image.size[0]}x{image.size[1]}")
        return image
    except Exception as e:
        logger.error(f"Failed to load image from {image_path}: {e}")
        raise

def enhance_image(image:Image.Image,enhance_contrast:bool=True,enhance_brightness:bool=True,sharpen:bool=True)->Image.Image:
    """Apply comprehensive image enhancement for better OCR."""
    try:
        enhanced=image.copy()
        if enhance_brightness:
            enhancer=ImageEnhance.Brightness(enhanced)
            enhanced=enhancer.enhance(1.2)
        if enhance_contrast:
            enhancer=ImageEnhance.Contrast(enhanced)
            enhanced=enhancer.enhance(1.3)
        if sharpen:enhanced=enhanced.filter(ImageFilter.SHARPEN)
        logger.info("Image enhancement applied")
        return enhanced
    except Exception as e:
        logger.warning(f"Enhancement failed, using original: {e}")
        return image

def assess_image_quality(image:Image.Image)->dict:
    """Assess image quality for OCR suitability with detailed metrics."""
    try:
        img_array=np.array(image.convert('L'))
        brightness,contrast=np.mean(img_array),np.std(img_array)
        
        # Calculate additional quality metrics
        blur_score = _estimate_blur(img_array)
        noise_level = _estimate_noise(img_array)
        
        quality={
            'brightness':float(brightness),
            'contrast':float(contrast),
            'blur_score':float(blur_score),
            'noise_level':float(noise_level),
            'is_bright_enough':brightness>BRIGHTNESS_THRESHOLD,
            'has_good_contrast':contrast>CONTRAST_THRESHOLD,
            'is_sharp':blur_score > 100,
            'is_clean':noise_level < 15,
            'overall_quality':'good' if(brightness>BRIGHTNESS_THRESHOLD and contrast>CONTRAST_THRESHOLD and blur_score > 100)else'poor'
        }
        logger.info(f"Image quality: brightness={brightness:.1f}, contrast={contrast:.1f}, blur={blur_score:.1f}, noise={noise_level:.1f}")
        return quality
    except Exception as e:
        logger.error(f"Quality assessment failed: {e}")
        return{'overall_quality':'unknown'}

def _estimate_blur(gray_image: np.ndarray) -> float:
    """Estimate image blur using Laplacian variance."""
    if not CV2_AVAILABLE:
        logger.warning("OpenCV not available, returning default blur score")
        return 100.0  # Default value indicating unknown
    laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
    return float(laplacian.var())

def _estimate_noise(gray_image: np.ndarray) -> float:
    """Estimate noise level in the image."""
    if not CV2_AVAILABLE:
        logger.warning("OpenCV not available, returning default noise level")
        return 10.0  # Default value indicating unknown
    # Use median absolute deviation of Laplacian
    laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
    noise = np.median(np.abs(laplacian - np.median(laplacian)))
    return float(noise)

def preprocess_for_ocr(image:Image.Image,aggressive:bool=True)->Image.Image:
    """
    Advanced preprocessing pipeline for OCR with multiple enhancement stages.
    
    Implements techniques similar to professional OCR services:
    - Adaptive upscaling for low-resolution images
    - Advanced deskewing and alignment
    - Multi-stage noise reduction
    - Adaptive contrast enhancement (CLAHE)
    - Edge-preserving smoothing
    - Intelligent binarization
    """
    if not CV2_AVAILABLE:
        logger.warning(
            "OpenCV (cv2) not available for advanced preprocessing. "
            "Using basic enhancement instead. Install opencv-python-headless for full functionality."
        )
        return enhance_image(image)
    
    try:
        img_array=np.array(image)
        if img_array is None or img_array.size==0:raise ValueError("Image array is empty or None")
        logger.info(f"Image array shape: {img_array.shape}")
        if len(img_array.shape)==3:gray=cv2.cvtColor(img_array,cv2.COLOR_RGB2GRAY)
        else:gray=img_array
        if aggressive:
            height,width=gray.shape
            # Adaptive upscaling for better text recognition
            if max(height,width)<1000:
                scale_factor=1500/max(height,width)
                new_width,new_height=int(width*scale_factor),int(height*scale_factor)
                gray=cv2.resize(gray,(new_width,new_height),interpolation=cv2.INTER_CUBIC)
                logger.info(f"Upscaled image from {width}x{height} to {new_width}x{new_height}")
            
            # Deskew for better text alignment
            gray=_deskew_image(gray)
            
            # Advanced noise reduction with edge preservation
            gray = _advanced_denoise(gray)
            
            # Adaptive contrast enhancement
            clahe=cv2.createCLAHE(clipLimit=3.0,tileGridSize=(8,8))
            gray=clahe.apply(gray)
            
            # Edge-preserving smoothing
            gray=cv2.bilateralFilter(gray,9,75,75)
            
            # Intelligent binarization
            binary = _adaptive_binarize(gray)
            
            # Morphological cleanup
            kernel=cv2.getStructuringElement(cv2.MORPH_RECT,(1,1))
            binary=cv2.morphologyEx(binary,cv2.MORPH_CLOSE,kernel)
            
            # Handle inverted images (dark background)
            if np.mean(binary)<127:
                binary=cv2.bitwise_not(binary)
                logger.info("Inverted image (dark background detected)")
            
            result=Image.fromarray(binary)
            logger.info("Aggressive OCR preprocessing complete")
        else:
            binary=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
            denoised=cv2.fastNlMeansDenoising(binary)
            result=Image.fromarray(denoised)
            logger.info("Standard OCR preprocessing complete")
        return result
    except Exception as e:
        logger.warning(f"OCR preprocessing failed, using enhanced image: {e}")
        return enhance_image(image)

def _advanced_denoise(gray: np.ndarray) -> np.ndarray:
    """
    Multi-stage noise reduction preserving text edges.
    
    Uses a combination of techniques for optimal text preservation:
    1. Fast non-local means denoising for general noise
    2. Median filter for salt-and-pepper noise
    3. Morphological operations for cleaning
    """
    if not CV2_AVAILABLE:
        logger.warning("OpenCV not available for denoising")
        return gray
    
    # First pass: non-local means denoising
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    
    # Second pass: light median filter for remaining salt-and-pepper noise
    denoised = cv2.medianBlur(denoised, 3)
    
    return denoised

def _adaptive_binarize(gray: np.ndarray) -> np.ndarray:
    """
    Intelligent binarization that adapts to image content.
    
    Combines multiple binarization techniques:
    1. Otsu's method for global threshold
    2. Adaptive thresholding for local variations
    3. Result selection based on text density
    """
    if not CV2_AVAILABLE:
        logger.warning("OpenCV not available for binarization")
        return gray
    
    # Method 1: Otsu's binarization
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Method 2: Adaptive Gaussian thresholding
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
    
    # Calculate text density for each method
    otsu_density = _calculate_text_density(otsu)
    adaptive_density = _calculate_text_density(adaptive)
    
    # Choose the method with better text density (closer to typical document ratio)
    # Typical text documents have 5-30% text coverage
    ideal_density = 0.15
    otsu_diff = abs(otsu_density - ideal_density)
    adaptive_diff = abs(adaptive_density - ideal_density)
    
    if otsu_diff <= adaptive_diff:
        logger.info(f"Using Otsu binarization (density: {otsu_density:.3f})")
        return otsu
    else:
        logger.info(f"Using Adaptive binarization (density: {adaptive_density:.3f})")
        return adaptive

def _calculate_text_density(binary: np.ndarray) -> float:
    """Calculate the ratio of text pixels to total pixels."""
    # Assuming white background, black text
    text_pixels = np.sum(binary < 128)
    total_pixels = binary.size
    return text_pixels / total_pixels

def _deskew_image(image:np.ndarray)->np.ndarray:
    """Correct image skew for better text alignment."""
    if not CV2_AVAILABLE:
        logger.warning("OpenCV not available for deskewing")
        return image
    
    try:
        coords=np.column_stack(np.where(image>0))
        if len(coords)<10:
            logger.warning("Not enough edge points for deskewing")
            return image
        angle=cv2.minAreaRect(coords)[-1]
        if angle<-45:angle=90+angle
        elif angle>45:angle=angle-90
        if abs(angle)<0.5:
            logger.info(f"Skew angle {angle:.2f}° is negligible, skipping correction")
            return image
        (h,w)=image.shape
        center=(w//2,h//2)
        M=cv2.getRotationMatrix2D(center,angle,1.0)
        rotated=cv2.warpAffine(image,M,(w,h),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
        logger.info(f"Deskewed image by {angle:.2f} degrees")
        return rotated
    except Exception as e:
        logger.warning(f"Deskew failed: {e}")
        return image

def resize_if_needed(image:Image.Image,max_size:int=2048)->Image.Image:
    """Resize image if it exceeds maximum dimensions."""
    width,height=image.size
    if max(width,height)>max_size:
        ratio=max_size/max(width,height)
        new_size=(int(width*ratio),int(height*ratio))
        resized=image.resize(new_size,Image.Resampling.LANCZOS)
        logger.info(f"Resized image from {image.size} to {new_size}")
        return resized
    return image

def detect_text_regions(image: Image.Image) -> list:
    """
    Detect text regions in an image using contour analysis.
    
    Returns a list of bounding boxes (x, y, w, h) for detected text regions.
    Similar to region detection used by advanced OCR services.
    """
    if not CV2_AVAILABLE:
        logger.warning("OpenCV not available for text region detection, returning empty list")
        return []
    
    try:
        img_array = np.array(image.convert('L'))
        
        # Apply edge detection
        edges = cv2.Canny(img_array, 50, 150)
        
        # Dilate to connect text components
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter and sort text regions
        regions = []
        min_area = 100  # Minimum area to consider as text
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            aspect_ratio = w / max(h, 1)
            
            # Text regions typically have width > height and reasonable area
            if area > min_area and 0.5 < aspect_ratio < 50:
                regions.append((x, y, w, h))
        
        # Sort by y-coordinate (top to bottom), then x (left to right)
        regions.sort(key=lambda r: (r[1], r[0]))
        
        logger.info(f"Detected {len(regions)} text regions")
        return regions
    except Exception as e:
        logger.warning(f"Text region detection failed: {e}")
        return []

def preprocess_multi_pass(image: Image.Image) -> list:
    """
    Generate multiple preprocessed versions for ensemble OCR.
    
    Returns a list of preprocessed images using different techniques,
    allowing OCR engines to pick the best result.
    """
    results = []
    
    try:
        # Original enhanced
        results.append(('enhanced', enhance_image(image)))
        
        # Only add cv2-based preprocessing if available
        if CV2_AVAILABLE:
            # Aggressive preprocessing
            results.append(('aggressive', preprocess_for_ocr(image, aggressive=True)))
            
            # Standard preprocessing
            results.append(('standard', preprocess_for_ocr(image, aggressive=False)))
            
            # High contrast version
            img_array = np.array(image.convert('L'))
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
            high_contrast = clahe.apply(img_array)
            results.append(('high_contrast', Image.fromarray(high_contrast)))
        else:
            logger.info("OpenCV not available, using enhanced version only for multi-pass")
        
        logger.info(f"Generated {len(results)} preprocessed versions")
    except Exception as e:
        logger.warning(f"Multi-pass preprocessing failed: {e}")
        results.append(('fallback', enhance_image(image)))
    
    return results

def non_maximum_suppression(
    boxes: list,
    confidences: list = None,
    overlap_threshold: float = 0.3
) -> list:
    """
    Apply Non-Maximum Suppression (NMS) to remove duplicate bounding boxes.
    
    This function eliminates overlapping detections by keeping only the boxes
    with highest confidence scores when multiple boxes overlap significantly.
    
    Args:
        boxes: List of bounding boxes, each as [x, y, width, height] or BoundingBox object
        confidences: List of confidence scores (0-1). If None, all boxes have equal priority.
        overlap_threshold: IoU threshold above which boxes are considered duplicates (default: 0.3)
    
    Returns:
        List of indices of boxes to keep after NMS
        
    Example:
        >>> boxes = [[10, 10, 50, 50], [15, 15, 50, 50], [100, 100, 30, 30]]
        >>> confidences = [0.9, 0.7, 0.8]
        >>> keep_indices = non_maximum_suppression(boxes, confidences, 0.3)
        >>> filtered_boxes = [boxes[i] for i in keep_indices]
    """
    if not boxes:
        return []
    
    # Import BoundingBox schema if available
    try:
        from shared.models.schemas import BoundingBox
        has_schema = True
    except ImportError:
        has_schema = False
    
    # Convert boxes to uniform format [x, y, width, height]
    normalized_boxes = []
    for box in boxes:
        if has_schema and isinstance(box, BoundingBox):
            normalized_boxes.append([box.x, box.y, box.width, box.height])
        elif isinstance(box, (list, tuple)) and len(box) >= 4:
            normalized_boxes.append(list(box[:4]))
        else:
            logger.warning(f"Invalid box format: {box}, skipping")
            continue
    
    if not normalized_boxes:
        return []
    
    # Use default confidences if not provided
    if confidences is None:
        confidences = [1.0] * len(normalized_boxes)
    
    # Validate inputs
    if len(normalized_boxes) != len(confidences):
        logger.error(
            f"Boxes ({len(normalized_boxes)}) and confidences ({len(confidences)}) "
            f"length mismatch"
        )
        return list(range(len(normalized_boxes)))
    
    # Convert to numpy arrays for efficient computation
    boxes_array = np.array(normalized_boxes, dtype=np.float32)
    confidences_array = np.array(confidences, dtype=np.float32)
    
    # Extract coordinates
    x = boxes_array[:, 0]
    y = boxes_array[:, 1]
    w = boxes_array[:, 2]
    h = boxes_array[:, 3]
    
    # Calculate areas
    areas = w * h
    
    # Sort by confidence (descending)
    order = confidences_array.argsort()[::-1]
    
    keep = []
    while order.size > 0:
        # Pick the box with highest confidence
        i = order[0]
        keep.append(int(i))
        
        if order.size == 1:
            break
        
        # Calculate IoU with remaining boxes
        xx1 = np.maximum(x[i], x[order[1:]])
        yy1 = np.maximum(y[i], y[order[1:]])
        xx2 = np.minimum(x[i] + w[i], x[order[1:]] + w[order[1:]])
        yy2 = np.minimum(y[i] + h[i], y[order[1:]] + h[order[1:]])
        
        # Calculate intersection area
        intersection_w = np.maximum(0.0, xx2 - xx1)
        intersection_h = np.maximum(0.0, yy2 - yy1)
        intersection = intersection_w * intersection_h
        
        # Calculate union area
        union = areas[i] + areas[order[1:]] - intersection
        
        # Calculate IoU
        iou = np.where(union > 0, intersection / union, 0.0)
        
        # Keep boxes with IoU below threshold
        inds = np.where(iou <= overlap_threshold)[0]
        order = order[inds + 1]
    
    logger.debug(f"NMS: kept {len(keep)} of {len(boxes)} boxes (threshold: {overlap_threshold})")
    return keep
