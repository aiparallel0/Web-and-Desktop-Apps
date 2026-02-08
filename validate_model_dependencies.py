#!/usr/bin/env python3
"""
Validation script to demonstrate model availability based on installed dependencies.

This script shows:
1. Current dependency status
2. Available models
3. Unavailable models with reasons
4. Installation instructions for missing dependencies
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    from shared.models.manager import ModelManager
    
    print("=" * 80)
    print("MODEL DEPENDENCY VALIDATION")
    print("=" * 80)
    
    # Initialize manager
    manager = ModelManager()
    
    # Check dependencies
    print("\n1. DEPENDENCY STATUS")
    print("-" * 80)
    deps = manager._check_dependencies()
    
    available_deps = []
    missing_deps = []
    
    for dep_name, dep_info in deps.items():
        if dep_info.get('available'):
            version = dep_info.get('version', 'unknown')
            print(f"  ✓ {dep_name:20s} - {version}")
            available_deps.append(dep_name)
        else:
            error = dep_info.get('error', 'Not installed')
            print(f"  ✗ {dep_name:20s} - {error}")
            missing_deps.append(dep_name)
    
    # Get models with availability check
    print("\n2. MODEL AVAILABILITY")
    print("-" * 80)
    models = manager.get_available_models(check_availability=True)
    
    available_models = [m for m in models if m.get('available')]
    unavailable_models = [m for m in models if not m.get('available')]
    
    print(f"  Total models configured: {len(models)}")
    print(f"  Available models: {len(available_models)}")
    print(f"  Unavailable models: {len(unavailable_models)}")
    
    if available_models:
        print("\n3. AVAILABLE MODELS (Ready to use)")
        print("-" * 80)
        for model in available_models:
            print(f"  ✓ {model['name']:40s} ({model['id']})")
            print(f"    Type: {model['type']}, Description: {model['description'][:60]}")
    
    if unavailable_models:
        print("\n4. UNAVAILABLE MODELS (Missing dependencies)")
        print("-" * 80)
        for model in unavailable_models:
            missing = model.get('missing_dependencies', [])
            print(f"  ✗ {model['name']:40s} ({model['id']})")
            print(f"    Missing: {', '.join(missing)}")
    
    # Installation instructions
    if missing_deps:
        print("\n5. INSTALLATION INSTRUCTIONS")
        print("-" * 80)
        print("  To enable all models, install missing dependencies:")
        print()
        
        # Group by installation method
        pip_packages = []
        system_packages = []
        
        dep_mapping = {
            'opencv': ('opencv-python-headless', None),
            'easyocr': ('easyocr', None),
            'paddleocr': ('paddleocr paddlepaddle', None),
            'torch': ('torch torchvision', None),
            'transformers': ('transformers accelerate sentencepiece', None),
            'craft': ('craft-text-detector', None),
            'pytesseract': ('pytesseract', 'tesseract-ocr (system package)')
        }
        
        for dep in missing_deps:
            if dep in dep_mapping:
                pip_pkg, sys_pkg = dep_mapping[dep]
                if pip_pkg:
                    pip_packages.append(pip_pkg)
                if sys_pkg:
                    system_packages.append(sys_pkg)
        
        if pip_packages:
            print("  Python packages:")
            all_pip = ' '.join(pip_packages)
            print(f"    pip install {all_pip}")
        
        if system_packages:
            print("\n  System packages (Debian/Ubuntu):")
            for pkg in system_packages:
                print(f"    sudo apt-get install {pkg}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if len(available_models) == 0:
        print("  ⚠️  NO MODELS AVAILABLE")
        print("  Install dependencies to enable text detection models.")
    elif len(available_models) == len(models):
        print("  ✅ ALL MODELS AVAILABLE")
        print("  All 8 text detection models are ready to use!")
    else:
        print(f"  ⚠️  PARTIAL AVAILABILITY: {len(available_models)}/{len(models)} models ready")
        print("  Some models are available, but install remaining dependencies for full functionality.")
    
    print("=" * 80)
    
    # Return exit code based on availability
    if len(available_models) == 0:
        return 1  # No models available
    elif len(available_models) < len(models):
        return 0  # Some models available (warning but success)
    else:
        return 0  # All models available

if __name__ == '__main__':
    sys.exit(main())
