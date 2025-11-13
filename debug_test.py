#!/usr/bin/env python3
"""
Simple test script to debug SROIE Donut extraction
"""
import os
import sys
import logging

# Add shared modules to path
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from shared.models.model_manager import ModelManager

def test_extraction(image_path: str):
    """Test extraction on a single image"""
    print(f"\nTesting SROIE Donut extraction on: {image_path}")
    print("=" * 60)

    try:
        # Initialize model manager
        manager = ModelManager()

        # Select SROIE model
        manager.select_model('donut_sroie')

        # Get processor
        processor = manager.get_processor('donut_sroie')

        # Extract data
        print("\nRunning extraction...")
        result = processor.extract(image_path)

        # Print results
        print("\nExtraction Result:")
        print("=" * 60)
        if result.success:
            data = result.data
            print(f"Model: {data.model_used}")
            print(f"Processing time: {data.processing_time:.2f}s")
            print(f"Confidence: {data.confidence_score}")
            print(f"\nStore Name: {data.store_name}")
            print(f"Store Address: {data.store_address}")
            print(f"Date: {data.transaction_date}")
            print(f"Total: {data.total}")
            print(f"Items: {len(data.items)}")

            if data.extraction_notes:
                print(f"\nNotes: {', '.join(data.extraction_notes)}")

            # Print full JSON
            print("\nFull JSON output:")
            print("-" * 60)
            import json
            print(json.dumps(data.to_dict(), indent=2))
        else:
            print(f"ERROR: {result.error}")
            if result.warnings:
                print(f"Warnings: {', '.join(result.warnings)}")

    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else "1.jpg"
    test_extraction(image_path)
