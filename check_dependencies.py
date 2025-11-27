#!/usr/bin/env python3
"""
Dependency checker and auto-installer for Receipt Extractor
Checks if required packages are installed and offers to install them
"""
import sys
import subprocess
import importlib.util
import os

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name

    spec = importlib.util.find_spec(import_name)
    return spec is not None

def install_package(package_name):
    """Install a package using pip"""
    try:
        print(f"  Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def check_and_install():
    """Check and install required dependencies"""
    print("=" * 60)
    print("Receipt Extractor - Dependency Checker")
    print("=" * 60)

    # Core dependencies
    core_deps = [
        ("flask", "Flask"),
        ("flask_cors", "flask-cors"),
        ("werkzeug", "Werkzeug"),
        ("PIL", "Pillow"),
        ("cv2", "opencv-python"),
        ("numpy", "numpy"),
        ("psutil", "psutil"),
        ("requests", "requests"),
    ]

    # OCR engines
    ocr_deps = [
        ("easyocr", "easyocr"),
        ("paddleocr", "paddleocr"),
        ("paddlepaddle", "paddlepaddle"),
        ("pytesseract", "pytesseract"),
    ]

    # AI models (optional)
    ai_deps = [
        ("torch", "torch"),
        ("transformers", "transformers"),
        ("accelerate", "accelerate"),
        ("sentencepiece", "sentencepiece"),
    ]

    missing_core = []
    missing_ocr = []
    missing_ai = []

    print("\n1. Checking CORE dependencies...")
    for import_name, package_name in core_deps:
        if check_package(import_name):
            print(f"  [OK] {package_name}")
        else:
            print(f"  [MISSING] {package_name}")
            missing_core.append(package_name)

    print("\n2. Checking OCR engines...")
    for import_name, package_name in ocr_deps:
        if check_package(import_name):
            print(f"  [OK] {package_name}")
        else:
            print(f"  [MISSING] {package_name}")
            missing_ocr.append(package_name)

    print("\n3. Checking AI models (optional)...")
    for import_name, package_name in ai_deps:
        if check_package(import_name):
            print(f"  [OK] {package_name}")
        else:
            print(f"  [MISSING] {package_name} (optional)")
            missing_ai.append(package_name)

    # Install missing packages
    if missing_core:
        print(f"\nWARNING: {len(missing_core)} core packages missing!")
        print("These packages are required for basic functionality.")
        response = input("Install missing core packages now? (y/n): ")
        if response.lower() == 'y':
            print("\nInstalling core packages...")
            for package in missing_core:
                if install_package(package):
                    print(f"  [OK] Installed {package}")
                else:
                    print(f"  [FAIL] Failed to install {package}")

    if missing_ocr:
        print(f"\nWARNING: {len(missing_ocr)} OCR packages missing.")
        print("At least one OCR engine is recommended (EasyOCR suggested).")
        if 'easyocr' in missing_ocr:
            response = input("Install EasyOCR (recommended)? (y/n): ")
            if response.lower() == 'y':
                if install_package('easyocr'):
                    print("  [OK] Installed easyocr")
                    missing_ocr.remove('easyocr')
                else:
                    print("  [FAIL] Failed to install easyocr")

        if 'paddleocr' in missing_ocr and 'paddlepaddle' in missing_ocr:
            response = input("Install PaddleOCR? (y/n): ")
            if response.lower() == 'y':
                if install_package('paddlepaddle'):
                    print("  [OK] Installed paddlepaddle")
                if install_package('paddleocr'):
                    print("  [OK] Installed paddleocr")

    if missing_ai:
        print(f"\nNOTE: {len(missing_ai)} AI packages missing (optional).")
        print("These are needed for Donut/Florence-2 models and finetuning.")
        print("Note: On Windows, this requires Visual Studio Build Tools.")
        response = input("Install AI packages? (y/n): ")
        if response.lower() == 'y':
            print("\nNOTE: This may take several minutes and requires 2-3 GB download.")
            response2 = input("Continue? (y/n): ")
            if response2.lower() == 'y':
                print("\nInstalling AI packages...")
                # Install PyTorch first
                if 'torch' in missing_ai:
                    print("  Installing torch (CPU version)...")
                    try:
                        subprocess.check_call([
                            sys.executable, "-m", "pip", "install",
                            "torch", "--index-url",
                            "https://download.pytorch.org/whl/cpu"
                        ])
                        print("  [OK] Installed torch")
                    except:
                        print("  [FAIL] Failed to install torch")

                # Install transformers
                if 'transformers' in missing_ai:
                    if install_package('transformers'):
                        print("  [OK] Installed transformers")

                # Install accelerate with specific version
                if 'accelerate' in missing_ai:
                    print("  Installing accelerate>=0.26.0...")
                    try:
                        subprocess.check_call([
                            sys.executable, "-m", "pip", "install",
                            "accelerate>=0.26.0"
                        ])
                        print("  [OK] Installed accelerate")
                    except:
                        print("  [FAIL] Failed to install accelerate")

                # Install sentencepiece (may fail on Windows)
                if 'sentencepiece' in missing_ai:
                    print("  Installing sentencepiece...")
                    try:
                        subprocess.check_call([
                            sys.executable, "-m", "pip", "install",
                            "sentencepiece", "--only-binary", ":all:"
                        ])
                        print("  [OK] Installed sentencepiece")
                    except:
                        print("  [FAIL] Failed to install sentencepiece")
                        print("     This may require Visual Studio Build Tools on Windows.")
                        print("     See WINDOWS_INSTALLATION.md for details.")

    # Final summary
    print("\n" + "=" * 60)
    print("Dependency Check Complete")
    print("=" * 60)

    # Recheck after installation
    core_ok = all(check_package(pkg[0]) for pkg in core_deps)
    ocr_ok = any(check_package(pkg[0]) for pkg in ocr_deps)

    if core_ok and ocr_ok:
        print("[SUCCESS] All required dependencies are installed!")
        print("\nYou can now run the application:")
        print("  cd web-app/backend")
        print("  python app.py")
        return True
    elif core_ok:
        print("[OK] Core dependencies installed")
        print("[WARNING] No OCR engines installed")
        print("\nPlease install at least one OCR engine:")
        print("  pip install easyocr")
        return False
    else:
        print("[ERROR] Some core dependencies are still missing")
        print("\nPlease install manually:")
        print("  pip install -r web-app/backend/requirements.txt")
        return False

if __name__ == "__main__":
    try:
        success = check_and_install()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
