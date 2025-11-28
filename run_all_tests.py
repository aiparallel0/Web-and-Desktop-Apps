#!/usr/bin/env python3
"""
Comprehensive Test Runner for Receipt Extractor
Runs all test suites with detailed reporting and coverage analysis

Features:
- Automatic cache cleanup before tests
- Detailed error reporting
- Coverage analysis
- Test result logging
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


def print_section(title):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {title}{Colors.NC}")
    print("─" * 60)


def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}[OK]{Colors.NC} {message}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}[FAIL]{Colors.NC} {message}")


def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}")


def print_info(message):
    """Print info message"""
    print(f"{Colors.CYAN}[INFO]{Colors.NC} {message}")


def clear_python_cache(root_dir='.'):
    """
    Clear Python bytecode cache and pytest cache

    Args:
        root_dir: Root directory to start cleaning from

    Returns:
        tuple: (num_pycache_removed, num_pyc_removed, num_pytest_cache_removed)
    """
    pycache_count = 0
    pyc_count = 0
    pytest_cache_count = 0

    root_path = Path(root_dir)

    # Remove __pycache__ directories
    for pycache_dir in root_path.rglob('__pycache__'):
        try:
            shutil.rmtree(pycache_dir)
            pycache_count += 1
        except Exception as e:
            print_warning(f"Could not remove {pycache_dir}: {e}")

    # Remove .pyc files
    for pyc_file in root_path.rglob('*.pyc'):
        try:
            pyc_file.unlink()
            pyc_count += 1
        except Exception as e:
            print_warning(f"Could not remove {pyc_file}: {e}")

    # Remove pytest cache
    pytest_cache = root_path / '.pytest_cache'
    if pytest_cache.exists():
        try:
            shutil.rmtree(pytest_cache)
            pytest_cache_count = 1
        except Exception as e:
            print_warning(f"Could not remove .pytest_cache: {e}")

    # Remove coverage cache
    coverage_cache = root_path / '.coverage'
    if coverage_cache.exists():
        try:
            coverage_cache.unlink()
        except Exception as e:
            print_warning(f"Could not remove .coverage: {e}")

    return pycache_count, pyc_count, pytest_cache_count


def verify_environment():
    """
    Verify the test environment is properly set up

    Returns:
        bool: True if environment is valid
    """
    issues = []

    # Check if pytest is installed
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            issues.append("pytest is not properly installed")
    except Exception as e:
        issues.append(f"pytest check failed: {e}")

    # Check if we're in the project root
    if not Path('tests').exists():
        issues.append("Not in project root directory (tests/ not found)")

    if not Path('shared').exists():
        issues.append("Not in project root directory (shared/ not found)")

    # Check if critical test files exist
    critical_tests = [
        'tests/test_system_health.py',
        'tests/shared/test_donut_processor.py'
    ]

    for test_file in critical_tests:
        if not Path(test_file).exists():
            issues.append(f"Critical test file missing: {test_file}")

    if issues:
        print_error("Environment validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    return True


def run_test_file(test_path, description, log_dir=None):
    """
    Run a single test file with pytest

    Args:
        test_path: Path to test file
        description: Human-readable description
        log_dir: Optional directory to save logs

    Returns:
        tuple: (passed, total_tests, coverage_percent)
    """
    if not os.path.exists(test_path):
        print_warning(f"Test file not found: {test_path}")
        return False, 0, 0

    print_info(f"Running {description}...")

    # Build pytest command
    cmd = [
        sys.executable, '-m', 'pytest',
        test_path,
        '-v',
        '--tb=short',
        '--cov=shared',
        '--cov=web-app/backend',
        '--cov-report=term-missing'
    ]

    # Add log file if specified
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{Path(test_path).stem}.log")
        cmd.extend(['--cov-report', f'html:htmlcov/{Path(test_path).stem}'])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        # Parse output for test results
        passed = result.returncode == 0
        output_lines = result.stdout.split('\n')

        # Extract test count
        total_tests = 0
        for line in output_lines:
            if ' passed' in line or ' failed' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'passed' and i > 0:
                        try:
                            total_tests = int(parts[i-1])
                        except ValueError:
                            pass

        # Extract coverage percentage
        coverage_percent = 0
        for line in output_lines:
            if 'TOTAL' in line and '%' in line:
                parts = line.split()
                for part in parts:
                    if '%' in part:
                        try:
                            coverage_percent = int(part.rstrip('%'))
                        except ValueError:
                            pass

        # Save log if specified
        if log_dir and log_file:
            with open(log_file, 'w') as f:
                f.write(f"=== {description} ===\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Command: {' '.join(cmd)}\n\n")
                f.write(result.stdout)
                f.write("\n\n=== STDERR ===\n")
                f.write(result.stderr)

        if passed:
            print_success(f"{description} passed ({total_tests} tests, {coverage_percent}% coverage)")
        else:
            print_error(f"{description} failed")
            # Print last few lines of output for debugging
            error_lines = [line for line in output_lines if 'FAILED' in line or 'ERROR' in line]
            if error_lines:
                print(f"  Errors: {' '.join(error_lines[:3])}")

        return passed, total_tests, coverage_percent

    except subprocess.TimeoutExpired:
        print_error(f"{description} timed out after 5 minutes")
        return False, 0, 0
    except Exception as e:
        print_error(f"{description} error: {e}")
        return False, 0, 0


def main():
    """Main test runner"""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║                                                                ║")
    print("║        Receipt Extractor - Comprehensive Test Suite           ║")
    print("║                                                                ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.NC}")

    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Verify environment before running tests
    print_section("Environment Verification")
    if not verify_environment():
        print_error("Environment verification failed. Please fix issues before running tests.")
        return 1
    print_success("Environment is properly configured")

    # Clear caches for clean test run
    print_section("Cache Cleanup")
    print_info("Clearing Python bytecode cache and pytest cache...")
    pycache_count, pyc_count, pytest_cache_count = clear_python_cache()
    print_success(f"Removed {pycache_count} __pycache__ directories")
    print_success(f"Removed {pyc_count} .pyc files")
    if pytest_cache_count:
        print_success("Removed .pytest_cache directory")
    print_info("Cache cleanup complete - tests will use fresh code")

    log_dir = script_dir / 'logs' / 'test-reports'

    # Define test suite
    test_suites = [
        {
            'path': 'tests/test_system_health.py',
            'description': 'System Health Tests',
            'critical': True
        },
        {
            'path': 'tests/shared/test_image_processing.py',
            'description': 'Image Processing Tests',
            'critical': True
        },
        {
            'path': 'tests/shared/test_model_manager.py',
            'description': 'Model Manager Tests',
            'critical': True
        },
        {
            'path': 'tests/shared/test_base_processor.py',
            'description': 'Base Processor Tests (NEW - High Coverage)',
            'critical': False
        },
        {
            'path': 'tests/shared/test_easyocr_processor.py',
            'description': 'EasyOCR Processor Tests (NEW)',
            'critical': False
        },
        {
            'path': 'tests/shared/test_paddle_processor.py',
            'description': 'Paddle Processor Tests (NEW)',
            'critical': False
        },
        {
            'path': 'tests/shared/test_donut_processor.py',
            'description': 'Donut Processor Tests (NEW)',
            'critical': False
        },
        {
            'path': 'tests/web/test_api.py',
            'description': 'API Tests',
            'critical': True
        }
    ]

    print_section("Running Test Suite")

    results = []
    total_tests = 0
    total_passed_suites = 0
    critical_failures = []

    for suite in test_suites:
        passed, test_count, coverage = run_test_file(
            suite['path'],
            suite['description'],
            log_dir
        )

        results.append({
            'name': suite['description'],
            'passed': passed,
            'tests': test_count,
            'coverage': coverage,
            'critical': suite['critical']
        })

        total_tests += test_count
        if passed:
            total_passed_suites += 1
        elif suite['critical']:
            critical_failures.append(suite['description'])

    # Print summary
    print_section("Test Summary")

    print(f"\n{Colors.BOLD}Results by Test Suite:{Colors.NC}")
    for result in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.NC}" if result['passed'] else f"{Colors.RED}✗ FAIL{Colors.NC}"
        critical = " [CRITICAL]" if result['critical'] else ""
        print(f"  {status} {result['name']}{critical}")
        print(f"      Tests: {result['tests']}, Coverage: {result['coverage']}%")

    print(f"\n{Colors.BOLD}Overall Statistics:{Colors.NC}")
    print(f"  Total Test Suites: {len(test_suites)}")
    print(f"  Passed: {Colors.GREEN}{total_passed_suites}{Colors.NC}")
    print(f"  Failed: {Colors.RED}{len(test_suites) - total_passed_suites}{Colors.NC}")
    print(f"  Total Tests Run: {total_tests}")

    avg_coverage = sum(r['coverage'] for r in results) / len(results) if results else 0
    print(f"  Average Coverage: {avg_coverage:.1f}%")

    # Check for critical failures
    if critical_failures:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠ CRITICAL FAILURES:{Colors.NC}")
        for failure in critical_failures:
            print(f"  - {failure}")
        print("\nCritical tests must pass before deploying to production!")
        return 1

    # Overall pass/fail
    if total_passed_suites == len(test_suites):
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.NC}")
        print(f"\nTest reports saved to: {log_dir}")
        print(f"Coverage reports saved to: htmlcov/")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ SOME TESTS FAILED{Colors.NC}")
        print(f"Non-critical tests failed. Review logs for details.")
        print(f"\nTest reports saved to: {log_dir}")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrupted by user{Colors.NC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.NC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
