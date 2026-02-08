"""
Advanced Image Preprocessing Module for Receipt Extraction

This module implements comprehensive image preprocessing capabilities including:
- Deskewing and rotation correction
- Image enhancement (contrast, brightness, sharpness)
- Column detection and splitting
- Manual region extraction
- Text detection mode processing
- Adaptive preprocessing based on image quality

All preprocessing functions are designed to be applied based on user-selected
detection settings from the frontend.
"""

import os
import sys
import logging
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Union
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw
from dataclasses import dataclass
from enum import Enum

# Import cv2 lazily
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

# Import scipy for advanced operations
try:
    import scipy.ndimage
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    scipy = None

logger = logging.getLogger(__name__)


class DetectionMode(Enum):
    """Detection modes for text extraction."""
    AUTO = "auto"
    MANUAL = "manual"
    LINE = "line"
    COLUMN = "column"


@dataclass
class PreprocessingSettings:
    """Settings for image preprocessing."""
    detection_mode: str = "auto"
    enable_deskew: bool = True
    enable_enhancement: bool = True
    column_mode: bool = False
    manual_regions: Optional[List[Dict[str, int]]] = None
    min_confidence: float = 0.5
    
    # Enhancement parameters
    contrast_factor: float = 1.5
    brightness_factor: float = 1.1
    sharpness_factor: float = 1.3
    
    # Deskew parameters
    max_angle: float = 45.0
    angle_step: float = 0.5
    
    # Column detection parameters
    min_column_width: int = 100
    column_spacing: int = 20
    
    @classmethod
    def from_dict(cls, settings: Dict[str, Any]) -> 'PreprocessingSettings':
        """Create PreprocessingSettings from dictionary."""
        return cls(
            detection_mode=settings.get('detection_mode', 'auto'),
            enable_deskew=settings.get('enable_deskew', True),
            enable_enhancement=settings.get('enable_enhancement', True),
            column_mode=settings.get('column_mode', False),
            manual_regions=settings.get('manual_regions', None)
        )


@dataclass
class PreprocessingResult:
    """Result of image preprocessing."""
    image: Image.Image
    original_image: Image.Image
    applied_operations: List[str]
    detected_angle: Optional[float] = None
    detected_columns: Optional[List[Dict[str, int]]] = None
    manual_regions: Optional[List[Dict[str, int]]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ImageDeskewer:
    """Handles image deskewing and rotation correction."""
    
    @staticmethod
    def detect_skew_angle(image: Image.Image, max_angle: float = 45.0) -> float:
        """
        Detect skew angle of image using edge detection.
        
        Args:
            image: PIL Image to analyze
            max_angle: Maximum angle to check (degrees)
            
        Returns:
            Detected skew angle in degrees
        """
        if not CV2_AVAILABLE:
            logger.warning("OpenCV not available, skipping skew detection")
            return 0.0
        
        try:
            # Convert to grayscale numpy array
            if image.mode != 'L':
                gray = image.convert('L')
            else:
                gray = image
            
            img_array = np.array(gray)
            
            # Apply edge detection
            edges = cv2.Canny(img_array, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
            
            if lines is None or len(lines) == 0:
                logger.debug("No lines detected for skew angle calculation")
                return 0.0
            
            # Calculate angles of detected lines
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = np.degrees(theta) - 90
                
                # Filter angles within reasonable range
                if -max_angle <= angle <= max_angle:
                    angles.append(angle)
            
            if not angles:
                return 0.0
            
            # Use median angle to reduce outlier effect
            detected_angle = float(np.median(angles))
            
            logger.info(f"Detected skew angle: {detected_angle:.2f} degrees")
            return detected_angle
            
        except Exception as e:
            logger.error(f"Error detecting skew angle: {e}")
            return 0.0
    
    @staticmethod
    def deskew_image(image: Image.Image, angle: Optional[float] = None, 
                     max_angle: float = 45.0) -> Tuple[Image.Image, float]:
        """
        Deskew image by rotating to correct skew.
        
        Args:
            image: PIL Image to deskew
            angle: Specific angle to rotate (if None, auto-detect)
            max_angle: Maximum angle for auto-detection
            
        Returns:
            Tuple of (deskewed_image, angle_used)
        """
        try:
            # Detect angle if not provided
            if angle is None:
                angle = ImageDeskewer.detect_skew_angle(image, max_angle)
            
            # Skip if angle is too small
            if abs(angle) < 0.5:
                logger.debug("Skew angle too small, skipping correction")
                return image, 0.0
            
            # Rotate image
            deskewed = image.rotate(-angle, expand=True, fillcolor='white')
            logger.info(f"Deskewed image by {angle:.2f} degrees")
            
            return deskewed, angle
            
        except Exception as e:
            logger.error(f"Error deskewing image: {e}")
            return image, 0.0


class ImageEnhancer:
    """Handles image enhancement operations."""
    
    @staticmethod
    def enhance_contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
        """Enhance image contrast."""
        try:
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(factor)
            logger.debug(f"Enhanced contrast by factor {factor}")
            return enhanced
        except Exception as e:
            logger.error(f"Error enhancing contrast: {e}")
            return image
    
    @staticmethod
    def enhance_brightness(image: Image.Image, factor: float = 1.1) -> Image.Image:
        """Enhance image brightness."""
        try:
            enhancer = ImageEnhance.Brightness(image)
            enhanced = enhancer.enhance(factor)
            logger.debug(f"Enhanced brightness by factor {factor}")
            return enhanced
        except Exception as e:
            logger.error(f"Error enhancing brightness: {e}")
            return image
    
    @staticmethod
    def enhance_sharpness(image: Image.Image, factor: float = 1.3) -> Image.Image:
        """Enhance image sharpness."""
        try:
            enhancer = ImageEnhance.Sharpness(image)
            enhanced = enhancer.enhance(factor)
            logger.debug(f"Enhanced sharpness by factor {factor}")
            return enhanced
        except Exception as e:
            logger.error(f"Error enhancing sharpness: {e}")
            return image
    
    @staticmethod
    def denoise(image: Image.Image) -> Image.Image:
        """Apply denoising filter."""
        try:
            if CV2_AVAILABLE:
                # Convert to numpy array
                img_array = np.array(image)
                
                # Apply fastNlMeans denoising
                if len(img_array.shape) == 3:
                    denoised = cv2.fastNlMeansDenoisingColored(img_array, None, 10, 10, 7, 21)
                else:
                    denoised = cv2.fastNlMeansDenoising(img_array, None, 10, 7, 21)
                
                # Convert back to PIL Image
                result = Image.fromarray(denoised)
                logger.debug("Applied denoising filter")
                return result
            else:
                # Fallback to PIL filter
                result = image.filter(ImageFilter.MedianFilter(size=3))
                logger.debug("Applied median filter (OpenCV not available)")
                return result
        except Exception as e:
            logger.error(f"Error denoising image: {e}")
            return image
    
    @staticmethod
    def auto_enhance(image: Image.Image, settings: PreprocessingSettings) -> Image.Image:
        """Apply full enhancement pipeline."""
        try:
            enhanced = image
            
            # Apply contrast enhancement
            enhanced = ImageEnhancer.enhance_contrast(enhanced, settings.contrast_factor)
            
            # Apply brightness enhancement
            enhanced = ImageEnhancer.enhance_brightness(enhanced, settings.brightness_factor)
            
            # Apply sharpness enhancement
            enhanced = ImageEnhancer.enhance_sharpness(enhanced, settings.sharpness_factor)
            
            # Apply denoising
            enhanced = ImageEnhancer.denoise(enhanced)
            
            logger.info("Applied full enhancement pipeline")
            return enhanced
            
        except Exception as e:
            logger.error(f"Error in auto enhance: {e}")
            return image


class ColumnDetector:
    """Handles column detection and splitting."""
    
    @staticmethod
    def detect_columns(image: Image.Image, min_width: int = 100, 
                      spacing: int = 20) -> List[Dict[str, int]]:
        """
        Detect columns in image using vertical projection.
        
        Args:
            image: PIL Image to analyze
            min_width: Minimum column width in pixels
            spacing: Minimum spacing between columns
            
        Returns:
            List of column bounding boxes [{'x': x, 'y': y, 'width': w, 'height': h}, ...]
        """
        if not CV2_AVAILABLE:
            logger.warning("OpenCV not available, cannot detect columns")
            return []
        
        try:
            # Convert to grayscale
            if image.mode != 'L':
                gray = image.convert('L')
            else:
                gray = image
            
            img_array = np.array(gray)
            
            # Binarize image
            _, binary = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Calculate vertical projection
            vertical_projection = np.sum(binary, axis=0)
            
            # Find column boundaries
            in_column = False
            column_start = 0
            columns = []
            
            for i, value in enumerate(vertical_projection):
                if value > 0 and not in_column:
                    column_start = i
                    in_column = True
                elif value == 0 and in_column:
                    column_width = i - column_start
                    if column_width >= min_width:
                        columns.append({
                            'x': column_start,
                            'y': 0,
                            'width': column_width,
                            'height': image.height
                        })
                    in_column = False
            
            # Handle case where column extends to end
            if in_column:
                column_width = len(vertical_projection) - column_start
                if column_width >= min_width:
                    columns.append({
                        'x': column_start,
                        'y': 0,
                        'width': column_width,
                        'height': image.height
                    })
            
            # Merge columns that are too close
            merged_columns = []
            for col in columns:
                if not merged_columns:
                    merged_columns.append(col)
                else:
                    last_col = merged_columns[-1]
                    gap = col['x'] - (last_col['x'] + last_col['width'])
                    
                    if gap < spacing:
                        # Merge columns
                        last_col['width'] = col['x'] + col['width'] - last_col['x']
                    else:
                        merged_columns.append(col)
            
            logger.info(f"Detected {len(merged_columns)} columns")
            return merged_columns
            
        except Exception as e:
            logger.error(f"Error detecting columns: {e}")
            return []
    
    @staticmethod
    def split_columns(image: Image.Image, columns: List[Dict[str, int]]) -> List[Image.Image]:
        """Split image into separate column images."""
        try:
            column_images = []
            for col in columns:
                # Extract column region
                column_img = image.crop((
                    col['x'],
                    col['y'],
                    col['x'] + col['width'],
                    col['y'] + col['height']
                ))
                column_images.append(column_img)
            
            logger.info(f"Split image into {len(column_images)} columns")
            return column_images
            
        except Exception as e:
            logger.error(f"Error splitting columns: {e}")
            return [image]


class RegionExtractor:
    """Handles manual region extraction."""
    
    @staticmethod
    def extract_regions(image: Image.Image, regions: List[Dict[str, int]]) -> List[Image.Image]:
        """
        Extract manual regions from image.
        
        Args:
            image: PIL Image
            regions: List of region dictionaries with x, y, width, height
            
        Returns:
            List of cropped images for each region
        """
        try:
            region_images = []
            for region in regions:
                # Extract region
                region_img = image.crop((
                    region['x'],
                    region['y'],
                    region['x'] + region['width'],
                    region['y'] + region['height']
                ))
                region_images.append(region_img)
            
            logger.info(f"Extracted {len(region_images)} manual regions")
            return region_images
            
        except Exception as e:
            logger.error(f"Error extracting regions: {e}")
            return [image]


class ImagePreprocessor:
    """Main preprocessing pipeline coordinator."""
    
    @staticmethod
    def preprocess(image: Union[Image.Image, str], 
                   settings: PreprocessingSettings) -> PreprocessingResult:
        """
        Apply complete preprocessing pipeline based on settings.
        
        Args:
            image: PIL Image or path to image file
            settings: PreprocessingSettings object
            
        Returns:
            PreprocessingResult with processed image and metadata
        """
        try:
            # Load image if path provided
            if isinstance(image, str):
                original_image = Image.open(image)
            else:
                original_image = image
            
            # Work on a copy
            processed = original_image.copy()
            applied_operations = []
            metadata = {
                'original_size': original_image.size,
                'detection_mode': settings.detection_mode
            }
            
            detected_angle = None
            detected_columns = None
            manual_regions_list = None
            
            # Step 1: Deskew if enabled
            if settings.enable_deskew:
                processed, detected_angle = ImageDeskewer.deskew_image(
                    processed, max_angle=settings.max_angle
                )
                if detected_angle and abs(detected_angle) > 0.5:
                    applied_operations.append(f"deskew_{detected_angle:.2f}deg")
                    metadata['skew_angle'] = detected_angle
            
            # Step 2: Enhance if enabled
            if settings.enable_enhancement:
                processed = ImageEnhancer.auto_enhance(processed, settings)
                applied_operations.append("enhancement")
            
            # Step 3: Column detection if enabled
            if settings.column_mode:
                detected_columns = ColumnDetector.detect_columns(
                    processed,
                    min_width=settings.min_column_width,
                    spacing=settings.column_spacing
                )
                if detected_columns:
                    applied_operations.append(f"column_detection_{len(detected_columns)}")
                    metadata['num_columns'] = len(detected_columns)
            
            # Step 4: Manual regions if provided
            if settings.manual_regions:
                manual_regions_list = settings.manual_regions
                applied_operations.append(f"manual_regions_{len(manual_regions_list)}")
                metadata['num_manual_regions'] = len(manual_regions_list)
            
            # Create result
            result = PreprocessingResult(
                image=processed,
                original_image=original_image,
                applied_operations=applied_operations,
                detected_angle=detected_angle,
                detected_columns=detected_columns,
                manual_regions=manual_regions_list,
                metadata=metadata
            )
            
            logger.info(f"Preprocessing complete. Applied: {', '.join(applied_operations)}")
            return result
            
        except Exception as e:
            logger.error(f"Error in preprocessing pipeline: {e}", exc_info=True)
            # Return original image on error
            return PreprocessingResult(
                image=original_image if isinstance(original_image, Image.Image) else Image.open(image),
                original_image=original_image if isinstance(original_image, Image.Image) else Image.open(image),
                applied_operations=["error"],
                metadata={'error': str(e)}
            )


def preprocess_for_extraction(image_path: str, settings: Dict[str, Any]) -> PreprocessingResult:
    """
    Convenience function for preprocessing with dictionary settings.
    
    Args:
        image_path: Path to image file
        settings: Dictionary of preprocessing settings
        
    Returns:
        PreprocessingResult
    """
    preprocessing_settings = PreprocessingSettings.from_dict(settings)
    return ImagePreprocessor.preprocess(image_path, preprocessing_settings)


def preprocess_image_with_settings(image: Image.Image, 
                                   detection_mode: str = "auto",
                                   enable_deskew: bool = True,
                                   enable_enhancement: bool = True,
                                   column_mode: bool = False,
                                   manual_regions: Optional[List[Dict]] = None) -> PreprocessingResult:
    """
    Convenience function for preprocessing with individual parameters.
    
    Args:
        image: PIL Image to preprocess
        detection_mode: Detection mode to use
        enable_deskew: Enable deskewing
        enable_enhancement: Enable enhancement
        column_mode: Enable column detection
        manual_regions: Manual region list
        
    Returns:
        PreprocessingResult
    """
    settings = PreprocessingSettings(
        detection_mode=detection_mode,
        enable_deskew=enable_deskew,
        enable_enhancement=enable_enhancement,
        column_mode=column_mode,
        manual_regions=manual_regions
    )
    return ImagePreprocessor.preprocess(image, settings)
