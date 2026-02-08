"""
Result Processing and Validation Module

This module provides comprehensive result processing including:
- Result format conversion and standardization
- Data validation and sanitization
- Error handling and recovery
- Response formatting for API
- Metadata enrichment
"""

import os
import sys
import logging
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from decimal import Decimal
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils.data import ReceiptData, LineItem, ExtractionResult

logger = logging.getLogger(__name__)


class ResultConverter:
    """Converts extraction results to different formats."""
    
    @staticmethod
    def to_api_response(result: ExtractionResult, include_metadata: bool = True) -> Dict[str, Any]:
        """
        Convert ExtractionResult to API response format.
        
        Args:
            result: ExtractionResult object
            include_metadata: Whether to include metadata
            
        Returns:
            Dictionary in API response format
        """
        try:
            response = {
                'success': result.success,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            if result.success and result.data:
                response['data'] = ResultConverter._serialize_receipt_data(result.data)
                
                if hasattr(result, 'confidence_score') and result.confidence_score is not None:
                    response['confidence'] = float(result.confidence_score)
                
                if include_metadata:
                    response['metadata'] = ResultConverter._build_metadata(result)
            
            else:
                response['error'] = result.error or 'Unknown error'
                if hasattr(result, 'error_type'):
                    response['error_type'] = result.error_type
            
            return response
            
        except Exception as e:
            logger.error(f"Error converting result to API response: {e}")
            return {
                'success': False,
                'error': f'Result conversion failed: {str(e)}',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
    
    @staticmethod
    def _serialize_receipt_data(receipt: ReceiptData) -> Dict[str, Any]:
        """Serialize ReceiptData to dictionary."""
        data = {}
        
        # Store name
        if receipt.store_name:
            data['store_name'] = receipt.store_name
        
        # Date
        if receipt.date:
            data['date'] = receipt.date
        
        # Financial fields
        if receipt.total is not None:
            data['total'] = str(receipt.total) if isinstance(receipt.total, Decimal) else receipt.total
        
        if receipt.subtotal is not None:
            data['subtotal'] = str(receipt.subtotal) if isinstance(receipt.subtotal, Decimal) else receipt.subtotal
        
        if receipt.tax is not None:
            data['tax'] = str(receipt.tax) if isinstance(receipt.tax, Decimal) else receipt.tax
        
        # Contact info
        if receipt.phone:
            data['phone'] = receipt.phone
        
        if receipt.address:
            data['address'] = receipt.address
        
        # Line items
        if receipt.items:
            data['items'] = [
                ResultConverter._serialize_line_item(item)
                for item in receipt.items
            ]
            data['item_count'] = len(receipt.items)
        else:
            data['items'] = []
            data['item_count'] = 0
        
        return data
    
    @staticmethod
    def _serialize_line_item(item: LineItem) -> Dict[str, Any]:
        """Serialize LineItem to dictionary."""
        return {
            'name': item.name,
            'price': str(item.price) if isinstance(item.price, Decimal) else item.price,
            'quantity': item.quantity,
            'total': str(item.price * item.quantity) if item.price and item.quantity else None
        }
    
    @staticmethod
    def _build_metadata(result: ExtractionResult) -> Dict[str, Any]:
        """Build metadata from extraction result."""
        metadata = {}
        
        # Processing time
        if hasattr(result, 'processing_time'):
            metadata['processing_time'] = result.processing_time
        
        # Model used
        if hasattr(result.data, 'model_used') and result.data.model_used:
            metadata['model'] = result.data.model_used
        
        # Raw text
        if hasattr(result, 'raw_text') and result.raw_text:
            metadata['raw_text_length'] = len(result.raw_text)
        
        # Additional metadata
        if hasattr(result, 'metadata') and result.metadata:
            metadata.update(result.metadata)
        
        return metadata


class ResultValidator:
    """Validates and sanitizes extraction results."""
    
    @staticmethod
    def validate_receipt(receipt: ReceiptData) -> Tuple[bool, List[str]]:
        """
        Validate receipt data.
        
        Args:
            receipt: ReceiptData object
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check for minimum required fields
        if not receipt.store_name and not receipt.total:
            issues.append("Missing both store name and total")
        
        # Validate total
        if receipt.total is not None:
            if receipt.total < 0:
                issues.append("Total is negative")
            elif receipt.total == 0:
                issues.append("Total is zero")
            elif receipt.total > 100000:
                issues.append("Total seems unreasonably high")
        
        # Validate item prices
        if receipt.items:
            for i, item in enumerate(receipt.items):
                if item.price is not None:
                    if item.price < 0:
                        issues.append(f"Item {i+1} has negative price")
                    elif item.price > 10000:
                        issues.append(f"Item {i+1} price seems unreasonably high")
                
                if item.quantity is not None and item.quantity < 0:
                    issues.append(f"Item {i+1} has negative quantity")
        
        # Check total consistency
        if receipt.total and receipt.subtotal and receipt.tax:
            calculated = receipt.subtotal + receipt.tax
            if abs(calculated - receipt.total) > Decimal('0.10'):
                issues.append(f"Total mismatch: {receipt.total} != {calculated}")
        
        # Check items sum
        if receipt.items and receipt.subtotal:
            items_sum = sum(
                item.price * item.quantity
                for item in receipt.items
                if item.price and item.quantity
            )
            if abs(items_sum - receipt.subtotal) > Decimal('1.00'):
                issues.append(f"Items sum doesn't match subtotal")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    @staticmethod
    def sanitize_receipt(receipt: ReceiptData) -> ReceiptData:
        """
        Sanitize receipt data by removing invalid values.
        
        Args:
            receipt: ReceiptData object
            
        Returns:
            Sanitized ReceiptData
        """
        # Sanitize store name
        if receipt.store_name:
            receipt.store_name = receipt.store_name.strip()
            if len(receipt.store_name) > 100:
                receipt.store_name = receipt.store_name[:100]
        
        # Sanitize financial fields
        if receipt.total is not None and receipt.total < 0:
            receipt.total = None
        
        if receipt.subtotal is not None and receipt.subtotal < 0:
            receipt.subtotal = None
        
        if receipt.tax is not None and receipt.tax < 0:
            receipt.tax = None
        
        # Sanitize items
        if receipt.items:
            valid_items = []
            for item in receipt.items:
                if item.name and len(item.name) > 1:
                    # Sanitize name
                    item.name = item.name.strip()
                    if len(item.name) > 200:
                        item.name = item.name[:200]
                    
                    # Sanitize price
                    if item.price is not None and item.price < 0:
                        item.price = None
                    
                    # Sanitize quantity
                    if item.quantity is not None and item.quantity < 0:
                        item.quantity = 1
                    
                    valid_items.append(item)
            
            receipt.items = valid_items
        
        return receipt


class ErrorHandler:
    """Handles and formats errors from extraction."""
    
    @staticmethod
    def format_error_response(error: Exception, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Format error as API response.
        
        Args:
            error: Exception object
            context: Optional context information
            
        Returns:
            Error response dictionary
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        response = {
            'success': False,
            'error': error_message,
            'error_type': error_type,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Add context if provided
        if context:
            response['context'] = context
        
        # Add specific error details based on type
        if isinstance(error, ImportError):
            response['resolution'] = 'Install required dependencies'
        elif isinstance(error, FileNotFoundError):
            response['resolution'] = 'Check if file exists and path is correct'
        elif isinstance(error, PermissionError):
            response['resolution'] = 'Check file permissions'
        
        return response
    
    @staticmethod
    def create_partial_result(partial_data: ReceiptData, error: str) -> ExtractionResult:
        """
        Create partial result when extraction partially succeeds.
        
        Args:
            partial_data: Partially extracted data
            error: Error message explaining what failed
            
        Returns:
            ExtractionResult with partial data
        """
        return ExtractionResult(
            success=False,
            data=partial_data,
            error=f"Partial extraction: {error}",
            confidence_score=0.5  # Lower confidence for partial results
        )


class ResponseEnricher:
    """Enriches API responses with additional information."""
    
    @staticmethod
    def enrich_response(response: Dict[str, Any], additional_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Enrich response with additional data.
        
        Args:
            response: Base response dictionary
            additional_data: Additional data to include
            
        Returns:
            Enriched response
        """
        enriched = response.copy()
        
        # Add API version
        enriched['api_version'] = '2.0'
        
        # Add request ID
        import uuid
        enriched['request_id'] = str(uuid.uuid4())
        
        # Add processing metadata
        if 'metadata' not in enriched:
            enriched['metadata'] = {}
        
        enriched['metadata']['server_timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add additional data if provided
        if additional_data:
            enriched['metadata'].update(additional_data)
        
        return enriched
    
    @staticmethod
    def add_suggestions(response: Dict[str, Any], receipt_data: Optional[ReceiptData] = None) -> Dict[str, Any]:
        """
        Add suggestions for improving extraction quality.
        
        Args:
            response: Response dictionary
            receipt_data: Extracted receipt data
            
        Returns:
            Response with suggestions
        """
        if not response.get('success'):
            # Add suggestions for failed extractions
            if 'suggestions' not in response:
                response['suggestions'] = []
            
            response['suggestions'].extend([
                "Try a different OCR model",
                "Ensure image is clear and well-lit",
                "Check if image is properly oriented"
            ])
        
        elif receipt_data:
            # Add suggestions based on extracted data
            suggestions = []
            
            if not receipt_data.store_name:
                suggestions.append("Store name could not be detected")
            
            if not receipt_data.items or len(receipt_data.items) == 0:
                suggestions.append("No line items detected - try adjusting image quality")
            
            if not receipt_data.date:
                suggestions.append("Date could not be detected")
            
            if suggestions:
                response['suggestions'] = suggestions
        
        return response


def process_extraction_result(result: ExtractionResult,
                              preprocessing_metadata: Optional[Dict] = None,
                              detection_settings: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Process extraction result into final API response.
    
    Args:
        result: ExtractionResult from processor
        preprocessing_metadata: Metadata from preprocessing
        detection_settings: Detection settings used
        
    Returns:
        Complete API response dictionary
    """
    try:
        # Convert to API response
        response = ResultConverter.to_api_response(result, include_metadata=True)
        
        # Validate if successful
        if result.success and result.data:
            is_valid, issues = ResultValidator.validate_receipt(result.data)
            
            if not is_valid:
                logger.warning(f"Receipt validation issues: {issues}")
                response['validation_issues'] = issues
            
            # Sanitize data
            result.data = ResultValidator.sanitize_receipt(result.data)
        
        # Add preprocessing metadata
        if preprocessing_metadata:
            if 'metadata' not in response:
                response['metadata'] = {}
            response['metadata']['preprocessing'] = preprocessing_metadata
        
        # Add detection settings
        if detection_settings:
            if 'metadata' not in response:
                response['metadata'] = {}
            response['metadata']['detection_settings'] = detection_settings
        
        # Enrich response
        response = ResponseEnricher.enrich_response(response)
        
        # Add suggestions
        if result.data:
            response = ResponseEnricher.add_suggestions(response, result.data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing extraction result: {e}", exc_info=True)
        return ErrorHandler.format_error_response(e)
