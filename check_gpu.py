#!/usr/bin/env python3
"""
GPU Setup Verification Script
Checks if CUDA and GPU-enabled PyTorch are properly installed
"""
import sys

def check_python_version():
    """Check Python version"""
    print("=" * 60)
    print("1. Python Version Check")
    print("=" * 60)
    version = sys.version
    major, minor = sys.version_info[:2]
    print(f"✓ Python {major}.{minor}")
    print(f"  {version}")

    if major < 3 or (major == 3 and minor < 8):
        print("  ⚠️  Warning: Python 3.8+ recommended")
    print()

def check_torch():
    """Check PyTorch installation"""
    print("=" * 60)
    print("2. PyTorch Installation Check")
    print("=" * 60)

    try:
        import torch
        print(f"✓ PyTorch {torch.__version__} installed")

        # Check if it's CPU or GPU version
        if '+cu' in torch.__version__:
            cuda_version = torch.__version__.split('+cu')[1]
            print(f"  ✓ GPU-enabled version (CUDA {cuda_version})")
        else:
            print(f"  ⚠️  CPU-only version detected")
            print(f"     Install GPU version with:")
            print(f"     pip install torch --index-url https://download.pytorch.org/whl/cu121")

        print()
        return torch
    except ImportError:
        print("✗ PyTorch not installed!")
        print("  Install with: pip install torch")
        print()
        return None

def check_cuda(torch_module):
    """Check CUDA availability"""
    print("=" * 60)
    print("3. CUDA Availability Check")
    print("=" * 60)

    if torch_module is None:
        print("✗ Cannot check CUDA (PyTorch not installed)")
        print()
        return False

    try:
        cuda_available = torch_module.cuda.is_available()

        if cuda_available:
            print("✓ CUDA is available!")
            print(f"  CUDA Version: {torch_module.version.cuda}")
            print(f"  cuDNN Version: {torch_module.backends.cudnn.version()}")
            print(f"  Number of GPUs: {torch_module.cuda.device_count()}")
            print()
            return True
        else:
            print("✗ CUDA is NOT available")
            print("  Possible reasons:")
            print("  1. CUDA Toolkit not installed")
            print("  2. No NVIDIA GPU present")
            print("  3. CPU-only PyTorch installed")
            print("  4. NVIDIA drivers outdated")
            print()
            print("  See CUDA_GPU_SETUP.md for installation instructions")
            print()
            return False
    except Exception as e:
        print(f"✗ Error checking CUDA: {e}")
        print()
        return False

def check_gpu_details(torch_module):
    """Check GPU details"""
    print("=" * 60)
    print("4. GPU Details")
    print("=" * 60)

    if torch_module is None or not torch_module.cuda.is_available():
        print("✗ No GPU available")
        print()
        return

    try:
        for i in range(torch_module.cuda.device_count()):
            props = torch_module.cuda.get_device_properties(i)
            print(f"GPU {i}: {torch_module.cuda.get_device_name(i)}")
            print(f"  Total Memory: {props.total_memory / 1024**3:.1f} GB")
            print(f"  Compute Capability: {props.major}.{props.minor}")
            print(f"  Multiprocessors: {props.multi_processor_count}")
            print()
    except Exception as e:
        print(f"✗ Error getting GPU details: {e}")
        print()

def run_simple_test(torch_module):
    """Run a simple GPU computation test"""
    print("=" * 60)
    print("5. GPU Computation Test")
    print("=" * 60)

    if torch_module is None or not torch_module.cuda.is_available():
        print("⊘ Skipped (no GPU available)")
        print()
        return

    try:
        import time

        # CPU test
        print("Testing CPU computation...")
        x_cpu = torch_module.randn(1000, 1000)
        start = time.time()
        _ = torch_module.matmul(x_cpu, x_cpu)
        cpu_time = time.time() - start
        print(f"  CPU: {cpu_time*1000:.2f} ms")

        # GPU test
        print("Testing GPU computation...")
        x_gpu = torch_module.randn(1000, 1000).cuda()
        torch_module.cuda.synchronize()
        start = time.time()
        _ = torch_module.matmul(x_gpu, x_gpu)
        torch_module.cuda.synchronize()
        gpu_time = time.time() - start
        print(f"  GPU: {gpu_time*1000:.2f} ms")

        speedup = cpu_time / gpu_time
        print(f"  Speedup: {speedup:.1f}x faster on GPU! ✓")
        print()

    except Exception as e:
        print(f"✗ Test failed: {e}")
        print()

def check_ai_libraries():
    """Check AI/ML library installations"""
    print("=" * 60)
    print("6. AI/ML Libraries Check")
    print("=" * 60)

    libraries = [
        ('torch', 'PyTorch'),
        ('torchvision', 'TorchVision'),
        ('transformers', 'Transformers'),
        ('PIL', 'Pillow'),
        ('cv2', 'OpenCV'),
        ('numpy', 'NumPy'),
        ('paddleocr', 'PaddleOCR'),
    ]

    for module_name, display_name in libraries:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {display_name}: {version}")
        except ImportError:
            print(f"✗ {display_name}: Not installed")

    print()

def main():
    """Main function"""
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "GPU SETUP VERIFICATION" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    check_python_version()
    torch_module = check_torch()
    cuda_available = check_cuda(torch_module)

    if cuda_available:
        check_gpu_details(torch_module)
        run_simple_test(torch_module)

    check_ai_libraries()

    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if cuda_available:
        print("✓ Your system is ready for GPU-accelerated AI models!")
        print("  Models will run 10-15x faster than CPU-only")
        print()
        print("  Start the server and check logs for:")
        print("  'Model loaded successfully on cuda'")
    else:
        print("⚠️  GPU acceleration is NOT enabled")
        print("  Models will run on CPU (slower)")
        print()
        print("  To enable GPU:")
        print("  1. Check CUDA_GPU_SETUP.md for detailed instructions")
        print("  2. Install CUDA Toolkit from nvidia.com")
        print("  3. Install GPU PyTorch:")
        print("     pip install torch --index-url https://download.pytorch.org/whl/cu121")

    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
