#!/usr/bin/env python3
"""
Docker Optimization Verification Script

This script verifies that the Docker optimization meets all requirements:
1. Image size is under 500 MB
2. Required files are present in the image
3. Tesseract OCR is installed
4. Health check endpoint works
"""

import subprocess
import sys
import json
import time

def run_command(cmd, shell=True):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1

def check_image_size(image_name="receipt-extractor:optimized"):
    """Check if Docker image size is under 500 MB."""
    print("\n✓ Checking Docker image size...")
    stdout, stderr, code = run_command(
        f'docker images {image_name} --format "{{{{.Size}}}}"'
    )
    
    if code != 0 or not stdout:
        print(f"  ❌ Failed to get image size: {stderr}")
        return False
    
    size_str = stdout.strip()
    print(f"  Image size: {size_str}")
    
    # Parse size (e.g., "486MB" or "0.5GB")
    if "GB" in size_str:
        size_gb = float(size_str.replace("GB", ""))
        size_mb = size_gb * 1024
    else:
        size_mb = float(size_str.replace("MB", ""))
    
    if size_mb > 500:
        print(f"  ❌ Image size ({size_mb:.0f} MB) exceeds 500 MB target")
        return False
    
    print(f"  ✅ Image size ({size_mb:.0f} MB) is under 500 MB target")
    return True

def check_required_files(image_name="receipt-extractor:optimized"):
    """Check if required files exist in the image."""
    print("\n✓ Checking required files in image...")
    
    files_to_check = [
        "/app/shared/models/ocr.py",
        "/app/web/backend/app.py",
        "/app/web/frontend/index.html",
        "/app/requirements-prod.txt"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        stdout, stderr, code = run_command(
            f'docker run --rm {image_name} test -f {file_path} && echo "exists" || echo "missing"'
        )
        
        if "exists" in stdout:
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} is missing")
            all_exist = False
    
    return all_exist

def check_tesseract(image_name="receipt-extractor:optimized"):
    """Check if Tesseract OCR is installed."""
    print("\n✓ Checking Tesseract OCR installation...")
    
    stdout, stderr, code = run_command(
        f'docker run --rm {image_name} tesseract --version 2>&1 | head -1'
    )
    
    if code != 0 or "tesseract" not in stdout.lower():
        print(f"  ❌ Tesseract not found: {stderr}")
        return False
    
    print(f"  ✅ {stdout.strip()}")
    return True

def check_health_endpoint(container_name="receipt-test-verify", port="5002"):
    """Start container and check health endpoint."""
    print("\n✓ Checking health endpoint...")
    
    # Clean up any existing container
    run_command(f'docker stop {container_name} 2>/dev/null || true')
    run_command(f'docker rm {container_name} 2>/dev/null || true')
    
    # Start container
    print(f"  Starting container on port {port}...")
    stdout, stderr, code = run_command(
        f'docker run -d --name {container_name} -p {port}:5000 '
        f'-e DATABASE_URL=sqlite:///receipts.db '
        f'-e SECRET_KEY=test-secret-key '
        f'receipt-extractor:optimized'
    )
    
    if code != 0:
        print(f"  ❌ Failed to start container: {stderr}")
        return False
    
    # Wait for startup
    print("  Waiting for application to start (10 seconds)...")
    time.sleep(10)
    
    # Check health endpoint
    stdout, stderr, code = run_command(
        f'curl -s http://localhost:{port}/api/health'
    )
    
    # Clean up
    run_command(f'docker stop {container_name}')
    run_command(f'docker rm {container_name}')
    
    if code != 0:
        print(f"  ❌ Failed to connect to health endpoint: {stderr}")
        return False
    
    try:
        health_data = json.loads(stdout)
        if health_data.get("status") == "healthy":
            print(f"  ✅ Health endpoint responds: {health_data.get('service')}")
            print(f"  ✅ Python version: {health_data.get('system', {}).get('python_version')}")
            return True
        else:
            print(f"  ❌ Health check failed: {health_data}")
            return False
    except json.JSONDecodeError:
        print(f"  ❌ Invalid health response: {stdout[:100]}")
        return False

def check_excluded_files(image_name="receipt-extractor:optimized"):
    """Check that heavy files/directories are excluded."""
    print("\n✓ Checking excluded files/directories...")
    
    excluded_items = [
        "/app/desktop",
        "/app/docs",
        "/app/tools/tests",
        "/app/web/backend/training"
    ]
    
    all_excluded = True
    for item_path in excluded_items:
        stdout, stderr, code = run_command(
            f'docker run --rm {image_name} test -e {item_path} && echo "exists" || echo "excluded"'
        )
        
        if "excluded" in stdout:
            print(f"  ✅ {item_path} excluded")
        else:
            print(f"  ❌ {item_path} should be excluded but exists")
            all_excluded = False
    
    return all_excluded

def main():
    """Run all verification checks."""
    print("=" * 70)
    print("Docker Image Optimization Verification")
    print("=" * 70)
    
    checks = [
        ("Image Size", check_image_size),
        ("Required Files", check_required_files),
        ("Tesseract OCR", check_tesseract),
        ("Excluded Files", check_excluded_files),
        ("Health Endpoint", check_health_endpoint)
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"\n  ❌ {check_name} check failed with exception: {e}")
            results[check_name] = False
    
    print("\n" + "=" * 70)
    print("Verification Summary")
    print("=" * 70)
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All verification checks passed!")
        print("Docker image is optimized and ready for production deployment.")
        return 0
    else:
        print("\n⚠️  Some verification checks failed.")
        print("Please review the output above and fix any issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
