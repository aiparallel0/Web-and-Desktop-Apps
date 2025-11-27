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
        print("\nRunning dependency checker...")
        try:
            subprocess.check_call([sys.executable, "check_dependencies.py"])
        except:
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
        print("\nRecommended: pip install easyocr")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return 1

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
