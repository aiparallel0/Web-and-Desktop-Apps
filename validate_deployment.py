#!/usr/bin/env python3
"""
Deployment Validation Script

Tests that the Flask app can be properly imported and started by gunicorn,
ensuring Railway deployment will succeed.

This script validates:
1. Module structure (web.backend is a package)
2. App can be imported as web.backend.app:app
3. Health endpoint responds correctly
4. All routes are registered
5. Gunicorn can start the app
"""

import sys
import time
import subprocess
import requests
import signal
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.END}")

def test_module_structure():
    """Test that web and web.backend are proper Python packages"""
    print_header("Test 1: Module Structure")
    
    project_root = Path(__file__).parent
    
    # Check __init__.py files exist
    web_init = project_root / "web" / "__init__.py"
    backend_init = project_root / "web" / "backend" / "__init__.py"
    
    if not web_init.exists():
        print_error(f"Missing {web_init}")
        return False
    
    if not backend_init.exists():
        print_error(f"Missing {backend_init}")
        return False
    
    print_success("web/__init__.py exists")
    print_success("web/backend/__init__.py exists")
    
    # Try importing the packages
    try:
        import web
        print_success("web package can be imported")
    except ImportError as e:
        print_error(f"Cannot import web package: {e}")
        return False
    
    try:
        import web.backend
        print_success("web.backend package can be imported")
    except ImportError as e:
        print_error(f"Cannot import web.backend package: {e}")
        return False
    
    return True

def test_app_import():
    """Test that the Flask app can be imported"""
    print_header("Test 2: Flask App Import")
    
    start_time = time.time()
    try:
        from web.backend.app import app
        elapsed = time.time() - start_time
        
        print_success(f"App imported successfully in {elapsed:.2f}s")
        print_info(f"App name: {app.name}")
        print_info(f"App is Flask instance: {app.__class__.__name__}")
        print_info(f"Routes registered: {len(list(app.url_map.iter_rules()))}")
        
        return True, app
    except ImportError as e:
        print_error(f"Cannot import app: {e}")
        return False, None
    except Exception as e:
        print_error(f"Error importing app: {e}")
        return False, None

def test_health_endpoint_direct(app):
    """Test health endpoint using test client"""
    print_header("Test 3: Health Endpoint (Direct)")
    
    try:
        client = app.test_client()
        response = client.get('/api/health')
        
        if response.status_code == 200:
            data = response.get_json()
            print_success("Health endpoint returned 200 OK")
            print_info(f"Service: {data.get('service')}")
            print_info(f"Status: {data.get('status')}")
            print_info(f"Version: {data.get('version')}")
            return True
        else:
            print_error(f"Health endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error testing health endpoint: {e}")
        return False

def test_gunicorn_start():
    """Test that gunicorn can start the app"""
    print_header("Test 4: Gunicorn Startup")
    
    print_info("Starting gunicorn...")
    
    # Start gunicorn in background
    proc = subprocess.Popen(
        ['gunicorn', '--bind', '127.0.0.1:8765', '--workers', '1', 
         '--timeout', '30', '--log-level', 'info', 'web.backend.app:app'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for startup
    time.sleep(3)
    
    # Check if process is running
    if proc.poll() is not None:
        stdout, stderr = proc.communicate()
        print_error("Gunicorn failed to start")
        print_error(f"STDOUT: {stdout}")
        print_error(f"STDERR: {stderr}")
        return False
    
    print_success("Gunicorn started successfully")
    
    # Test health endpoint via HTTP
    try:
        response = requests.get('http://127.0.0.1:8765/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("Health endpoint accessible via HTTP")
            print_info(f"Service: {data.get('service')}")
            print_info(f"Status: {data.get('status')}")
            result = True
        else:
            print_error(f"Health endpoint returned {response.status_code}")
            result = False
    except Exception as e:
        print_error(f"Error accessing health endpoint: {e}")
        result = False
    finally:
        # Stop gunicorn
        print_info("Stopping gunicorn...")
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=5)
        print_success("Gunicorn stopped")
    
    return result

def test_docker_command_syntax():
    """Test that the Docker CMD syntax is correct"""
    print_header("Test 5: Docker CMD Validation")
    
    # Read Dockerfile
    dockerfile = Path(__file__).parent / "Dockerfile"
    if not dockerfile.exists():
        print_error("Dockerfile not found")
        return False
    
    with open(dockerfile) as f:
        content = f.read()
    
    # Check for correct CMD
    if 'web.backend.app:app' in content:
        print_success("Dockerfile uses correct module path: web.backend.app:app")
    else:
        print_error("Dockerfile doesn't use web.backend.app:app")
        return False
    
    # Check for PORT variable
    if '$PORT' in content or '${PORT}' in content:
        print_success("Dockerfile uses PORT environment variable")
    else:
        print_error("Dockerfile doesn't use PORT variable")
        return False
    
    return True

def main():
    """Run all validation tests"""
    print_header("DEPLOYMENT VALIDATION SUITE")
    print_info("Testing Flask app can be started by gunicorn for Railway deployment")
    
    results = []
    
    # Test 1: Module structure
    results.append(("Module Structure", test_module_structure()))
    
    # Test 2: App import
    success, app = test_app_import()
    results.append(("Flask App Import", success))
    
    if app:
        # Test 3: Health endpoint direct
        results.append(("Health Endpoint (Direct)", test_health_endpoint_direct(app)))
        
        # Test 4: Gunicorn
        try:
            results.append(("Gunicorn Startup", test_gunicorn_start()))
        except Exception as e:
            print_error(f"Gunicorn test failed: {e}")
            results.append(("Gunicorn Startup", False))
    else:
        results.append(("Health Endpoint (Direct)", False))
        results.append(("Gunicorn Startup", False))
    
    # Test 5: Docker CMD
    results.append(("Docker CMD Validation", test_docker_command_syntax()))
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        if success:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    if passed == total:
        print_success(f"ALL TESTS PASSED ({passed}/{total})")
        print_success("✅ App is ready for Railway deployment!")
        print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")
        return 0
    else:
        print_error(f"SOME TESTS FAILED ({passed}/{total})")
        print_error("❌ Fix the issues before deploying to Railway")
        print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
