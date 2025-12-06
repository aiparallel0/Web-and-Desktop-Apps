#!/usr/bin/env python3
"""
=============================================================================
Batch Receipt OCR Processor
=============================================================================

This script processes all 20 receipt images (0.jpg - 19.jpg + 6.JPG) using OCR
and exports structured data to a single JSON file for development purposes.

Features:
- Processes all receipt images in the repository root
- Robust exception handling to continue processing even if individual images fail
- Extracts: items, dates, company names, totals, taxes, addresses, phone numbers
- Exports comprehensive JSON file with all extraction results
- Provides detailed progress logging and error reporting

Usage:
    python tools/scripts/batch_receipt_processor.py
    python tools/scripts/batch_receipt_processor.py --output receipts_data.json
    python tools/scripts/batch_receipt_processor.py --model tesseract
    python tools/scripts/batch_receipt_processor.py --verbose

Output Format:
    {
        "metadata": {
            "processed_at": "2025-12-06T09:30:00",
            "total_images": 20,
            "successful_extractions": 18,
            "failed_extractions": 2
        },
        "receipts": [
            {
                "image_file": "0.jpg",
                "success": true,
                "company_name": "Store Name",
                "date": "2024-01-15",
                "total": "45.67",
                "subtotal": "42.50",
                "tax": "3.17",
                "items": [
                    {"name": "Product 1", "quantity": 2, "price": "10.50"},
                    ...
                ],
                "address": "123 Main St",
                "phone": "555-1234",
                ...
            },
            ...
        ]
    }

=============================================================================
"""

import sys
import os
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
import traceback

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="scripts.batch_receipt_processor",
            file_path=__file__,
            description="Batch OCR processor for receipt images with comprehensive JSON export",
            dependencies=["shared.models.ocr", "shared.models.config", "shared.utils.data"],
            exports=["process_all_receipts", "export_to_json"]
        ))
    except Exception:
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@contextmanager
def suppress_logging(logger_names: List[str], level: int = logging.ERROR):
    """
    Context manager to temporarily suppress logging for specific loggers.
    
    Args:
        logger_names: List of logger names to suppress
        level: Logging level to set during suppression
        
    Yields:
        None
        
    Example:
        with suppress_logging(['shared.models.ocr_processor']):
            # Code with suppressed logging
            process_image()
    """
    loggers = [(name, logging.getLogger(name)) for name in logger_names]
    original_levels = [(name, logger.level) for name, logger in loggers]
    
    try:
        # Set suppression levels
        for name, logger in loggers:
            logger.setLevel(level)
        yield
    finally:
        # Restore original levels
        for (name, original_level), (_, logger) in zip(original_levels, loggers):
            logger.setLevel(original_level)


def find_receipt_images(project_root: Path) -> List[Path]:
    """
    Find all receipt image files in the project root.
    
    Looks for:
    - 0.jpg through 19.jpg
    - 6.JPG (uppercase)
    - Any other .jpg/.JPG files
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        Sorted list of image file paths
    """
    image_files = []
    
    # First, try numbered files 0-19
    for i in range(20):
        for ext in ['jpg', 'JPG']:
            img_path = project_root / f"{i}.{ext}"
            if img_path.exists() and img_path not in image_files:
                image_files.append(img_path)
                break  # Found this number, move to next
    
    # Also check for any other .jpg/.JPG files we might have missed
    for pattern in ['*.jpg', '*.JPG']:
        for img_path in project_root.glob(pattern):
            if img_path not in image_files:
                image_files.append(img_path)
    
    # Sort by filename for consistent ordering
    image_files.sort(key=lambda p: p.name.lower())
    
    return image_files


def process_single_receipt(image_path: Path, processor, image_index: int, total_images: int) -> Dict[str, Any]:
    """
    Process a single receipt image and extract structured data.
    
    This function handles all exceptions to ensure batch processing continues
    even if individual images fail.
    
    Args:
        image_path: Path to the receipt image
        processor: OCRProcessor instance
        image_index: Current image index (for progress reporting)
        total_images: Total number of images being processed
        
    Returns:
        Dictionary with extraction results in standardized format
    """
    result = {
        'image_file': image_path.name,
        'image_path': str(image_path),
        'success': False,
        'error': None,
        'company_name': None,
        'date': None,
        'total': None,
        'subtotal': None,
        'tax': None,
        'items': [],
        'address': None,
        'phone': None,
        'payment_method': None,
        'confidence_score': 0.0,
        'model_used': None,
        'processing_time_seconds': 0.0,
        'raw_text_preview': None,
    }
    
    try:
        logger.info(f"[{image_index + 1}/{total_images}] Processing: {image_path.name}")
        
        import time
        start_time = time.time()
        
        # Perform OCR extraction
        extraction = processor.extract(str(image_path))
        
        result['processing_time_seconds'] = round(time.time() - start_time, 2)
        result['success'] = extraction.success
        
        if extraction.success and extraction.data:
            data = extraction.data
            
            # Extract store/company information
            result['company_name'] = data.store_name
            result['address'] = data.store_address
            result['phone'] = data.store_phone
            
            # Extract transaction details
            result['date'] = data.transaction_date
            result['total'] = str(data.total) if data.total else None
            result['subtotal'] = str(data.subtotal) if data.subtotal else None
            result['tax'] = str(data.tax) if data.tax else None
            result['payment_method'] = data.payment_method
            
            # Extract line items
            if data.items:
                result['items'] = [
                    {
                        'name': item.name,
                        'quantity': item.quantity,
                        'unit_price': str(item.unit_price) if item.unit_price else None,
                        'price': str(item.total_price) if item.total_price else None,
                        'category': item.category,
                        'sku': item.sku,
                    }
                    for item in data.items
                ]
            
            # Additional metadata
            result['confidence_score'] = round(data.confidence_score or 0.0, 3)
            result['model_used'] = data.model_used
            
            # Store a preview of raw text if available (first 200 chars)
            if hasattr(data, 'raw_text') and data.raw_text:
                result['raw_text_preview'] = data.raw_text[:200] + '...' if len(data.raw_text) > 200 else data.raw_text
            
            # Log summary
            logger.info(f"  ✓ Success - Company: {result['company_name'] or 'N/A'}, "
                       f"Total: ${result['total'] or 'N/A'}, Items: {len(result['items'])}, "
                       f"Score: {result['confidence_score']:.2f}")
        else:
            result['error'] = extraction.error or "Extraction failed without specific error"
            logger.warning(f"  ✗ Failed - {result['error']}")
    
    except Exception as e:
        result['error'] = f"{type(e).__name__}: {str(e)}"
        result['traceback'] = traceback.format_exc()
        logger.error(f"  ✗ Exception - {result['error']}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"  Traceback:\n{result['traceback']}")
    
    return result


def process_all_receipts(project_root: Path, model_name: str = 'tesseract', verbose: bool = False) -> Dict[str, Any]:
    """
    Process all receipt images in the project root.
    
    Args:
        project_root: Path to the project root directory
        model_name: OCR model to use ('tesseract', 'easyocr', 'paddleocr')
        verbose: Enable verbose logging
        
    Returns:
        Dictionary with metadata and all extraction results
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("=" * 80)
    logger.info("BATCH RECEIPT OCR PROCESSOR")
    logger.info("=" * 80)
    
    # Import required modules
    try:
        from shared.models.ocr_processor import OCRProcessor
        from shared.models.config import get_ocr_config, reset_ocr_config
    except ImportError as e:
        logger.error(f"Failed to import OCR modules: {e}")
        logger.error("Make sure you're running from the project root and dependencies are installed")
        return {
            'metadata': {
                'processed_at': datetime.now().isoformat(),
                'error': f"Import error: {str(e)}",
                'total_images': 0,
                'successful_extractions': 0,
                'failed_extractions': 0,
            },
            'receipts': []
        }
    
    # Reset OCR config to defaults for consistent processing
    reset_ocr_config()
    ocr_config = get_ocr_config()
    
    # Set faster OCR configuration to speed up batch processing
    # Reduce the number of OCR passes for faster processing
    if hasattr(ocr_config, 'max_psm_modes'):
        ocr_config.max_psm_modes = 5  # Reduce from 10 to 5 OCR mode combinations
    if hasattr(ocr_config, 'auto_retry'):
        # Disable auto-retry for batch processing - speeds up sequential image processing
        # by preventing redundant retry attempts when handling multiple images
        ocr_config.auto_retry = False
    
    logger.info(f"\nOCR Configuration:")
    logger.info(f"  Model: {model_name}")
    logger.info(f"  Min Confidence: {ocr_config.min_confidence}")
    logger.info(f"  Auto-tune: {ocr_config.auto_tune}")
    logger.info(f"  Auto-fallback: {ocr_config.auto_fallback}")
    
    # Initialize OCR processor
    model_config = {
        'name': f'{model_name.title()} OCR',
        'type': model_name.lower()
    }
    processor = OCRProcessor(model_config)
    
    # Find all receipt images
    image_files = find_receipt_images(project_root)
    logger.info(f"\nFound {len(image_files)} receipt images")
    
    if not image_files:
        logger.warning("No receipt images found in project root!")
        return {
            'metadata': {
                'processed_at': datetime.now().isoformat(),
                'total_images': 0,
                'successful_extractions': 0,
                'failed_extractions': 0,
            },
            'receipts': []
        }
    
    # Log image list
    logger.info("\nImages to process:")
    for idx, img in enumerate(image_files, 1):
        logger.info(f"  {idx}. {img.name}")
    
    # Process all images
    logger.info("\n" + "=" * 80)
    logger.info("PROCESSING RECEIPTS")
    logger.info("=" * 80 + "\n")
    
    receipts = []
    progress_path = project_root / "receipt_processing_progress.json"
    
    # Suppress verbose OCR logging for cleaner output
    with suppress_logging(['shared.models.ocr_processor', 'shared.utils']):
        for idx, image_path in enumerate(image_files):
            result = process_single_receipt(image_path, processor, idx, len(image_files))
            receipts.append(result)
            
            # Save progress after every 5 images
            if (idx + 1) % 5 == 0:
                progress_data = {
                    'metadata': {
                        'last_updated': datetime.now().isoformat(),
                        'images_processed': idx + 1,
                        'total_images': len(image_files),
                    },
                    'receipts': receipts
                }
                with open(progress_path, 'w', encoding='utf-8') as f:
                    json.dump(progress_data, f, indent=2, ensure_ascii=False)
                logger.info(f"  Progress saved: {idx + 1}/{len(image_files)} images processed")
    
    # Remove progress file if it exists
    if progress_path.exists():
        progress_path.unlink()
    
    # Calculate statistics
    successful = sum(1 for r in receipts if r['success'])
    failed = len(receipts) - successful
    
    # Create output structure
    output = {
        'metadata': {
            'processed_at': datetime.now().isoformat(),
            'model_used': model_name,
            'total_images': len(receipts),
            'successful_extractions': successful,
            'failed_extractions': failed,
            'success_rate': round(successful / len(receipts) if receipts else 0, 3),
            'total_items_extracted': sum(len(r['items']) for r in receipts),
            'images_with_company_name': sum(1 for r in receipts if r['company_name']),
            'images_with_date': sum(1 for r in receipts if r['date']),
            'images_with_total': sum(1 for r in receipts if r['total']),
        },
        'receipts': receipts
    }
    
    # Log summary
    logger.info("\n" + "=" * 80)
    logger.info("PROCESSING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"\nResults Summary:")
    logger.info(f"  Total Images: {output['metadata']['total_images']}")
    logger.info(f"  Successful: {output['metadata']['successful_extractions']} ({output['metadata']['success_rate']*100:.1f}%)")
    logger.info(f"  Failed: {output['metadata']['failed_extractions']}")
    logger.info(f"  Total Items Extracted: {output['metadata']['total_items_extracted']}")
    logger.info(f"  Images with Company Name: {output['metadata']['images_with_company_name']}")
    logger.info(f"  Images with Date: {output['metadata']['images_with_date']}")
    logger.info(f"  Images with Total: {output['metadata']['images_with_total']}")
    
    return output


def export_to_json(data: Dict[str, Any], output_path: Path) -> None:
    """
    Export extraction results to JSON file.
    
    Args:
        data: Dictionary with extraction results
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nJSON output saved to: {output_path}")
    logger.info(f"File size: {output_path.stat().st_size:,} bytes")


def main():
    """Main entry point for batch receipt processor."""
    parser = argparse.ArgumentParser(
        description="Batch Receipt OCR Processor - Process all receipt images and export to JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/scripts/batch_receipt_processor.py
  python tools/scripts/batch_receipt_processor.py --output my_receipts.json
  python tools/scripts/batch_receipt_processor.py --model tesseract --verbose
        """
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='receipt_extractions.json',
        help='Output JSON file path (default: receipt_extractions.json)'
    )
    parser.add_argument(
        '--model', '-m',
        type=str,
        default='tesseract',
        choices=['tesseract', 'easyocr', 'paddleocr'],
        help='OCR model to use (default: tesseract)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    project_root = PROJECT_ROOT
    output_path = project_root / args.output
    
    try:
        # Process all receipts
        results = process_all_receipts(
            project_root=project_root,
            model_name=args.model,
            verbose=args.verbose
        )
        
        # Export to JSON
        export_to_json(results, output_path)
        
        # Final status
        logger.info("\n" + "=" * 80)
        if results['metadata']['failed_extractions'] == 0:
            logger.info("✓ ALL RECEIPTS PROCESSED SUCCESSFULLY!")
        elif results['metadata']['successful_extractions'] > 0:
            logger.info(f"⚠ PROCESSING COMPLETED WITH {results['metadata']['failed_extractions']} FAILURES")
        else:
            logger.info("✗ ALL RECEIPTS FAILED TO PROCESS")
        logger.info("=" * 80 + "\n")
        
        return 0 if results['metadata']['failed_extractions'] == 0 else 1
        
    except Exception as e:
        logger.error(f"\n✗ FATAL ERROR: {e}")
        if args.verbose:
            logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
