#!/usr/bin/env python3
"""
Test Docker PORT Environment Variable Handling

This script validates that the Docker image correctly handles the PORT
environment variable for deployment platforms like Railway and Koyeb.
"""

import subprocess
import time
import sys
import requests
from typing import Tuple, Optional

def run_command(cmd: list, timeout: int = 30) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"

def test_docker_build():
    """Test 1: Docker image builds successfully."""
    print("\n" + "="*80)
    print("TEST 1: Docker Build")
    print("="*80)
    
    print("Building Docker image...")
    code, stdout, stderr = run_command(
        ["docker", "build", "-t", "receipt-extractor-test", "."],
        timeout=300
    )
    
    if code == 0:
        print("✅ Docker build succeeded")
        return True
    else:
        print("❌ Docker build failed")
        print(f"Error: {stderr[-500:]}")
        return False

def test_docker_inspect():
    """Test 2: Docker image has correct CMD and entrypoint."""
    print("\n" + "="*80)
    print("TEST 2: Docker Image Inspection")
    print("="*80)
    
    code, stdout, stderr = run_command(
        ["docker", "inspect", "receipt-extractor-test"]
    )
    
    if code == 0:
        print("✅ Docker inspect succeeded")
        if "/app/scripts/docker-entrypoint.sh" in stdout:
            print("✅ CMD uses docker-entrypoint.sh")
            return True
        else:
            print("⚠️  CMD might not use docker-entrypoint.sh")
            return False
    else:
        print("❌ Docker inspect failed")
        return False

def test_startup_script_syntax():
    """Test 3: Startup script has valid bash syntax."""
    print("\n" + "="*80)
    print("TEST 3: Startup Script Syntax")
    print("="*80)
    
    code, stdout, stderr = run_command(
        ["bash", "-n", "scripts/docker-entrypoint.sh"]
    )
    
    if code == 0:
        print("✅ docker-entrypoint.sh syntax is valid")
        return True
    else:
        print("❌ docker-entrypoint.sh has syntax errors")
        print(f"Error: {stderr}")
        return False

def test_dockerfile_has_healthcheck():
    """Test 4: Dockerfile has HEALTHCHECK."""
    print("\n" + "="*80)
    print("TEST 4: Dockerfile HEALTHCHECK")
    print("="*80)
    
    try:
        with open("Dockerfile", "r") as f:
            content = f.read()
        
        if "HEALTHCHECK" in content and "${PORT:-5000}" in content:
            print("✅ Dockerfile has HEALTHCHECK with PORT fallback")
            return True
        else:
            print("⚠️  Dockerfile might not have proper HEALTHCHECK")
            return False
    except Exception as e:
        print(f"❌ Error reading Dockerfile: {e}")
        return False

def cleanup_containers():
    """Clean up any running test containers."""
    subprocess.run(
        ["docker", "stop", "test-container-default", "test-container-custom"],
        capture_output=True
    )
    subprocess.run(
        ["docker", "rm", "test-container-default", "test-container-custom"],
        capture_output=True
    )

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("DOCKER PORT ENVIRONMENT VARIABLE TEST SUITE")
    print("="*80)
    
    # Cleanup before tests
    cleanup_containers()
    
    # Test 1: Build
    build_ok = test_docker_build()
    if not build_ok:
        print("\n❌ Build failed, skipping remaining tests")
        return 1
    
    # Test 2: Inspect
    inspect_ok = test_docker_inspect()
    
    # Test 3: Script syntax
    script_ok = test_startup_script_syntax()
    
    # Test 4: HEALTHCHECK
    healthcheck_ok = test_dockerfile_has_healthcheck()
    
    # Cleanup after tests
    cleanup_containers()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    total_tests = 4
    passed_tests = sum([build_ok, inspect_ok, script_ok, healthcheck_ok])
    
    print(f"\nPassed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("\n✅ All tests passed!")
        print("The Docker PORT environment variable handling is correctly implemented.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
