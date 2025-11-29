#!/usr/bin/env python3
"""
Dependency checker and auto-installer for Receipt Extractor
Checks if required packages are installed and offers to install them
"""
import sys
import subprocess
import importlib.util
import os
import argparse

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name

    spec = importlib.util.find_spec(import_name)
    return spec is not None

def install_package(package_name):
    """Install a package using pip"""
    try:
        print(f"\n  Installing {package_name}...")
        print(f"  (This may take a moment...)")
        sys.stdout.flush()

        # Special handling for paddlepaddle - ignore system PyYAML to avoid conflicts
        if package_name == 'paddlepaddle':
            print(f"  Note: Using --ignore-installed to avoid system package conflicts")
            sys.stdout.flush()
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--ignore-installed", "PyYAML", "-q"],
                timeout=60
            )
            if result.returncode != 0:
                print(f"  [WARNING] PyYAML installation had issues, continuing anyway...")

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package_name, "-q"],
                timeout=180
            )
        else:
            # For other packages, use standard installation without capturing output
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package_name, "-q"],
                timeout=180
            )

        sys.stdout.flush()
        if result.returncode == 0:
            print(f"  [OK] Successfully installed {package_name}")
            sys.stdout.flush()
            return True
        else:
            print(f"  [FAIL] Failed to install {package_name} (exit code: {result.returncode})")
            sys.stdout.flush()
            return False
    except subprocess.TimeoutExpired:
        print(f"  [FAIL] Installation timed out after 3 minutes")
        sys.stdout.flush()
        return False
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        sys.stdout.flush()
        return False

def check_and_install(auto_install=False, install_ai=False, silent=False):
    """Check and install required dependencies

    Args:
        auto_install: Automatically install missing packages without prompting
        install_ai: Include AI packages in auto-installation
        silent: Suppress non-critical output
    """
    if not silent:
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

    if not silent:
        print("\n1. Checking CORE dependencies...")
    for import_name, package_name in core_deps:
        if check_package(import_name):
            if not silent:
                print(f"  [OK] {package_name}")
        else:
            if not silent:
                print(f"  [MISSING] {package_name}")
            missing_core.append(package_name)

    if not silent:
        print("\n2. Checking OCR engines...")
    for import_name, package_name in ocr_deps:
        if check_package(import_name):
            if not silent:
                print(f"  [OK] {package_name}")
        else:
            if not silent:
                print(f"  [MISSING] {package_name}")
            missing_ocr.append(package_name)

    if not silent:
        print("\n3. Checking AI models (optional)...")
    for import_name, package_name in ai_deps:
        if check_package(import_name):
            if not silent:
                print(f"  [OK] {package_name}")
        else:
            if not silent:
                print(f"  [MISSING] {package_name} (optional)")
            missing_ai.append(package_name)

    # Install missing packages
    if missing_core:
        if not silent:
            print(f"\nWARNING: {len(missing_core)} core packages missing!")
            print("These packages are required for basic functionality.")

        if auto_install:
            response = 'y'
        else:
            response = input("Install missing core packages now? (y/n): ")

        if response.lower() == 'y':
            if not silent:
                print("\nInstalling core packages...")
            for package in missing_core:
                if install_package(package):
                    if not silent:
                        print(f"  [OK] Installed {package}")
                else:
                    if not silent:
                        print(f"  [FAIL] Failed to install {package}")

    if missing_ocr:
        if not silent:
            print(f"\nWARNING: {len(missing_ocr)} OCR packages missing.")
            print("At least one OCR engine is recommended (EasyOCR suggested).")

        if 'easyocr' in missing_ocr:
            if auto_install:
                response = 'y'
            else:
                response = input("Install EasyOCR (recommended)? (y/n): ")
            if response.lower() == 'y':
                if install_package('easyocr'):
                    if not silent:
                        print("  [OK] Installed easyocr")
                    missing_ocr.remove('easyocr')
                else:
                    if not silent:
                        print("  [FAIL] Failed to install easyocr")

        # Handle PaddleOCR - install both if both missing
        if 'paddleocr' in missing_ocr and 'paddlepaddle' in missing_ocr:
            if auto_install:
                response = 'n'  # Skip PaddleOCR in auto mode (EasyOCR is preferred)
            else:
                response = input("Install PaddleOCR and PaddlePaddle? (y/n): ")
            if response.lower() == 'y':
                if install_package('paddlepaddle'):
                    if not silent:
                        print("  [OK] Installed paddlepaddle")
                    missing_ocr.remove('paddlepaddle')
                if install_package('paddleocr'):
                    if not silent:
                        print("  [OK] Installed paddleocr")
                    missing_ocr.remove('paddleocr')
        # Handle case where only paddlepaddle is missing (paddleocr already installed)
        elif 'paddlepaddle' in missing_ocr and 'paddleocr' not in missing_ocr:
            if auto_install:
                response = 'n'
            else:
                response = input("Install PaddlePaddle (required for PaddleOCR)? (y/n): ")
            if response.lower() == 'y':
                if install_package('paddlepaddle'):
                    if not silent:
                        print("  [OK] Installed paddlepaddle")
                    missing_ocr.remove('paddlepaddle')
                else:
                    if not silent:
                        print("  [FAIL] Failed to install paddlepaddle")

    if missing_ai:
        if not silent:
            print(f"\nNOTE: {len(missing_ai)} AI packages missing (optional).")
            print("These are needed for Donut/Florence-2 models and finetuning.")
            print("Note: On Windows, this requires Visual Studio Build Tools.")

        if auto_install and install_ai:
            response = 'y'
            response2 = 'y'
        elif auto_install:
            response = 'n'
            response2 = 'n'
        else:
            response = input("Install AI packages? (y/n): ")
            if response.lower() == 'y':
                print("\nNOTE: This may take several minutes and requires 2-3 GB download.")
                response2 = input("Continue? (y/n): ")
            else:
                response2 = 'n'

        if response.lower() == 'y' and response2.lower() == 'y':
                print("\nInstalling AI packages...")
                sys.stdout.flush()

                # Install PyTorch first
                if 'torch' in missing_ai:
                    print("  Installing torch (CPU version)...")
                    print("  (This is a large download, may take 5-10 minutes...)")
                    sys.stdout.flush()
                    try:
                        result = subprocess.run([
                            sys.executable, "-m", "pip", "install",
                            "torch", "--index-url",
                            "https://download.pytorch.org/whl/cpu", "-q"
                        ], timeout=600)
                        if result.returncode == 0:
                            print("  [OK] Installed torch")
                        else:
                            print("  [FAIL] Failed to install torch")
                        sys.stdout.flush()
                    except subprocess.TimeoutExpired:
                        print("  [FAIL] torch installation timed out")
                        sys.stdout.flush()
                    except Exception as e:
                        print(f"  [FAIL] Failed to install torch: {e}")
                        sys.stdout.flush()

                # Install transformers
                if 'transformers' in missing_ai:
                    if install_package('transformers'):
                        print("  [OK] Installed transformers")

                # Install accelerate with specific version
                if 'accelerate' in missing_ai:
                    print("  Installing accelerate>=0.26.0...")
                    sys.stdout.flush()
                    try:
                        result = subprocess.run([
                            sys.executable, "-m", "pip", "install",
                            "accelerate>=0.26.0", "-q"
                        ], timeout=180)
                        if result.returncode == 0:
                            print("  [OK] Installed accelerate")
                        else:
                            print("  [FAIL] Failed to install accelerate")
                        sys.stdout.flush()
                    except subprocess.TimeoutExpired:
                        print("  [FAIL] accelerate installation timed out")
                        sys.stdout.flush()
                    except Exception as e:
                        print(f"  [FAIL] Failed to install accelerate: {e}")
                        sys.stdout.flush()

                # Install sentencepiece (may fail on Windows)
                if 'sentencepiece' in missing_ai:
                    print("  Installing sentencepiece...")
                    sys.stdout.flush()
                    try:
                        result = subprocess.run([
                            sys.executable, "-m", "pip", "install",
                            "sentencepiece", "--only-binary", ":all:", "-q"
                        ], timeout=180)
                        if result.returncode == 0:
                            print("  [OK] Installed sentencepiece")
                        else:
                            print("  [FAIL] Failed to install sentencepiece")
                            print("     This may require Visual Studio Build Tools on Windows.")
                            print("     See WINDOWS_INSTALLATION.md for details.")
                        sys.stdout.flush()
                    except subprocess.TimeoutExpired:
                        print("  [FAIL] sentencepiece installation timed out")
                        sys.stdout.flush()
                    except Exception as e:
                        print(f"  [FAIL] Failed to install sentencepiece: {e}")
                        print("     This may require Visual Studio Build Tools on Windows.")
                        print("     See WINDOWS_INSTALLATION.md for details.")
                        sys.stdout.flush()

    # Final summary
    if not silent:
        print("\n" + "=" * 60)
        print("Dependency Check Complete")
        print("=" * 60)
        sys.stdout.flush()

    # Recheck after installation
    if not silent:
        print("\nRechecking installed packages...")
        sys.stdout.flush()
    core_ok = all(check_package(pkg[0]) for pkg in core_deps)
    ocr_ok = any(check_package(pkg[0]) for pkg in ocr_deps)

    if core_ok and ocr_ok:
        if not silent:
            print("\n[SUCCESS] All required dependencies are installed!")
            print("\nYou can now run the application:")
            print("  cd web-app/backend")
            print("  python app.py")
            print("\n" + "=" * 60)
            print("Setup complete - you can close this window")
            print("=" * 60)
            sys.stdout.flush()
        return True
    elif core_ok:
        if not silent:
            print("\n[OK] Core dependencies installed")
            print("[WARNING] No OCR engines installed")
            print("\nPlease install at least one OCR engine:")
            print("  pip install easyocr")
            print("\n" + "=" * 60)
            print("Setup incomplete - please install OCR engines")
            print("=" * 60)
            sys.stdout.flush()
        return False
    else:
        if not silent:
            print("\n[ERROR] Some core dependencies are still missing")
            print("\nPlease install manually:")
            print("  pip install -r web-app/backend/requirements.txt")
            print("\n" + "=" * 60)
            print("Setup failed - please install dependencies manually")
            print("=" * 60)
            sys.stdout.flush()
        return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Check and install Receipt Extractor dependencies')
    parser.add_argument('--auto-install', action='store_true',
                        help='Automatically install missing core and OCR packages without prompting')
    parser.add_argument('--install-ai', action='store_true',
                        help='Also install AI packages (only with --auto-install)')
    parser.add_argument('--silent', action='store_true',
                        help='Suppress non-critical output')
    args = parser.parse_args()

    try:
        success = check_and_install(
            auto_install=args.auto_install,
            install_ai=args.install_ai,
            silent=args.silent
        )
        sys.stdout.flush()
        if not args.silent:
            print("\nDependency check script finished.")
        sys.stdout.flush()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Installation cancelled by user.")
        print("=" * 60)
        sys.stdout.flush()
        sys.exit(1)
    except Exception as e:
        print("\n\n" + "=" * 60)
        print(f"ERROR: Dependency check failed")
        print("=" * 60)
        print(f"Error details: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        sys.stdout.flush()
        sys.exit(1)
#!/usr/bin/env python3
"""
Startup script for Receipt Extractor
Checks dependencies and starts the backend server
"""
import sys
import os
import subprocess
from pathlib import Path

def check_basic_imports():
    """Quick check for critical imports"""
    try:
        import flask
        import PIL
        import numpy
        return True
    except ImportError:
        return False

def main():
    print("=" * 60)
    print("Starting Receipt Extractor Pro")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path("web-app/backend/app.py").exists():
        print("Error: Please run this script from the project root directory")
        print("Current directory:", os.getcwd())
        return 1

    # Quick dependency check
    if not check_basic_imports():
        print("\n⚠️  Core dependencies not found!")
        print("\nRunning dependency checker with auto-install...")
        try:
            # Run with --auto-install flag to avoid blocking on user input
            subprocess.check_call([sys.executable, "check_dependencies.py", "--auto-install"])
        except subprocess.CalledProcessError:
            print("\n⚠️  Automatic installation failed.")
            print("\nPlease install dependencies manually:")
            print("  pip install -r web-app/backend/requirements.txt")
            print("\nOr run the dependency checker interactively:")
            print("  python3 check_dependencies.py")
            return 1
        except Exception as e:
            print(f"\n⚠️  Error running dependency checker: {e}")
            print("\nPlease install dependencies manually:")
            print("  pip install -r web-app/backend/requirements.txt")
            return 1

    # Check for at least one OCR engine
    has_ocr = False
    try:
        import easyocr
        print("[OK] EasyOCR available")
        has_ocr = True
    except ImportError:
        pass

    try:
        import paddleocr
        print("[OK] PaddleOCR available")
        has_ocr = True
    except ImportError:
        pass

    try:
        import pytesseract
        print("[OK] Tesseract available")
        has_ocr = True
    except ImportError:
        pass

    if not has_ocr:
        print("\n[WARNING] No OCR engines installed!")
        print("The application needs at least one OCR engine to work.")
        print("\nAttempting to install EasyOCR...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "easyocr", "-q"])
            print("[OK] EasyOCR installed successfully")
        except:
            print("\n[FAILED] Could not install EasyOCR automatically.")
            print("\nRecommended: pip install easyocr")
            print("\nYou can still start the server, but extraction will not work without an OCR engine.")
            import sys
            # Check if running interactively
            if sys.stdin.isatty():
                response = input("\nContinue anyway? (y/n): ")
                if response.lower() != 'y':
                    return 1
            else:
                print("Running in non-interactive mode, continuing anyway...")

    # Start the backend
    print("\n" + "=" * 60)
    print("Starting Backend Server...")
    print("=" * 60)
    print("\nBackend will be available at: http://localhost:5000")
    print("Frontend: Open web-app/frontend/index.html in your browser")
    print("\nPress Ctrl+C to stop the server\n")

    try:
        os.chdir("web-app/backend")
        subprocess.check_call([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
        return 0
    except Exception as e:
        print(f"\n\nError starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
