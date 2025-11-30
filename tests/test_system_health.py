import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_python_version():
    version = sys.version_info
    assert version.major == 3 and version.minor >= 8, \
        f"Python 3.8+ required, found {version.major}.{version.minor}"
    print(f"[OK] Python version: {version.major}.{version.minor}.{version.micro}")

def test_core_dependencies():
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
            print(f"[OK] {name} installed")
        except (ImportError, OSError) as e:
            # OSError can happen when torch is partially installed but broken
            if 'optional' in name:
                print(f"[WARN] {name} not installed (optional)")
            else:
                print(f"[FAIL] {name} NOT installed (required)")
                raise

def test_tesseract_installation():
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"[OK] Tesseract OCR version: {version}")
    except Exception as e:
        print(f"[WARN] Tesseract OCR not available: {e}")
        print("  Install from: https://github.com/tesseract-ocr/tesseract")

def test_config_files():
    config_path = Path(__file__).parent.parent / 'shared' / 'config' / 'models_config.json'
    assert config_path.exists(), f"Config file not found: {config_path}"
    import json
    with open(config_path) as f:
        config = json.load(f)
    assert 'available_models' in config
    assert 'default_model' in config
    print(f"[OK] Configuration file valid ({len(config['available_models'])} models)")

def test_model_manager_initialization():
    from shared.models.model_manager import ModelManager
    try:
        manager = ModelManager()
        models = manager.get_available_models()
        print(f"[OK] ModelManager initialized ({len(models)} models available)")
    except Exception as e:
        print(f"[FAIL] ModelManager initialization failed: {e}")
        assert False, f"ModelManager initialization failed: {e}"

def test_memory_available():
    try:
        import psutil
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        total_gb = memory.total / (1024**3)
        print(f"[OK] Memory: {available_gb:.1f}GB available / {total_gb:.1f}GB total")
        if available_gb < 2:
            print("  [WARN] Warning: Low memory. 4GB+ recommended for model loading")
    except ImportError:
        print("  [INFO] psutil not installed - cannot check memory")

def test_disk_space():
    try:
        import psutil
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024**3)
        print(f"[OK] Disk space: {free_gb:.1f}GB free")
        if free_gb < 5:
            print("  [WARN] Warning: Low disk space. 5GB+ recommended for models")
    except ImportError:
        print("  [INFO] psutil not installed - cannot check disk space")

def test_cuda_availability():
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            print(f"[OK] CUDA available: {device_name}")
        else:
            print("  [INFO] CUDA not available (CPU mode)")
    except (ImportError, OSError):
        # OSError can happen when torch is partially installed but broken
        print("  [INFO] PyTorch not installed or not working - cannot check CUDA")

def run_all_tests():
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
            print(f"[FAIL] {name} FAILED: {e}")
            results[name] = False
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, result in results.items():
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {name}")
    print(f"\nTotal: {passed}/{total} passed")
    if passed == total:
        print("\n[OK] All tests passed! System is ready.")
        return 0
    else:
        print(f"\n[WARN] {total - passed} test(s) failed. Review errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
