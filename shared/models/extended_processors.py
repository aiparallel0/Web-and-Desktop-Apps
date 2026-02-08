"""
Extended Processor Module with Column and Region Support

This module extends the base processors to handle:
- Multi-column text extraction
- Manual region processing
- Line-by-line detection modes
- Enhanced preprocessing integration

All processors are wrapped to support the advanced preprocessing features.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional, Union
from PIL import Image
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils.data import ExtractionResult, ReceiptData, LineItem
from shared.utils.advanced_preprocessing import (
    PreprocessingResult,
    PreprocessingSettings,
    ColumnDetector,
    RegionExtractor,
    ImagePreprocessor
)

logger = logging.getLogger(__name__)


class ExtendedProcessorWrapper:
    """
    Wrapper for processors that adds column and region support.
    
    This wrapper intercepts extract() calls and:
    1. Handles column splitting if multiple columns detected
    2. Handles manual region extraction if regions specified
    3. Combines results from multiple regions/columns
    4. Maintains compatibility with existing processors
    """
    
    def __init__(self, base_processor, preprocessing_result: Optional[PreprocessingResult] = None):
        """
        Initialize the wrapper.
        
        Args:
            base_processor: The underlying processor instance
            preprocessing_result: Result from preprocessing with column/region info
        """
        self.base_processor = base_processor
        self.preprocessing_result = preprocessing_result
        self.model_config = getattr(base_processor, 'model_config', {})
        self.model_name = getattr(base_processor, 'model_name', 'Unknown')
    
    def extract(self, image_path: str) -> ExtractionResult:
        """
        Extract with column and region support.
        
        Args:
            image_path: Path to preprocessed image
            
        Returns:
            ExtractionResult with combined data from all regions/columns
        """
        try:
            # If no preprocessing result, use base processor directly
            if not self.preprocessing_result:
                return self.base_processor.extract(image_path)
            
            # Load the preprocessed image
            image = Image.open(image_path)
            
            # Case 1: Column mode - split image into columns and process each
            if (self.preprocessing_result.detected_columns and 
                len(self.preprocessing_result.detected_columns) > 1):
                return self._extract_with_columns(image)
            
            # Case 2: Manual regions - extract and process each region
            elif (self.preprocessing_result.manual_regions and 
                  len(self.preprocessing_result.manual_regions) > 0):
                return self._extract_with_regions(image)
            
            # Case 3: No special handling - process normally
            else:
                return self.base_processor.extract(image_path)
                
        except Exception as e:
            logger.error(f"Error in extended processor: {e}", exc_info=True)
            return ExtractionResult(
                success=False,
                error=f"Extended processing failed: {str(e)}"
            )
    
    def _extract_with_columns(self, image: Image.Image) -> ExtractionResult:
        """Extract text from each column and combine results."""
        try:
            columns = self.preprocessing_result.detected_columns
            logger.info(f"Processing {len(columns)} columns")
            
            # Split image into columns
            column_images = ColumnDetector.split_columns(image, columns)
            
            # Process each column
            column_results = []
            for i, col_img in enumerate(column_images):
                # Save column image temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                    col_img.save(tmp.name, 'PNG')
                    col_path = tmp.name
                
                try:
                    # Extract from column
                    result = self.base_processor.extract(col_path)
                    column_results.append(result)
                finally:
                    # Clean up temp file
                    if os.path.exists(col_path):
                        os.unlink(col_path)
            
            # Combine results from all columns
            combined_result = self._combine_column_results(column_results)
            logger.info(f"Combined results from {len(column_results)} columns")
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Error extracting with columns: {e}")
            return ExtractionResult(
                success=False,
                error=f"Column extraction failed: {str(e)}"
            )
    
    def _extract_with_regions(self, image: Image.Image) -> ExtractionResult:
        """Extract text from each manual region and combine results."""
        try:
            regions = self.preprocessing_result.manual_regions
            logger.info(f"Processing {len(regions)} manual regions")
            
            # Extract regions
            region_images = RegionExtractor.extract_regions(image, regions)
            
            # Process each region
            region_results = []
            for i, region_img in enumerate(region_images):
                # Save region image temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                    region_img.save(tmp.name, 'PNG')
                    region_path = tmp.name
                
                try:
                    # Extract from region
                    result = self.base_processor.extract(region_path)
                    region_results.append(result)
                finally:
                    # Clean up temp file
                    if os.path.exists(region_path):
                        os.unlink(region_path)
            
            # Combine results from all regions
            combined_result = self._combine_region_results(region_results)
            logger.info(f"Combined results from {len(region_results)} regions")
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Error extracting with regions: {e}")
            return ExtractionResult(
                success=False,
                error=f"Region extraction failed: {str(e)}"
            )
    
    def _combine_column_results(self, results: List[ExtractionResult]) -> ExtractionResult:
        """Combine extraction results from multiple columns."""
        try:
            # Filter successful results
            successful_results = [r for r in results if getattr(r, 'success', False)]
            
            if not successful_results:
                return ExtractionResult(
                    success=False,
                    error="No successful column extractions"
                )
            
            # Combine receipt data
            combined_receipt = ReceiptData()
            all_items = []
            
            for result in successful_results:
                if hasattr(result, 'data') and result.data:
                    receipt = result.data
                    
                    # Take first non-empty value for scalar fields
                    if not combined_receipt.store_name and getattr(receipt, 'store_name', None):
                        combined_receipt.store_name = receipt.store_name
                    
                    if not combined_receipt.total and getattr(receipt, 'total', None):
                        combined_receipt.total = receipt.total
                    
                    if not combined_receipt.date and getattr(receipt, 'date', None):
                        combined_receipt.date = receipt.date
                    
                    # Combine items from all columns
                    if hasattr(receipt, 'items') and receipt.items:
                        all_items.extend(receipt.items)
            
            combined_receipt.items = all_items
            combined_receipt.model_used = self.model_name + " (multi-column)"
            
            return ExtractionResult(
                success=True,
                data=combined_receipt,
                confidence_score=0.85  # Slightly lower confidence for combined results
            )
            
        except Exception as e:
            logger.error(f"Error combining column results: {e}")
            return ExtractionResult(
                success=False,
                error=f"Failed to combine results: {str(e)}"
            )
    
    def _combine_region_results(self, results: List[ExtractionResult]) -> ExtractionResult:
        """Combine extraction results from multiple manual regions."""
        try:
            # Filter successful results
            successful_results = [r for r in results if getattr(r, 'success', False)]
            
            if not successful_results:
                return ExtractionResult(
                    success=False,
                    error="No successful region extractions"
                )
            
            # For manual regions, concatenate all text
            combined_receipt = ReceiptData()
            all_items = []
            all_text_lines = []
            
            for result in successful_results:
                if hasattr(result, 'data') and result.data:
                    receipt = result.data
                    
                    # Take first non-empty value for scalar fields
                    if not combined_receipt.store_name and getattr(receipt, 'store_name', None):
                        combined_receipt.store_name = receipt.store_name
                    
                    if not combined_receipt.total and getattr(receipt, 'total', None):
                        combined_receipt.total = receipt.total
                    
                    if not combined_receipt.date and getattr(receipt, 'date', None):
                        combined_receipt.date = receipt.date
                    
                    # Combine items
                    if hasattr(receipt, 'items') and receipt.items:
                        all_items.extend(receipt.items)
            
            combined_receipt.items = all_items
            combined_receipt.model_used = self.model_name + " (manual regions)"
            
            return ExtractionResult(
                success=True,
                data=combined_receipt,
                confidence_score=0.9  # Higher confidence for manually selected regions
            )
            
        except Exception as e:
            logger.error(f"Error combining region results: {e}")
            return ExtractionResult(
                success=False,
                error=f"Failed to combine results: {str(e)}"
            )


def create_extended_processor(base_processor, preprocessing_result: Optional[PreprocessingResult] = None):
    """
    Factory function to create an extended processor wrapper.
    
    Args:
        base_processor: The base processor instance
        preprocessing_result: Optional preprocessing result with column/region info
        
    Returns:
        ExtendedProcessorWrapper or base processor if no special handling needed
    """
    # Only wrap if we have column or region data
    if preprocessing_result and (
        (preprocessing_result.detected_columns and len(preprocessing_result.detected_columns) > 1) or
        (preprocessing_result.manual_regions and len(preprocessing_result.manual_regions) > 0)
    ):
        return ExtendedProcessorWrapper(base_processor, preprocessing_result)
    else:
        return base_processor
