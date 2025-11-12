#!/usr/bin/env python3
"""
Diagnostic script to identify issues with DONUT setup
"""

import sys
import subprocess

def check_package(package_name, import_name=None):
    """Check if a package is installed and importable"""
    if import_name is None:
        import_name = package_name

    print(f"\nChecking {package_name}...")

    # Check if installed via pip
    result = subprocess.run(
        ["pip3", "show", package_name],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"  ✗ {package_name} is NOT installed via pip")
        print(f"  Install with: pip3 install {package_name}")
        return False
    else:
        # Extract version
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                version = line.split(':', 1)[1].strip()
                print(f"  ✓ {package_name} {version} is installed")
                break

    # Try to import
    try:
        if import_name == 'torch':
            import torch
            print(f"  ✓ PyTorch {torch.__version__} imported successfully")
            print(f"  Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
        elif import_name == 'transformers':
            import transformers
            print(f"  ✓ Transformers {transformers.__version__} imported successfully")
        elif import_name == 'gradio':
            import gradio
            print(f"  ✓ Gradio {gradio.__version__} imported successfully")
        elif import_name == 'PIL':
            from PIL import Image
            print(f"  ✓ Pillow imported successfully")
        elif import_name == 'sentencepiece':
            import sentencepiece
            print(f"  ✓ Sentencepiece imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import {import_name}: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error importing {import_name}: {e}")
        return False

def test_model_loading():
    """Test if we can load the DONUT model"""
    print("\n" + "="*60)
    print("Testing DONUT Model Loading")
    print("="*60)

    try:
        from transformers import DonutProcessor, VisionEncoderDecoderModel
        import torch

        model_name = "naver-clova-ix/donut-base-finetuned-cord-v2"
        print(f"\nAttempting to load model: {model_name}")
        print("Note: This will download ~1.5GB on first run")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Device: {device}")

        print("\nLoading processor...")
        processor = DonutProcessor.from_pretrained(model_name)
        print("✓ Processor loaded")

        print("\nLoading model (this may take a while)...")
        model = VisionEncoderDecoderModel.from_pretrained(
            model_name,
            device_map=None,
            low_cpu_mem_usage=False,
            torch_dtype=torch.float32
        )
        print("✓ Model loaded")

        print(f"\nMoving model to {device}...")
        model = model.to(device)
        model.eval()
        print(f"✓ Model successfully moved to {device}")

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\nYou can now run: python3 donut_minimal.py")
        return True

    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        print("\nMissing dependencies. Install with:")
        print("  pip3 install torch transformers pillow gradio sentencepiece")
        return False
    except Exception as e:
        print(f"\n✗ Error loading model: {e}")
        print("\nPossible issues:")
        print("1. Network connection (model download failed)")
        print("2. Insufficient disk space")
        print("3. HuggingFace hub connectivity")
        print("\nTry:")
        print("  - Clear cache: rm -rf ~/.cache/huggingface/")
        print("  - Check internet connection")
        print("  - Ensure >2GB free disk space")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print("DONUT Web Application - Diagnostic Script")
    print("="*60)
    print(f"Python: {sys.version.split()[0]}")

    # Check all required packages
    packages = [
        ("torch", "torch"),
        ("transformers", "transformers"),
        ("pillow", "PIL"),
        ("gradio", "gradio"),
        ("sentencepiece", "sentencepiece"),
    ]

    all_installed = True
    for pkg_name, import_name in packages:
        if not check_package(pkg_name, import_name):
            all_installed = False

    if not all_installed:
        print("\n" + "="*60)
        print("✗ MISSING DEPENDENCIES")
        print("="*60)
        print("\nInstall all dependencies with:")
        print("  pip3 install -r requirements.txt")
        print("\nOr install individually:")
        print("  pip3 install torch transformers pillow gradio sentencepiece")
        return 1

    # If all packages are installed, test model loading
    print("\n" + "="*60)
    print("All dependencies installed! Testing model loading...")
    print("="*60)

    if test_model_loading():
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
