"""
OCR Processor Enhancements

This module provides comprehensive enhancements to OCR processors including:
- Better text extraction with multiple strategies
- Improved line item detection
- Enhanced receipt parsing with validation
- Multi-pass OCR with confidence scoring
- Fallback strategies for difficult receipts
"""

import os
import sys
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

# Import base utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.utils.data import ReceiptData, LineItem, ExtractionResult

logger = logging.getLogger(__name__)


class EnhancedTextExtractor:
    """Enhanced text extraction with multiple strategies."""
    
    @staticmethod
    def extract_with_multiple_strategies(image_path: str, ocr_engine) -> List[Tuple[str, List[str], float]]:
        """
        Extract text using multiple strategies and confidence levels.
        
        Args:
            image_path: Path to image file
            ocr_engine: OCR engine instance (Tesseract, EasyOCR, Paddle)
            
        Returns:
            List of (strategy_name, text_lines, confidence) tuples
        """
        strategies = []
        
        try:
            # Strategy 1: Direct OCR with default settings
            result1 = EnhancedTextExtractor._extract_default(image_path, ocr_engine)
            if result1:
                strategies.append(('default', result1[0], result1[1]))
            
            # Strategy 2: Enhanced preprocessing
            result2 = EnhancedTextExtractor._extract_enhanced(image_path, ocr_engine)
            if result2:
                strategies.append(('enhanced', result2[0], result2[1]))
            
            # Strategy 3: High contrast mode
            result3 = EnhancedTextExtractor._extract_high_contrast(image_path, ocr_engine)
            if result3:
                strategies.append(('high_contrast', result3[0], result3[1]))
            
            # Strategy 4: Binarized mode
            result4 = EnhancedTextExtractor._extract_binarized(image_path, ocr_engine)
            if result4:
                strategies.append(('binarized', result4[0], result4[1]))
            
        except Exception as e:
            logger.error(f"Error in multi-strategy extraction: {e}")
        
        return strategies
    
    @staticmethod
    def _extract_default(image_path: str, ocr_engine) -> Optional[Tuple[List[str], float]]:
        """Extract with default settings."""
        try:
            # Implementation depends on OCR engine type
            # This is a placeholder - actual implementation would call the OCR engine
            return None
        except Exception as e:
            logger.debug(f"Default extraction failed: {e}")
            return None
    
    @staticmethod
    def _extract_enhanced(image_path: str, ocr_engine) -> Optional[Tuple[List[str], float]]:
        """Extract with enhanced preprocessing."""
        try:
            image = Image.open(image_path)
            
            # Apply enhancements
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            
            # Save and process
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                image.save(tmp.name)
                temp_path = tmp.name
            
            try:
                # Process enhanced image
                # Placeholder for actual OCR call
                return None
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.debug(f"Enhanced extraction failed: {e}")
            return None
    
    @staticmethod
    def _extract_high_contrast(image_path: str, ocr_engine) -> Optional[Tuple[List[str], float]]:
        """Extract with very high contrast."""
        try:
            image = Image.open(image_path)
            
            # Apply very high contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(3.0)
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Save and process
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                image.save(tmp.name)
                temp_path = tmp.name
            
            try:
                # Process high contrast image
                return None
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.debug(f"High contrast extraction failed: {e}")
            return None
    
    @staticmethod
    def _extract_binarized(image_path: str, ocr_engine) -> Optional[Tuple[List[str], float]]:
        """Extract from binarized image."""
        try:
            image = Image.open(image_path)
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Apply threshold
            threshold = 128
            image = image.point(lambda p: 255 if p > threshold else 0, '1')
            
            # Save and process
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                image.save(tmp.name)
                temp_path = tmp.name
            
            try:
                # Process binarized image
                return None
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.debug(f"Binarized extraction failed: {e}")
            return None


class EnhancedLineItemExtractor:
    """Enhanced line item extraction with multiple patterns."""
    
    # Additional patterns for line items
    ITEM_PATTERNS = [
        # Pattern 1: Name ... Price
        r'^(.+?)\s+[\.\s]{2,}\s*\$?(\d+\.\d{2})$',
        # Pattern 2: Name Price (no dots)
        r'^(.+?)\s+\$?(\d+\.\d{2})$',
        # Pattern 3: Name $Price
        r'^(.+?)\s*\$(\d+\.\d{2})$',
        # Pattern 4: Quantity x Name @ Price
        r'^(\d+)\s*[xX]\s*(.+?)\s*@\s*\$?(\d+\.\d{2})$',
        # Pattern 5: Name Quantity Price
        r'^(.+?)\s+(\d+)\s+\$?(\d+\.\d{2})$',
        # Pattern 6: SKU Name Price
        r'^(\d{6,})\s+(.+?)\s+\$?(\d+\.\d{2})$',
    ]
    
    @staticmethod
    def extract_line_items(text_lines: List[str], aggressive: bool = False) -> List[LineItem]:
        """
        Extract line items from text lines.
        
        Args:
            text_lines: List of text strings
            aggressive: If True, use more aggressive pattern matching
            
        Returns:
            List of LineItem objects
        """
        items = []
        
        for line in text_lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Try each pattern
            for pattern in EnhancedLineItemExtractor.ITEM_PATTERNS:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    item = EnhancedLineItemExtractor._create_item_from_match(match, pattern)
                    if item:
                        items.append(item)
                        break
            
            # Aggressive mode: try fuzzy matching
            if aggressive and not any(item for item in items if item.name in line):
                fuzzy_item = EnhancedLineItemExtractor._fuzzy_extract_item(line)
                if fuzzy_item:
                    items.append(fuzzy_item)
        
        return items
    
    @staticmethod
    def _create_item_from_match(match, pattern: str) -> Optional[LineItem]:
        """Create LineItem from regex match."""
        try:
            groups = match.groups()
            
            # Different patterns have different group structures
            if len(groups) == 2:
                # Name and price
                name = groups[0].strip()
                price = Decimal(groups[1])
                return LineItem(name=name, price=price, quantity=1)
            
            elif len(groups) == 3:
                # Could be quantity x name @ price or name quantity price
                if 'x' in pattern.lower() or '@' in pattern:
                    quantity = int(groups[0])
                    name = groups[1].strip()
                    price = Decimal(groups[2])
                    return LineItem(name=name, price=price, quantity=quantity)
                else:
                    # SKU Name Price or Name Quantity Price
                    name = groups[1].strip() if groups[0].isdigit() and len(groups[0]) > 5 else groups[0].strip()
                    quantity = int(groups[1]) if not groups[0].isdigit() or len(groups[0]) <= 5 else 1
                    price = Decimal(groups[2])
                    return LineItem(name=name, price=price, quantity=quantity)
            
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to create item from match: {e}")
            return None
    
    @staticmethod
    def _fuzzy_extract_item(line: str) -> Optional[LineItem]:
        """Try to extract item using fuzzy logic."""
        try:
            # Look for any price pattern
            price_match = re.search(r'\$?(\d+\.\d{2})', line)
            if not price_match:
                return None
            
            price = Decimal(price_match.group(1))
            
            # Everything before the price is the name
            name = line[:price_match.start()].strip()
            
            # Clean up the name
            name = re.sub(r'[\.]{2,}', '', name)  # Remove multiple dots
            name = re.sub(r'\s+', ' ', name)  # Normalize spaces
            
            if len(name) < 2:
                return None
            
            return LineItem(name=name, price=price, quantity=1)
            
        except Exception as e:
            logger.debug(f"Fuzzy extraction failed: {e}")
            return None


class EnhancedReceiptParser:
    """Enhanced receipt parsing with validation."""
    
    @staticmethod
    def parse_receipt(text_lines: List[str], extract_items: bool = True) -> ReceiptData:
        """
        Parse receipt data from text lines with enhanced extraction.
        
        Args:
            text_lines: List of text strings
            extract_items: Whether to extract line items
            
        Returns:
            ReceiptData object
        """
        receipt = ReceiptData()
        
        try:
            # Extract store name (usually in first few lines)
            receipt.store_name = EnhancedReceiptParser._extract_store_name(text_lines)
            
            # Extract date
            receipt.date = EnhancedReceiptParser._extract_date(text_lines)
            
            # Extract total
            receipt.total = EnhancedReceiptParser._extract_total(text_lines)
            
            # Extract subtotal and tax
            receipt.subtotal = EnhancedReceiptParser._extract_subtotal(text_lines)
            receipt.tax = EnhancedReceiptParser._extract_tax(text_lines)
            
            # Extract phone and address
            receipt.phone = EnhancedReceiptParser._extract_phone(text_lines)
            receipt.address = EnhancedReceiptParser._extract_address(text_lines)
            
            # Extract line items
            if extract_items:
                receipt.items = EnhancedLineItemExtractor.extract_line_items(text_lines, aggressive=True)
            
            # Validate and fix inconsistencies
            receipt = EnhancedReceiptParser._validate_and_fix(receipt)
            
        except Exception as e:
            logger.error(f"Error parsing receipt: {e}")
        
        return receipt
    
    @staticmethod
    def _extract_store_name(lines: List[str]) -> Optional[str]:
        """Extract store name from first few lines."""
        # Look in first 10 lines
        for line in lines[:10]:
            line = line.strip()
            # Store names are usually short, capitalized, and near the top
            if 3 <= len(line) <= 50 and line[0].isupper():
                # Skip common words
                if not any(word in line.lower() for word in ['total', 'subtotal', 'tax', 'date', 'time', 'receipt']):
                    return line
        return None
    
    @staticmethod
    def _extract_date(lines: List[str]) -> Optional[str]:
        """Extract date from text lines."""
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}-\d{1,2}-\d{2,4}',
            r'\d{4}-\d{2}-\d{2}',
            r'[A-Z][a-z]+ \d{1,2},? \d{4}',
        ]
        
        for line in lines:
            for pattern in date_patterns:
                match = re.search(pattern, line)
                if match:
                    return match.group(0)
        return None
    
    @staticmethod
    def _extract_total(lines: List[str]) -> Optional[Decimal]:
        """Extract total amount."""
        # Look for "TOTAL" or "GRAND TOTAL"
        for line in lines:
            if re.search(r'\bTOTAL\b', line, re.IGNORECASE):
                # Extract price
                price_match = re.search(r'\$?(\d+\.\d{2})', line)
                if price_match:
                    try:
                        return Decimal(price_match.group(1))
                    except:
                        pass
        return None
    
    @staticmethod
    def _extract_subtotal(lines: List[str]) -> Optional[Decimal]:
        """Extract subtotal amount."""
        for line in lines:
            if re.search(r'\bSUBTOTAL\b', line, re.IGNORECASE):
                price_match = re.search(r'\$?(\d+\.\d{2})', line)
                if price_match:
                    try:
                        return Decimal(price_match.group(1))
                    except:
                        pass
        return None
    
    @staticmethod
    def _extract_tax(lines: List[str]) -> Optional[Decimal]:
        """Extract tax amount."""
        for line in lines:
            if re.search(r'\bTAX\b', line, re.IGNORECASE):
                price_match = re.search(r'\$?(\d+\.\d{2})', line)
                if price_match:
                    try:
                        return Decimal(price_match.group(1))
                    except:
                        pass
        return None
    
    @staticmethod
    def _extract_phone(lines: List[str]) -> Optional[str]:
        """Extract phone number."""
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        for line in lines:
            match = re.search(phone_pattern, line)
            if match:
                return match.group(0)
        return None
    
    @staticmethod
    def _extract_address(lines: List[str]) -> Optional[str]:
        """Extract address."""
        # Look for lines with street indicators
        address_indicators = ['st', 'street', 'ave', 'avenue', 'blvd', 'road', 'rd', 'drive', 'dr']
        
        for i, line in enumerate(lines[:15]):  # Check first 15 lines
            line_lower = line.lower()
            if any(indicator in line_lower for indicator in address_indicators):
                # Include this line and possibly next line (for city/state/zip)
                address_parts = [line.strip()]
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # Check if next line looks like city/state/zip
                    if re.search(r'\d{5}', next_line):
                        address_parts.append(next_line)
                return ' '.join(address_parts)
        return None
    
    @staticmethod
    def _validate_and_fix(receipt: ReceiptData) -> ReceiptData:
        """Validate receipt data and fix inconsistencies."""
        # Check if total matches sum of items
        if receipt.items and receipt.total:
            items_sum = sum(item.price * item.quantity for item in receipt.items)
            
            # If items sum is close to subtotal, that's good
            if receipt.subtotal and abs(items_sum - receipt.subtotal) < Decimal('0.50'):
                pass  # Validated
            # If items sum + tax is close to total, calculate missing values
            elif abs(items_sum - receipt.total) < Decimal('0.50'):
                # Total is items sum, no tax
                receipt.subtotal = items_sum
                receipt.tax = Decimal('0.00')
            
        # Ensure subtotal + tax = total (within rounding)
        if receipt.subtotal and receipt.tax and receipt.total:
            calculated_total = receipt.subtotal + receipt.tax
            if abs(calculated_total - receipt.total) > Decimal('0.02'):
                logger.warning(f"Total mismatch: {receipt.total} vs calculated {calculated_total}")
        
        return receipt


class ConfidenceScorer:
    """Calculate confidence scores for extraction results."""
    
    @staticmethod
    def score_receipt(receipt: ReceiptData) -> float:
        """
        Calculate confidence score for extracted receipt data.
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 0.0
        max_score = 0.0
        
        # Store name (20 points)
        max_score += 20
        if receipt.store_name:
            score += 20
        
        # Total (30 points)
        max_score += 30
        if receipt.total and receipt.total > 0:
            score += 30
        
        # Date (15 points)
        max_score += 15
        if receipt.date:
            score += 15
        
        # Items (20 points)
        max_score += 20
        if receipt.items and len(receipt.items) > 0:
            score += 20
        
        # Subtotal and tax (10 points)
        max_score += 10
        if receipt.subtotal or receipt.tax:
            score += 5
        if receipt.subtotal and receipt.tax:
            score += 5
        
        # Address or phone (5 points)
        max_score += 5
        if receipt.address or receipt.phone:
            score += 5
        
        # Calculate final confidence
        confidence = score / max_score if max_score > 0 else 0.0
        
        return confidence
