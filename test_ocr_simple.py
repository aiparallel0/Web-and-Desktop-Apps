#!/usr/bin/env python3
"""
Simple test script to verify OCR models work
"""
import sys
import os

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from models.model_manager import ModelManager

def test_model(model_id, image_path):
    """Test a single model"""
    print(f"\n{'='*60}")
    print(f"TESTING: {model_id}")
    print(f"{'='*60}")
    
    try:
        manager = ModelManager()
        manager.select_model(model_id)
        processor = manager.get_processor(model_id)
        
        print(f"Processor loaded: {processor.__class__.__name__}")
        print(f"Extracting from: {image_path}")
        
        result = processor.extract(image_path)
        
        if result.success:
            print(f"✅ SUCCESS!")
            print(f"Store: {result.data.store_name}")
            print(f"Total: ${result.data.total}")
            print(f"Items: {len(result.data.items)}")
            print(f"Time: {result.data.processing_time:.2f}s")
            return True
        else:
            print(f"❌ FAILED: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_ocr_simple.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"ERROR: Image not found: {image_path}")
        sys.exit(1)
    
    print(f"Testing OCR models with: {image_path}")
    
    models = ['ocr_tesseract', 'ocr_easyocr', 'ocr_paddle']
    results = {}
    
    for model_id in models:
        results[model_id] = test_model(model_id, image_path)
    
    print(f"\n{'='*60}")
    print("RESULTS SUMMARY:")
    print(f"{'='*60}")
    for model_id, success in results.items():
        status = "✅ WORKS" if success else "❌ FAILED"
        print(f"{model_id}: {status}")
    
    working = [m for m, s in results.items() if s]
    print(f"\nWorking models: {len(working)}/{len(models)}")
    
    if working:
        print(f"\n🎉 AT LEAST ONE MODEL WORKS!")
        sys.exit(0)
    else:
        print(f"\n❌ NO MODELS WORKING!")
        sys.exit(1)
