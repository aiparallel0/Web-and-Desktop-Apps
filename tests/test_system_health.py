"""
System health and diagnostic tests
Verifies all dependencies are installed and working
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_python_version():
    """Verify Python version is 3.8+"""
    version = sys.version_info
    assert version.major == 3 and version.minor >= 8, \
        f"Python 3.8+ required, found {version.major}.{version.minor}"
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")


def test_core_dependencies():
    """Test core dependencies are installed"""
    required = {
        'PIL': 'Pillow',
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'flask': 'Flask',
        'transformers': 'transformers (optional)',
        'torch': 'torch (optional)'
    }

    for module, name in required.items():
        try:
            __import__(module)
            print(f"✓ {name} installed")
        except ImportError:
            if 'optional' in name:
                print(f"⚠ {name} not installed (optional)")
            else:
                print(f"✗ {name} NOT installed (required)")
                raise


def test_tesseract_installation():
    """Test if Tesseract OCR is installed"""
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract OCR version: {version}")
        return True
    except Exception as e:
        print(f"⚠ Tesseract OCR not available: {e}")
        print("  Install from: https://github.com/tesseract-ocr/tesseract")
        return False


def test_config_files():
    """Test that config files exist and are valid"""
    config_path = Path(__file__).parent.parent / 'shared' / 'config' / 'models_config.json'
    assert config_path.exists(), f"Config file not found: {config_path}"

    import json
    with open(config_path) as f:
        config = json.load(f)

    assert 'available_models' in config
    assert 'default_model' in config
    print(f"✓ Configuration file valid ({len(config['available_models'])} models)")


def test_model_manager_initialization():
    """Test ModelManager can be initialized"""
    from shared.models.model_manager import ModelManager

    try:
        manager = ModelManager()
        models = manager.get_available_models()
        print(f"✓ ModelManager initialized ({len(models)} models available)")
        return True
    except Exception as e:
        print(f"✗ ModelManager initialization failed: {e}")
        return False


def test_memory_available():
    """Check available system memory"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        total_gb = memory.total / (1024**3)

        print(f"✓ Memory: {available_gb:.1f}GB available / {total_gb:.1f}GB total")

        if available_gb < 2:
            print("  ⚠ Warning: Low memory. 4GB+ recommended for model loading")
    except ImportError:
        print("  ℹ psutil not installed - cannot check memory")


def test_disk_space():
    """Check available disk space"""
    try:
        import psutil
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024**3)

        print(f"✓ Disk space: {free_gb:.1f}GB free")

        if free_gb < 5:
            print("  ⚠ Warning: Low disk space. 5GB+ recommended for models")
    except ImportError:
        print("  ℹ psutil not installed - cannot check disk space")


def test_cuda_availability():
    """Check if CUDA is available for GPU acceleration"""
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            print(f"✓ CUDA available: {device_name}")
        else:
            print("  ℹ CUDA not available (CPU mode)")
    except ImportError:
        print("  ℹ PyTorch not installed - cannot check CUDA")


def run_all_tests():
    """Run all system health tests"""
    print("=" * 60)
    print("SYSTEM HEALTH CHECK")
    print("=" * 60)

    tests = [
        ("Python Version", test_python_version),
        ("Core Dependencies", test_core_dependencies),
        ("Tesseract Installation", test_tesseract_installation),
        ("Configuration Files", test_config_files),
        ("ModelManager", test_model_manager_initialization),
        ("System Memory", test_memory_available),
        ("Disk Space", test_disk_space),
        ("CUDA/GPU", test_cuda_availability),
    ]

    results = {}
    for name, test_func in tests:
        print(f"\n{name}:")
        try:
            result = test_func()
            results[name] = result if result is not None else True
        except Exception as e:
            print(f"✗ {name} FAILED: {e}")
            results[name] = False

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\n✓ All tests passed! System is ready.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Review errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
