#!/usr/bin/env python3
"""
Quick Test Runner for DonutProcessor Tests
Automatically clears cache and runs DonutProcessor tests with detailed output
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path


def clear_cache():
    """Clear Python and pytest cache"""
    print("🧹 Clearing cache...")

    # Remove __pycache__ directories
    for pycache_dir in Path('.').rglob('__pycache__'):
        try:
            shutil.rmtree(pycache_dir)
        except Exception:
            pass

    # Remove .pyc files
    for pyc_file in Path('.').rglob('*.pyc'):
        try:
            pyc_file.unlink()
        except Exception:
            pass

    # Remove pytest cache
    pytest_cache = Path('.pytest_cache')
    if pytest_cache.exists():
        try:
            shutil.rmtree(pytest_cache)
        except Exception:
            pass

    print("✓ Cache cleared\n")


def main():
    """Run DonutProcessor tests"""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║         DonutProcessor Test Runner (with Auto Cache Clear)    ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")

    # Clear cache first
    clear_cache()

    # Run the tests
    print("🧪 Running DonutProcessor tests...\n")

    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/shared/test_donut_processor.py',
        '-v',
        '--tb=short',
        '--color=yes'
    ]

    try:
        result = subprocess.run(cmd, timeout=300)
        return result.returncode
    except subprocess.TimeoutExpired:
        print("\n❌ Tests timed out after 5 minutes")
        return 1
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        if exit_code == 0:
            print("\n✅ All DonutProcessor tests passed!")
        else:
            print(f"\n❌ Tests failed with exit code {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(130)
