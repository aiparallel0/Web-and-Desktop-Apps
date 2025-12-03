#!/usr/bin/env python3
"""
=============================================================================
PROCESS RECEIPT - Desktop App Receipt Extraction Script
=============================================================================

Module: desktop-app.process_receipt
Description: Command-line script for receipt data extraction from the desktop app
Compliance Version: 2.0.0

CIRCULAR EXCHANGE INTEGRATION:
This script integrates with the Circular Information Exchange Framework.
It uses the shared models package for receipt extraction and outputs
JSON results for the Electron main process.

Usage:
    python process_receipt.py <image_path> [model_id]

Arguments:
    image_path: Path to the receipt image file
    model_id:   Optional model identifier (default: uses system default)

Output:
    JSON object printed to stdout with extraction results

=============================================================================
"""

import sys
import os
import json
import logging

# Add the project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure logging to stderr (so it doesn't interfere with JSON output on stdout)
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
    
    PROJECT_CONFIG.register_module(ModuleRegistration(
        module_id="desktop.process_receipt",
        file_path=__file__,
        description="Desktop app CLI script for receipt extraction",
        dependencies=["shared.models.manager", "shared.circular_exchange"],
        exports=["main", "extract_receipt"]
    ))
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False


def extract_receipt(image_path: str, model_id: str = None) -> dict:
    """
    Extract receipt data from an image file.
    
    Args:
        image_path: Path to the receipt image
        model_id: Optional model identifier to use
        
    Returns:
        Dictionary with extraction results
    """
    try:
        from shared.models.manager import ModelManager
        
        # Initialize model manager
        manager = ModelManager(max_loaded_models=2)
        
        # Select model if specified
        if model_id:
            success = manager.select_model(model_id)
            if not success:
                # Try to find a similar model
                available = manager.get_available_models()
                model_ids = [m['id'] for m in available]
                if model_id not in model_ids:
                    # Use default model if specified model not found
                    logger.warning(f"Model {model_id} not found, using default")
                    model_id = manager.get_default_model()
                    manager.select_model(model_id)
        
        # Get processor and extract
        processor = manager.get_processor(model_id)
        result = processor.extract(image_path)
        
        # Convert result to dictionary
        if hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
        else:
            result_dict = {
                'success': result.success if hasattr(result, 'success') else False,
                'data': result.data if hasattr(result, 'data') else None,
                'error': result.error if hasattr(result, 'error') else None
            }
        
        # Format result for desktop app
        if result_dict.get('success') and result_dict.get('data'):
            data = result_dict['data']
            
            # Ensure data has expected structure for desktop app
            formatted_result = {
                'success': True,
                'data': {
                    'receipt': {
                        'store': {
                            'name': data.get('store', {}).get('name') or data.get('store_name'),
                            'address': data.get('store', {}).get('address') or data.get('store_address'),
                            'phone': data.get('store', {}).get('phone') or data.get('store_phone')
                        },
                        'date': data.get('date') or data.get('transaction_date'),
                        'time': data.get('time') or data.get('transaction_time'),
                        'items': data.get('items', []),
                        'totals': {
                            'subtotal': data.get('totals', {}).get('subtotal') or data.get('subtotal'),
                            'tax': data.get('totals', {}).get('tax') or data.get('tax'),
                            'total': data.get('totals', {}).get('total') or data.get('total')
                        },
                        'confidence': data.get('confidence_score') or data.get('confidence')
                    },
                    'model': data.get('model_used') or model_id or manager.get_current_model(),
                    'processing_time': data.get('processing_time', 0)
                }
            }
            return formatted_result
        else:
            return {
                'success': False,
                'error': result_dict.get('error', 'Extraction failed')
            }
            
    except ImportError as e:
        return {
            'success': False,
            'error': f"Missing dependencies: {str(e)}. Please install: pip install -r requirements.txt"
        }
    except FileNotFoundError as e:
        return {
            'success': False,
            'error': f"Image file not found: {image_path}"
        }
    except Exception as e:
        logger.error(f"Extraction error: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Main entry point for the script."""
    # Check arguments
    if len(sys.argv) < 2:
        result = {
            'success': False,
            'error': 'Usage: python process_receipt.py <image_path> [model_id]'
        }
        print(json.dumps(result))
        sys.exit(1)
    
    image_path = sys.argv[1]
    model_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Validate image path
    if not os.path.exists(image_path):
        result = {
            'success': False,
            'error': f"Image file not found: {image_path}"
        }
        print(json.dumps(result))
        sys.exit(1)
    
    # Check file extension
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    _, ext = os.path.splitext(image_path.lower())
    if ext not in valid_extensions:
        result = {
            'success': False,
            'error': f"Invalid file type '{ext}'. Supported: {', '.join(valid_extensions)}"
        }
        print(json.dumps(result))
        sys.exit(1)
    
    # Extract receipt data
    result = extract_receipt(image_path, model_id)
    
    # Output JSON result (main.js expects JSON output on stdout)
    print(json.dumps(result, indent=2, default=str))
    
    # Exit with appropriate code
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
