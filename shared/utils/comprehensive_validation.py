"""
Comprehensive Validation Module

Provides extensive validation for:
- Image quality assessment
- OCR result validation  
- Receipt data integrity checks
- Business rule validation
- Data consistency verification
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from PIL import Image
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils.data import ReceiptData, LineItem

logger = logging.getLogger(__name__)


class ImageQualityValidator:
    """Validates image quality for OCR processing."""
    
    @staticmethod
    def assess_quality(image_path: str) -> Dict[str, Any]:
        """
        Assess image quality for OCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with quality metrics and issues
        """
        issues = []
        metrics = {}
        
        try:
            image = Image.open(image_path)
            
            # Check dimensions
            width, height = image.size
            metrics['width'] = width
            metrics['height'] = height
            metrics['aspect_ratio'] = width / height if height > 0 else 0
            
            # Minimum resolution check
            if width < 300 or height < 300:
                issues.append(f"Low resolution: {width}x{height}. Minimum recommended: 300x300")
            
            # Maximum resolution check
            if width > 8000 or height > 8000:
                issues.append(f"Very high resolution: {width}x{height}. May be slow to process")
            
            # Aspect ratio check
            aspect_ratio = width / height if height > 0 else 0
            if aspect_ratio < 0.2 or aspect_ratio > 5:
                issues.append(f"Unusual aspect ratio: {aspect_ratio:.2f}")
            
            # Check color mode
            metrics['mode'] = image.mode
            if image.mode not in ['RGB', 'L', 'RGBA']:
                issues.append(f"Unusual color mode: {image.mode}")
            
            # Brightness check (if grayscale or RGB)
            if image.mode in ['L', 'RGB']:
                import numpy as np
                img_array = np.array(image.convert('L'))
                avg_brightness = np.mean(img_array)
                metrics['brightness'] = float(avg_brightness)
                
                if avg_brightness < 50:
                    issues.append(f"Image is very dark (brightness: {avg_brightness:.0f}/255)")
                elif avg_brightness > 200:
                    issues.append(f"Image is very bright (brightness: {avg_brightness:.0f}/255)")
            
            # Estimate sharpness/blur
            if image.mode in ['L', 'RGB']:
                try:
                    import numpy as np
                    from scipy import ndimage
                    
                    gray = np.array(image.convert('L'))
                    # Laplacian variance as blur metric
                    laplacian = ndimage.laplace(gray)
                    variance = float(np.var(laplacian))
                    metrics['sharpness'] = variance
                    
                    if variance < 100:
                        issues.append(f"Image may be blurry (sharpness: {variance:.0f})")
                except:
                    pass
            
            # Overall quality score
            quality_score = 100
            quality_score -= len(issues) * 10
            quality_score = max(0, min(100, quality_score))
            metrics['quality_score'] = quality_score
            
            # Quality rating
            if quality_score >= 80:
                metrics['quality_rating'] = 'excellent'
            elif quality_score >= 60:
                metrics['quality_rating'] = 'good'
            elif quality_score >= 40:
                metrics['quality_rating'] = 'fair'
            else:
                metrics['quality_rating'] = 'poor'
            
        except Exception as e:
            logger.error(f"Error assessing image quality: {e}")
            issues.append(f"Failed to assess image quality: {str(e)}")
            metrics['quality_score'] = 0
            metrics['quality_rating'] = 'unknown'
        
        return {
            'metrics': metrics,
            'issues': issues,
            'quality_score': metrics.get('quality_score', 0),
            'quality_rating': metrics.get('quality_rating', 'unknown')
        }


class ReceiptDataValidator:
    """Validates extracted receipt data for business rules and integrity."""
    
    @staticmethod
    def validate_comprehensive(receipt: ReceiptData) -> Dict[str, Any]:
        """
        Comprehensive validation of receipt data.
        
        Args:
            receipt: ReceiptData object
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'info': []
        }
        
        # Validate individual components
        ReceiptDataValidator._validate_store_info(receipt, results)
        ReceiptDataValidator._validate_financial_data(receipt, results)
        ReceiptDataValidator._validate_line_items(receipt, results)
        ReceiptDataValidator._validate_consistency(receipt, results)
        ReceiptDataValidator._validate_business_rules(receipt, results)
        
        # Set overall validity
        results['is_valid'] = len(results['errors']) == 0
        
        # Calculate validation score
        total_checks = len(results['errors']) + len(results['warnings']) + len(results['info'])
        if total_checks > 0:
            score = 100 - (len(results['errors']) * 20) - (len(results['warnings']) * 5)
            results['validation_score'] = max(0, min(100, score))
        else:
            results['validation_score'] = 100
        
        return results
    
    @staticmethod
    def _validate_store_info(receipt: ReceiptData, results: Dict):
        """Validate store information."""
        # Store name
        if not receipt.store_name:
            results['warnings'].append("No store name detected")
        elif len(receipt.store_name) < 2:
            results['warnings'].append("Store name is too short")
        elif len(receipt.store_name) > 100:
            results['errors'].append("Store name is unreasonably long")
        
        # Date
        if receipt.date:
            # Validate date format
            date_patterns = [
                r'\d{1,2}/\d{1,2}/\d{2,4}',
                r'\d{1,2}-\d{1,2}-\d{2,4}',
                r'\d{4}-\d{2}-\d{2}'
            ]
            is_valid_format = any(re.match(pattern, receipt.date) for pattern in date_patterns)
            if not is_valid_format:
                results['warnings'].append(f"Date format may be invalid: {receipt.date}")
        else:
            results['info'].append("No date detected")
        
        # Phone
        if receipt.phone:
            # Validate phone format
            phone_pattern = r'[\d\(\)\-\.\s]{10,}'
            if not re.search(phone_pattern, receipt.phone):
                results['warnings'].append(f"Phone number format may be invalid: {receipt.phone}")
        
        # Address
        if receipt.address and len(receipt.address) < 5:
            results['warnings'].append("Address is very short")
    
    @staticmethod
    def _validate_financial_data(receipt: ReceiptData, results: Dict):
        """Validate financial data."""
        # Total
        if receipt.total is None:
            results['warnings'].append("No total amount detected")
        elif receipt.total < 0:
            results['errors'].append(f"Total is negative: {receipt.total}")
        elif receipt.total == 0:
            results['warnings'].append("Total is zero")
        elif receipt.total > Decimal('100000'):
            results['warnings'].append(f"Total seems very high: {receipt.total}")
        
        # Subtotal
        if receipt.subtotal is not None:
            if receipt.subtotal < 0:
                results['errors'].append(f"Subtotal is negative: {receipt.subtotal}")
            elif receipt.total and receipt.subtotal > receipt.total:
                results['errors'].append(f"Subtotal ({receipt.subtotal}) exceeds total ({receipt.total})")
        
        # Tax
        if receipt.tax is not None:
            if receipt.tax < 0:
                results['errors'].append(f"Tax is negative: {receipt.tax}")
            elif receipt.total and receipt.tax > receipt.total:
                results['errors'].append(f"Tax ({receipt.tax}) exceeds total ({receipt.total})")
            elif receipt.subtotal:
                # Tax rate check (typically 0-15%)
                tax_rate = (receipt.tax / receipt.subtotal) * 100 if receipt.subtotal > 0 else 0
                if tax_rate > 30:
                    results['warnings'].append(f"Tax rate seems high: {tax_rate:.1f}%")
                elif tax_rate < 0:
                    results['errors'].append(f"Tax rate is negative: {tax_rate:.1f}%")
    
    @staticmethod
    def _validate_line_items(receipt: ReceiptData, results: Dict):
        """Validate line items."""
        if not receipt.items:
            results['info'].append("No line items detected")
            return
        
        for i, item in enumerate(receipt.items, 1):
            # Name
            if not item.name or len(item.name) < 1:
                results['errors'].append(f"Item {i} has no name")
            elif len(item.name) > 200:
                results['warnings'].append(f"Item {i} name is very long: {len(item.name)} characters")
            
            # Price
            if item.price is None:
                results['warnings'].append(f"Item {i} ({item.name}) has no price")
            elif item.price < 0:
                results['errors'].append(f"Item {i} ({item.name}) has negative price: {item.price}")
            elif item.price > Decimal('10000'):
                results['warnings'].append(f"Item {i} ({item.name}) has very high price: {item.price}")
            elif item.price == 0:
                results['info'].append(f"Item {i} ({item.name}) has zero price")
            
            # Quantity
            if item.quantity is None or item.quantity <= 0:
                results['warnings'].append(f"Item {i} ({item.name}) has invalid quantity: {item.quantity}")
            elif item.quantity > 1000:
                results['warnings'].append(f"Item {i} ({item.name}) has very high quantity: {item.quantity}")
    
    @staticmethod
    def _validate_consistency(receipt: ReceiptData, results: Dict):
        """Validate consistency between fields."""
        # Total = Subtotal + Tax
        if receipt.total and receipt.subtotal and receipt.tax:
            calculated_total = receipt.subtotal + receipt.tax
            diff = abs(receipt.total - calculated_total)
            
            if diff > Decimal('0.10'):
                results['errors'].append(
                    f"Total mismatch: {receipt.total} != {receipt.subtotal} + {receipt.tax} = {calculated_total}"
                )
            elif diff > Decimal('0.01'):
                results['warnings'].append(
                    f"Small total discrepancy: {diff} (may be due to rounding)"
                )
        
        # Items sum = Subtotal
        if receipt.items and receipt.subtotal:
            items_sum = sum(
                item.price * item.quantity
                for item in receipt.items
                if item.price and item.quantity
            )
            diff = abs(items_sum - receipt.subtotal)
            
            if diff > Decimal('5.00'):
                results['warnings'].append(
                    f"Items sum ({items_sum}) differs significantly from subtotal ({receipt.subtotal})"
                )
    
    @staticmethod
    def _validate_business_rules(receipt: ReceiptData, results: Dict):
        """Validate business rules."""
        # Minimum data requirement
        has_min_data = (
            (receipt.store_name and len(receipt.store_name) > 2) or
            (receipt.total and receipt.total > 0) or
            (receipt.items and len(receipt.items) > 0)
        )
        
        if not has_min_data:
            results['errors'].append("Receipt lacks minimum required data")
        
        # Reasonable receipt check
        if receipt.items and len(receipt.items) > 100:
            results['warnings'].append(f"Receipt has many items: {len(receipt.items)}")
        
        # Price consistency
        if receipt.items:
            prices = [item.price for item in receipt.items if item.price]
            if prices:
                avg_price = sum(prices) / len(prices)
                for item in receipt.items:
                    if item.price and item.price > avg_price * 10:
                        results['warnings'].append(
                            f"Item '{item.name}' price ({item.price}) is much higher than average ({avg_price:.2f})"
                        )


class OCRResultValidator:
    """Validates OCR extraction results."""
    
    @staticmethod
    def validate_text_quality(text: str) -> Dict[str, Any]:
        """
        Validate quality of extracted text.
        
        Args:
            text: Extracted text string
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'is_valid': True,
            'issues': [],
            'metrics': {}
        }
        
        if not text or len(text.strip()) == 0:
            results['is_valid'] = False
            results['issues'].append("No text extracted")
            return results
        
        # Basic metrics
        results['metrics']['length'] = len(text)
        results['metrics']['lines'] = len(text.split('\n'))
        results['metrics']['words'] = len(text.split())
        
        # Character analysis
        alphanumeric = sum(c.isalnum() for c in text)
        special = sum(not c.isalnum() and not c.isspace() for c in text)
        spaces = sum(c.isspace() for c in text)
        
        total_chars = len(text)
        if total_chars > 0:
            results['metrics']['alphanumeric_ratio'] = alphanumeric / total_chars
            results['metrics']['special_ratio'] = special / total_chars
            results['metrics']['space_ratio'] = spaces / total_chars
        
        # Quality checks
        if len(text) < 20:
            results['issues'].append("Very short text extracted")
        
        if results['metrics'].get('alphanumeric_ratio', 0) < 0.5:
            results['issues'].append("Low alphanumeric content - may have many OCR errors")
        
        if results['metrics'].get('special_ratio', 0) > 0.3:
            results['issues'].append("High special character ratio - may indicate OCR issues")
        
        # Look for common OCR errors
        if '|||' in text or '```' in text or '~~~' in text:
            results['issues'].append("Text contains patterns suggesting OCR errors")
        
        results['is_valid'] = len(results['issues']) == 0
        
        return results


def validate_extraction_request(file_data: Any, model_id: str, settings: Dict) -> Tuple[bool, List[str]]:
    """
    Validate complete extraction request.
    
    Args:
        file_data: Uploaded file data
        model_id: Model identifier
        settings: Detection settings
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate file
    if not file_data:
        errors.append("No file provided")
    
    # Validate model
    valid_models = [
        'ocr_tesseract', 'ocr_easyocr', 'ocr_easyocr_spatial',
        'ocr_paddle', 'ocr_paddle_spatial', 'florence2', 'donut_cord', 'craft_detector'
    ]
    if model_id not in valid_models:
        errors.append(f"Invalid model: {model_id}")
    
    # Validate settings
    if settings:
        if 'detection_mode' in settings:
            valid_modes = ['auto', 'manual', 'line', 'column']
            if settings['detection_mode'] not in valid_modes:
                errors.append(f"Invalid detection mode: {settings['detection_mode']}")
        
        if 'manual_regions' in settings and settings['manual_regions']:
            if not isinstance(settings['manual_regions'], list):
                errors.append("manual_regions must be a list")
    
    return len(errors) == 0, errors
