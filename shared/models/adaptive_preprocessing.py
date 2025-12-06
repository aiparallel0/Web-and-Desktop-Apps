"""
=============================================================================
ADAPTIVE PREPROCESSING PIPELINE - Intelligent Image Processing
=============================================================================

Implements the adaptive preprocessing pipeline from the enhancement plan:
- Comprehensive image quality assessment (blur, noise, contrast, resolution)
- Automatic strategy selection based on quality metrics
- Multi-strategy ensemble with voting mechanism
- Receipt-specific binarization techniques

Features:
- Quality score (0-100) with component breakdown
- Automatic preprocessing strategy selection
- Multiple binarization methods (Sauvola, Niblack, Wolf-Jolion)
- Shadow removal and perspective correction

Usage:
    from adaptive_preprocessing import AdaptivePreprocessor, assess_quality
    
    preprocessor = AdaptivePreprocessor()
    processed_images = preprocessor.process(image)
    best_image = preprocessor.select_best(processed_images, ocr_results)

=============================================================================
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)

# Try to import OpenCV
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available. Install with: pip install opencv-python")


class PreprocessingStrategy(str, Enum):
    """Available preprocessing strategies."""
    STANDARD = "standard"
    DEBLUR = "deblur"
    DENOISE = "denoise"
    ENHANCE_CONTRAST = "enhance_contrast"
    DESKEW = "deskew"
    BINARIZE_SAUVOLA = "binarize_sauvola"
    BINARIZE_ADAPTIVE = "binarize_adaptive"
    SHADOW_REMOVAL = "shadow_removal"
    PERSPECTIVE_CORRECT = "perspective_correct"


@dataclass
class QualityMetrics:
    """
    Comprehensive image quality metrics.
    
    Attributes:
        blur_score: Laplacian variance (higher = sharper)
        noise_level: Local standard deviation estimate
        contrast: Histogram-based contrast measurement
        brightness: Mean pixel intensity
        resolution_score: Based on image dimensions
        skew_angle: Detected text skew angle
        overall_score: Weighted combination (0-100)
    """
    blur_score: float = 0.0
    noise_level: float = 0.0
    contrast: float = 0.0
    brightness: float = 0.0
    resolution_score: float = 0.0
    skew_angle: float = 0.0
    text_density: float = 0.0
    lighting_uniformity: float = 0.0
    overall_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'blur_score': round(self.blur_score, 2),
            'noise_level': round(self.noise_level, 2),
            'contrast': round(self.contrast, 2),
            'brightness': round(self.brightness, 2),
            'resolution_score': round(self.resolution_score, 2),
            'skew_angle': round(self.skew_angle, 2),
            'text_density': round(self.text_density, 3),
            'lighting_uniformity': round(self.lighting_uniformity, 2),
            'overall_score': round(self.overall_score, 1),
            'quality_level': self.get_quality_level()
        }
    
    def get_quality_level(self) -> str:
        """Get human-readable quality level."""
        if self.overall_score >= 80:
            return "excellent"
        elif self.overall_score >= 60:
            return "good"
        elif self.overall_score >= 40:
            return "fair"
        else:
            return "poor"


def assess_image_quality(image: Image.Image) -> QualityMetrics:
    """
    Perform comprehensive image quality assessment.
    
    Analyzes multiple quality factors:
    - Blur detection using Laplacian variance
    - Noise estimation using local statistics
    - Contrast measurement using histogram analysis
    - Resolution adequacy check
    - Skew angle detection
    - Lighting uniformity assessment
    
    Args:
        image: PIL Image to assess
        
    Returns:
        QualityMetrics with detailed measurements
    """
    if not CV2_AVAILABLE:
        logger.warning("OpenCV not available for quality assessment")
        return QualityMetrics(overall_score=50)
    
    # Convert to grayscale numpy array
    gray = np.array(image.convert('L'))
    height, width = gray.shape
    
    metrics = QualityMetrics()
    
    # 1. Blur Detection (Laplacian variance)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    metrics.blur_score = float(laplacian.var())
    
    # 2. Noise Level Estimation
    # Use median absolute deviation of Laplacian
    median_lap = np.median(np.abs(laplacian - np.median(laplacian)))
    metrics.noise_level = float(median_lap)
    
    # 3. Contrast Measurement
    metrics.contrast = float(np.std(gray))
    
    # 4. Brightness
    metrics.brightness = float(np.mean(gray))
    
    # 5. Resolution Score
    # Higher resolution is better, but normalize to 0-100
    min_dim = min(width, height)
    if min_dim >= 2000:
        metrics.resolution_score = 100
    elif min_dim >= 1000:
        metrics.resolution_score = 80
    elif min_dim >= 500:
        metrics.resolution_score = 60
    else:
        metrics.resolution_score = max(20, min_dim / 25)
    
    # 6. Skew Angle Detection
    try:
        coords = np.column_stack(np.where(gray > 0))
        if len(coords) >= 10:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = 90 + angle
            elif angle > 45:
                angle = angle - 90
            metrics.skew_angle = float(angle)
    except Exception:
        metrics.skew_angle = 0.0
    
    # 7. Text Density Estimation
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text_pixels = np.sum(binary < 128)
    metrics.text_density = float(text_pixels / gray.size)
    
    # 8. Lighting Uniformity (using local means)
    try:
        # Divide image into regions and check variance of means
        block_size = max(50, min(width, height) // 8)
        local_means = []
        for y in range(0, height - block_size, block_size):
            for x in range(0, width - block_size, block_size):
                block = gray[y:y+block_size, x:x+block_size]
                local_means.append(np.mean(block))
        if local_means:
            uniformity = 1 - (np.std(local_means) / max(np.mean(local_means), 1))
            metrics.lighting_uniformity = max(0, min(1, uniformity)) * 100
    except Exception:
        metrics.lighting_uniformity = 50
    
    # Calculate overall score (weighted combination)
    # Weights based on importance for OCR
    weights = {
        'blur': 0.25,      # Sharpness is critical
        'contrast': 0.20,   # Good contrast helps text detection
        'noise': 0.15,      # Noise affects recognition
        'resolution': 0.15, # Higher resolution is better
        'lighting': 0.10,   # Uniform lighting helps
        'skew': 0.10,       # Skew affects reading order
        'density': 0.05     # Text density indicates document type
    }
    
    # Normalize and score each component
    blur_norm = min(100, metrics.blur_score / 10)  # Higher is better
    contrast_norm = min(100, metrics.contrast / 0.8)  # ~80 std is good
    noise_norm = max(0, 100 - metrics.noise_level * 5)  # Lower is better
    skew_norm = max(0, 100 - abs(metrics.skew_angle) * 5)  # Near 0 is best
    density_norm = 100 if 0.05 < metrics.text_density < 0.30 else 50  # Typical document range
    
    metrics.overall_score = (
        weights['blur'] * blur_norm +
        weights['contrast'] * contrast_norm +
        weights['noise'] * noise_norm +
        weights['resolution'] * metrics.resolution_score +
        weights['lighting'] * metrics.lighting_uniformity +
        weights['skew'] * skew_norm +
        weights['density'] * density_norm
    )
    
    logger.info(f"Image quality assessment: score={metrics.overall_score:.1f}, "
                f"blur={metrics.blur_score:.1f}, contrast={metrics.contrast:.1f}")
    
    return metrics


class AdaptivePreprocessor:
    """
    Adaptive preprocessing pipeline that selects strategies based on image quality.
    
    Automatically analyzes input images and applies the most appropriate
    preprocessing techniques for optimal OCR performance.
    """
    
    def __init__(self):
        """Initialize the adaptive preprocessor."""
        self.quality_metrics = None
    
    def select_strategy(
        self,
        image: Image.Image,
        quality_metrics: QualityMetrics = None
    ) -> List[PreprocessingStrategy]:
        """
        Select preprocessing strategies based on image quality assessment.
        
        Args:
            image: Input image
            quality_metrics: Pre-computed quality metrics (optional)
            
        Returns:
            List of recommended preprocessing strategies
        """
        if quality_metrics is None:
            quality_metrics = assess_image_quality(image)
        
        self.quality_metrics = quality_metrics
        strategies = []
        
        # Determine strategies based on quality issues
        
        # Blur handling
        if quality_metrics.blur_score < 100:
            strategies.append(PreprocessingStrategy.DEBLUR)
            logger.info(f"Blur detected (score: {quality_metrics.blur_score:.1f}), adding deblur")
        
        # Noise handling
        if quality_metrics.noise_level > 15:
            strategies.append(PreprocessingStrategy.DENOISE)
            logger.info(f"High noise detected (level: {quality_metrics.noise_level:.1f}), adding denoise")
        
        # Contrast handling
        if quality_metrics.contrast < 40:
            strategies.append(PreprocessingStrategy.ENHANCE_CONTRAST)
            logger.info(f"Low contrast detected ({quality_metrics.contrast:.1f}), adding contrast enhancement")
        
        # Skew handling
        if abs(quality_metrics.skew_angle) > 2.0:
            strategies.append(PreprocessingStrategy.DESKEW)
            logger.info(f"Skew detected ({quality_metrics.skew_angle:.1f}°), adding deskew")
        
        # Lighting uniformity
        if quality_metrics.lighting_uniformity < 60:
            strategies.append(PreprocessingStrategy.SHADOW_REMOVAL)
            logger.info(f"Uneven lighting detected, adding shadow removal")
        
        # Always add appropriate binarization
        if quality_metrics.lighting_uniformity < 70:
            strategies.append(PreprocessingStrategy.BINARIZE_SAUVOLA)
        else:
            strategies.append(PreprocessingStrategy.BINARIZE_ADAPTIVE)
        
        # If good quality, just use standard
        if not strategies:
            strategies.append(PreprocessingStrategy.STANDARD)
        
        return strategies
    
    def apply_strategy(
        self,
        image: Image.Image,
        strategy: PreprocessingStrategy
    ) -> Image.Image:
        """
        Apply a single preprocessing strategy.
        
        Args:
            image: Input image
            strategy: Strategy to apply
            
        Returns:
            Processed image
        """
        if not CV2_AVAILABLE:
            return image
        
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        result = gray
        
        if strategy == PreprocessingStrategy.DEBLUR:
            result = self._apply_deblur(gray)
        elif strategy == PreprocessingStrategy.DENOISE:
            result = self._apply_denoise(gray)
        elif strategy == PreprocessingStrategy.ENHANCE_CONTRAST:
            result = self._apply_contrast_enhancement(gray)
        elif strategy == PreprocessingStrategy.DESKEW:
            result = self._apply_deskew(gray)
        elif strategy == PreprocessingStrategy.BINARIZE_SAUVOLA:
            result = self._apply_sauvola_binarization(gray)
        elif strategy == PreprocessingStrategy.BINARIZE_ADAPTIVE:
            result = self._apply_adaptive_binarization(gray)
        elif strategy == PreprocessingStrategy.SHADOW_REMOVAL:
            result = self._apply_shadow_removal(gray)
        elif strategy == PreprocessingStrategy.STANDARD:
            result = self._apply_standard(gray)
        
        return Image.fromarray(result)
    
    def process(
        self,
        image: Image.Image,
        strategies: List[PreprocessingStrategy] = None
    ) -> List[Tuple[str, Image.Image]]:
        """
        Process image with multiple preprocessing strategies.
        
        Generates multiple preprocessed versions for ensemble OCR.
        
        Args:
            image: Input image
            strategies: Strategies to apply (auto-selected if None)
            
        Returns:
            List of (strategy_name, processed_image) tuples
        """
        if strategies is None:
            strategies = self.select_strategy(image)
        
        results = []
        
        # Always include the original (grayscale)
        gray = image.convert('L')
        results.append(('original', gray))
        
        # Apply each strategy
        for strategy in strategies:
            try:
                processed = self.apply_strategy(image, strategy)
                results.append((strategy.value, processed))
            except Exception as e:
                logger.warning(f"Strategy {strategy.value} failed: {e}")
        
        # Add combined preprocessing (all selected strategies in sequence)
        try:
            combined = image
            for strategy in strategies:
                combined = self.apply_strategy(combined, strategy)
            results.append(('combined', combined))
        except Exception as e:
            logger.warning(f"Combined preprocessing failed: {e}")
        
        logger.info(f"Generated {len(results)} preprocessed versions")
        return results
    
    def select_best(
        self,
        processed_images: List[Tuple[str, Image.Image]],
        ocr_results: List[Dict[str, Any]]
    ) -> Tuple[str, Image.Image, Dict[str, Any]]:
        """
        Select the best preprocessed image based on OCR results.
        
        Uses voting mechanism and confidence scores to select the optimal result.
        
        Args:
            processed_images: List of (name, image) tuples
            ocr_results: OCR results for each processed image
            
        Returns:
            Tuple of (name, image, ocr_result) for the best result
        """
        if len(processed_images) != len(ocr_results):
            raise ValueError("Mismatch between images and results count")
        
        best_idx = 0
        best_score = 0
        
        for i, (name, img) in enumerate(processed_images):
            result = ocr_results[i]
            score = self._score_ocr_result(result)
            
            if score > best_score:
                best_score = score
                best_idx = i
        
        name, img = processed_images[best_idx]
        return name, img, ocr_results[best_idx]
    
    # =========================================================================
    # PREPROCESSING IMPLEMENTATIONS
    # =========================================================================
    
    def _apply_standard(self, gray: np.ndarray) -> np.ndarray:
        """Standard preprocessing pipeline."""
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        # CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        return enhanced
    
    def _apply_deblur(self, gray: np.ndarray) -> np.ndarray:
        """Apply deblurring using unsharp masking."""
        # Gaussian blur and then subtract for sharpening
        blurred = cv2.GaussianBlur(gray, (0, 0), 3)
        sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
        return np.clip(sharpened, 0, 255).astype(np.uint8)
    
    def _apply_denoise(self, gray: np.ndarray) -> np.ndarray:
        """Multi-stage noise reduction."""
        # First pass: non-local means
        denoised = cv2.fastNlMeansDenoising(gray, h=12)
        # Second pass: light median filter
        denoised = cv2.medianBlur(denoised, 3)
        return denoised
    
    def _apply_contrast_enhancement(self, gray: np.ndarray) -> np.ndarray:
        """Adaptive contrast enhancement using CLAHE."""
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
        enhanced = clahe.apply(gray)
        return enhanced
    
    def _apply_deskew(self, gray: np.ndarray) -> np.ndarray:
        """Correct image skew."""
        try:
            coords = np.column_stack(np.where(gray > 0))
            if len(coords) < 10:
                return gray
            
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = 90 + angle
            elif angle > 45:
                angle = angle - 90
            
            if abs(angle) < 0.5:
                return gray
            
            h, w = gray.shape
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                gray, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            return rotated
        except Exception:
            return gray
    
    def _apply_sauvola_binarization(self, gray: np.ndarray) -> np.ndarray:
        """
        Sauvola adaptive thresholding.
        
        Better for receipts with uneven lighting than simple adaptive threshold.
        """
        window_size = 25
        k = 0.08  # Sauvola parameter
        
        # Calculate local mean and std
        mean = cv2.blur(gray.astype(np.float64), (window_size, window_size))
        mean_sq = cv2.blur(gray.astype(np.float64) ** 2, (window_size, window_size))
        std = np.sqrt(mean_sq - mean ** 2)
        
        # Sauvola threshold
        R = 128  # Dynamic range
        threshold = mean * (1 + k * (std / R - 1))
        
        binary = (gray > threshold).astype(np.uint8) * 255
        return binary
    
    def _apply_adaptive_binarization(self, gray: np.ndarray) -> np.ndarray:
        """Standard adaptive Gaussian thresholding."""
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        return binary
    
    def _apply_shadow_removal(self, gray: np.ndarray) -> np.ndarray:
        """Remove shadows using morphological operations."""
        # Create background model
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (51, 51))
        background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Divide to remove shadows
        normalized = cv2.divide(gray, background, scale=255)
        
        return normalized
    
    def _score_ocr_result(self, result: Dict[str, Any]) -> float:
        """Score an OCR result for quality."""
        score = 0.0
        
        if result.get('success'):
            score += 10
        
        if result.get('confidence'):
            score += result['confidence'] * 50
        
        data = result.get('data', {})
        
        if data.get('store_name'):
            score += 10
        if data.get('total'):
            score += 20
        if data.get('items'):
            score += len(data['items']) * 2
        if data.get('transaction_date'):
            score += 5
        
        return score


# =============================================================================
# MULTI-STRATEGY ENSEMBLE
# =============================================================================

class PreprocessingEnsemble:
    """
    Ensemble preprocessor that generates multiple versions and votes on best.
    
    Creates 3-5 preprocessed versions per image and combines OCR results
    using confidence-weighted voting.
    """
    
    def __init__(self, num_versions: int = 5):
        """
        Initialize ensemble preprocessor.
        
        Args:
            num_versions: Maximum number of preprocessed versions to generate
        """
        self.num_versions = num_versions
        self.preprocessor = AdaptivePreprocessor()
    
    def generate_versions(self, image: Image.Image) -> List[Tuple[str, Image.Image]]:
        """
        Generate multiple preprocessed versions of an image.
        
        Args:
            image: Input image
            
        Returns:
            List of (name, processed_image) tuples
        """
        quality = assess_image_quality(image)
        versions = []
        
        # 1. Original (grayscale)
        versions.append(('original', image.convert('L')))
        
        # 2. Quality-based adaptive
        strategies = self.preprocessor.select_strategy(image, quality)
        for strategy in strategies[:2]:  # Limit to avoid too many versions
            try:
                processed = self.preprocessor.apply_strategy(image, strategy)
                versions.append((strategy.value, processed))
            except Exception as e:
                logger.warning(f"Strategy {strategy.value} failed: {e}")
        
        # 3. Always include high contrast version
        try:
            high_contrast = self.preprocessor.apply_strategy(
                image, PreprocessingStrategy.ENHANCE_CONTRAST
            )
            versions.append(('high_contrast', high_contrast))
        except Exception:
            pass
        
        # 4. Include binarized version
        try:
            if quality.lighting_uniformity < 70:
                binarized = self.preprocessor.apply_strategy(
                    image, PreprocessingStrategy.BINARIZE_SAUVOLA
                )
            else:
                binarized = self.preprocessor.apply_strategy(
                    image, PreprocessingStrategy.BINARIZE_ADAPTIVE
                )
            versions.append(('binarized', binarized))
        except Exception:
            pass
        
        return versions[:self.num_versions]
    
    def weighted_voting(
        self,
        ocr_results: List[Dict[str, Any]],
        weights: List[float] = None
    ) -> Dict[str, Any]:
        """
        Combine OCR results using weighted voting.
        
        Args:
            ocr_results: List of OCR result dictionaries
            weights: Optional weights for each result (default: use confidence)
            
        Returns:
            Combined result
        """
        if not ocr_results:
            return {'success': False, 'error': 'No results to combine'}
        
        # Use confidence scores as weights if not provided
        if weights is None:
            weights = []
            for result in ocr_results:
                conf = result.get('confidence', 0.5)
                if isinstance(conf, (int, float)):
                    weights.append(conf)
                else:
                    weights.append(0.5)
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            weights = [1.0 / len(weights)] * len(weights)
        
        # Find best result by weighted score
        best_idx = 0
        best_score = 0
        
        for i, (result, weight) in enumerate(zip(ocr_results, weights)):
            if result.get('success'):
                score = weight * self._calculate_completeness(result)
                if score > best_score:
                    best_score = score
                    best_idx = i
        
        # Return best result with aggregated confidence
        result = ocr_results[best_idx].copy()
        
        # Average confidence across all results
        confidences = [r.get('confidence', 0) for r in ocr_results if r.get('success')]
        if confidences:
            result['ensemble_confidence'] = sum(confidences) / len(confidences)
        
        result['ensemble_versions'] = len(ocr_results)
        return result
    
    def _calculate_completeness(self, result: Dict[str, Any]) -> float:
        """Calculate result completeness score."""
        score = 0.0
        data = result.get('data', {})
        
        if data.get('store_name'):
            score += 0.2
        if data.get('total'):
            score += 0.3
        if data.get('items'):
            score += min(0.3, len(data['items']) * 0.05)
        if data.get('transaction_date'):
            score += 0.1
        if data.get('subtotal') and data.get('tax'):
            score += 0.1
        
        return score


# Global instances for convenience
adaptive_preprocessor = AdaptivePreprocessor()
preprocessing_ensemble = PreprocessingEnsemble()
