#!/usr/bin/env python3
"""
Test Extraction Script - Demonstrates Working Receipt Extraction

This script creates a test receipt image and extracts data from it,
proving that the extraction pipeline works end-to-end.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFont
from shared.models.ocr_processor import OCRProcessor

def create_test_receipt(filename='/tmp/test_receipt.jpg'):
    """Create a realistic test receipt image."""
    print("Creating test receipt image...")
    
    img = Image.new('RGB', (600, 500), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    except:
        font = None
    
    # Draw receipt content
    draw.text((50, 20), 'GROCERY STORE', fill='black', font=font)
    draw.text((50, 50), '123 Main Street', fill='black', font=font)
    draw.text((50, 70), 'Phone: (555) 123-4567', fill='black', font=font)
    draw.text((50, 100), 'Date: 01/15/2024', fill='black', font=font)
    draw.text((50, 120), 'Time: 14:30', fill='black', font=font)
    draw.text((50, 160), 'Milk                 3.99', fill='black', font=font)
    draw.text((50, 190), 'Bread                2.49', fill='black', font=font)
    draw.text((50, 220), 'Eggs                 4.99', fill='black', font=font)
    draw.text((50, 250), 'Cheese               5.99', fill='black', font=font)
    draw.text((50, 300), 'Subtotal:           17.46', fill='black', font=font)
    draw.text((50, 330), 'Tax:                 1.40', fill='black', font=font)
    draw.text((50, 360), 'TOTAL:              18.86', fill='black', font=font)
    draw.text((50, 400), 'Thank you for shopping!', fill='black', font=font)
    
    img.save(filename, quality=95)
    print(f"✓ Test receipt saved to: {filename}")
    return filename

def test_extraction():
    """Test receipt extraction."""
    print("\n" + "="*60)
    print("TESTING RECEIPT EXTRACTION")
    print("="*60)
    
    # Create test image
    image_path = create_test_receipt()
    
    # Initialize processor
    print("\nInitializing OCR processor...")
    model_config = {
        'id': 'ocr_tesseract',
        'name': 'Tesseract OCR',
        'type': 'ocr'
    }
    processor = OCRProcessor(model_config)
    print("✓ Processor initialized")
    
    # Extract
    print("\nExtracting receipt data...")
    result = processor.extract(image_path)
    
    # Display results
    print("\n" + "="*60)
    print("EXTRACTION RESULTS")
    print("="*60)
    
    print(f"\nSuccess: {result.success}")
    
    if result.success and result.data:
        data = result.data
        
        print("\n--- Store Information ---")
        print(f"Store: {data.store_name or 'N/A'}")
        print(f"Address: {data.store_address or 'N/A'}")
        print(f"Phone: {data.store_phone or 'N/A'}")
        
        print("\n--- Transaction Details ---")
        print(f"Date: {data.transaction_date or 'N/A'}")
        print(f"Time: {data.transaction_time or 'N/A'}")
        
        print("\n--- Financial Summary ---")
        print(f"Subtotal: ${data.subtotal or 0:.2f}")
        print(f"Tax: ${data.tax or 0:.2f}")
        print(f"Total: ${data.total or 0:.2f}")
        
        print("\n--- Line Items ---")
        if data.items:
            print(f"Found {len(data.items)} items:")
            for i, item in enumerate(data.items, 1):
                print(f"  {i}. {item.name}: ${item.total_price}")
        else:
            print("No items detected")
        
        print("\n--- Processing Metadata ---")
        print(f"Model: {data.model_used}")
        print(f"Processing time: {data.processing_time:.2f}s")
        print(f"Confidence: {data.confidence_score:.2%}")
        
        print("\n" + "="*60)
        print("✓ EXTRACTION SUCCESSFUL!")
        print("="*60)
        return True
    else:
        print(f"\n✗ EXTRACTION FAILED")
        print(f"Error: {result.error}")
        return False

if __name__ == '__main__':
    try:
        success = test_extraction()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
