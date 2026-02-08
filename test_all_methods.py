#!/usr/bin/env python3
"""
Comprehensive Test: All Extraction Methods and Settings

Tests each extraction method and detection setting to verify
frontend-backend compatibility.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFont
from shared.models.manager import ModelManager
import json

def create_test_receipt(filename='/tmp/test_comprehensive.jpg'):
    """Create test receipt image."""
    img = Image.new('RGB', (600, 500), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    except:
        font = None
    
    draw.text((50, 20), 'TEST STORE', fill='black', font=font)
    draw.text((50, 50), 'Date: 01/15/2024', fill='black', font=font)
    draw.text((50, 90), 'Item 1     10.00', fill='black', font=font)
    draw.text((50, 120), 'Item 2     20.00', fill='black', font=font)
    draw.text((50, 160), 'Total:     30.00', fill='black', font=font)
    
    img.save(filename, quality=95)
    return filename

def test_extraction_method(model_id, model_name, image_path):
    """Test a single extraction method."""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name} ({model_id})")
    print('='*60)
    
    try:
        manager = ModelManager()
        processor = manager.get_processor(model_id)
        print(f"✓ Processor loaded: {type(processor).__name__}")
        
        result = processor.extract(image_path)
        
        if result.success and result.data:
            print(f"✓ SUCCESS")
            print(f"  Store: {result.data.store_name or 'N/A'}")
            print(f"  Date: {result.data.transaction_date or 'N/A'}")
            print(f"  Total: ${result.data.total or 0}")
            print(f"  Items: {len(result.data.items) if result.data.items else 0}")
            return True, "Working"
        else:
            print(f"✗ FAILED: {result.error}")
            return False, result.error
            
    except ImportError as e:
        error = f"Missing dependency: {str(e)}"
        print(f"✗ IMPORT ERROR: {error}")
        return False, error
    except Exception as e:
        error = str(e)
        print(f"✗ ERROR: {error}")
        return False, error

def test_all_methods():
    """Test all extraction methods."""
    print("\n" + "="*60)
    print("COMPREHENSIVE EXTRACTION METHOD TEST")
    print("="*60)
    
    # Create test image
    image_path = create_test_receipt()
    print(f"\n✓ Test image created: {image_path}")
    
    # Get available models
    manager = ModelManager()
    models = manager.models_config.get('available_models', {})
    
    results = {}
    
    for model_id, config in models.items():
        model_name = config.get('name', model_id)
        success, message = test_extraction_method(model_id, model_name, image_path)
        results[model_id] = {
            'name': model_name,
            'success': success,
            'message': message
        }
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    working = []
    not_working = []
    
    for model_id, result in results.items():
        status = "✓" if result['success'] else "✗"
        print(f"{status} {result['name']}: {result['message']}")
        
        if result['success']:
            working.append(model_id)
        else:
            not_working.append(model_id)
    
    print(f"\nWorking: {len(working)}/{len(results)}")
    print(f"Not working: {len(not_working)}/{len(results)}")
    
    # Save results to JSON
    with open('/tmp/extraction_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to /tmp/extraction_test_results.json")
    
    return working, not_working

if __name__ == '__main__':
    try:
        working, not_working = test_all_methods()
        sys.exit(0 if len(working) > 0 else 1)
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
