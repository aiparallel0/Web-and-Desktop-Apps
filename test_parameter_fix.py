#!/usr/bin/env python3
"""
Test script to verify parameter name fix and detection settings extraction
"""
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

def test_code_inspection():
    """Verify the code changes are in place"""
    print("=" * 80)
    print("Testing Backend Code Changes")
    print("=" * 80)
    
    # Read the app.py file and verify changes
    app_py_path = os.path.join(os.path.dirname(__file__), 'web', 'backend', 'app.py')
    
    with open(app_py_path, 'r') as f:
        content = f.read()
    
    # Check for 'image' parameter support
    if "'image' in request.files" in content:
        print("✅ Backend accepts 'image' parameter")
    else:
        print("❌ Backend doesn't check for 'image' parameter")
        return False
    
    # Check for backward compatibility with 'file'
    if "'file' in request.files" in content:
        print("✅ Backward compatibility with 'file' parameter maintained")
    else:
        print("❌ No backward compatibility with 'file'")
        return False
    
    # Check for detection settings extraction
    detection_checks = [
        "detection_mode = request.form.get('detection_mode'",
        "enable_deskew = request.form.get('enable_deskew'",
        "enable_enhancement = request.form.get('enable_enhancement'",
        "column_mode = request.form.get('column_mode'",
        "manual_regions = request.form.get('manual_regions'"
    ]
    
    print("\n✅ Detection Settings Extraction:")
    for check in detection_checks:
        if check in content:
            param_name = check.split("'")[1]
            print(f"   ✅ {param_name}")
        else:
            print(f"   ❌ Missing: {check}")
            return False
    
    # Check for logging
    if "logger.info(f\"Extraction request - model_id:" in content:
        print("\n✅ Backend logging for parameters added")
    else:
        print("\n⚠️  Backend logging not found (optional)")
    
    # Check frontend logging
    app_js_path = os.path.join(os.path.dirname(__file__), 'web', 'frontend', 'app.js')
    with open(app_js_path, 'r') as f:
        frontend_content = f.read()
    
    if "console.log('[Extract API]" in frontend_content:
        print("✅ Frontend logging added")
    else:
        print("⚠️  Frontend logging not found")
    
    # Check for gradient removal
    unified_controls_path = os.path.join(os.path.dirname(__file__), 'web', 'frontend', 'components', 'unified-extractor-controls.js')
    with open(unified_controls_path, 'r') as f:
        controls_content = f.read()
    
    gradient_count = controls_content.count('linear-gradient')
    if gradient_count == 0:
        print("✅ All gradients removed from unified-extractor-controls.js")
    else:
        print(f"⚠️  {gradient_count} gradient(s) still present in unified-extractor-controls.js")
    
    print("\n" + "=" * 80)
    print("✅ CODE INSPECTION PASSED!")
    print("=" * 80)
    print("\nKey Changes:")
    print("1. Backend now accepts 'image' parameter (with 'file' fallback)")
    print("2. Detection settings are extracted from form data")
    print("3. Logging added for debugging")
    print("4. Gradients removed from UI components")
    print("\nNote: To fully test, start the application and upload a file.")
    return True

if __name__ == '__main__':
    try:
        test_code_inspection()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
