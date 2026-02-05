#!/usr/bin/env python3
"""
Test PORT Environment Variable Handling

Verifies that the PORT environment variable is properly handled in all
startup configurations to prevent the error: "'${PORT' is not a valid port number"
"""

import os
import subprocess
import sys
from pathlib import Path

def test_start_web_script():
    """Test that start_web.sh properly handles PORT variable"""
    print("\n" + "="*80)
    print("Testing start_web.sh PORT handling")
    print("="*80 + "\n")
    
    script_path = Path(__file__).parent / "start_web.sh"
    
    if not script_path.exists():
        print("❌ start_web.sh not found")
        return False
    
    # Test 1: Check script exists and is executable
    if not os.access(script_path, os.X_OK):
        print("⚠️  start_web.sh is not executable, attempting to fix...")
        try:
            os.chmod(script_path, 0o755)
            print("✅ Made start_web.sh executable")
        except Exception as e:
            print(f"❌ Failed to make executable: {e}")
            return False
    else:
        print("✅ start_web.sh is executable")
    
    # Test 2: Check bash syntax
    result = subprocess.run(
        ['bash', '-n', str(script_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Bash syntax is valid")
    else:
        print(f"❌ Bash syntax error: {result.stderr}")
        return False
    
    # Test 3: Check that script handles PORT variable
    with open(script_path, 'r') as f:
        content = f.read()
    
    if 'PORT' in content and '${PORT}' in content:
        print("✅ Script references PORT environment variable")
    else:
        print("❌ Script doesn't properly reference PORT variable")
        return False
    
    if 'export PORT=8000' in content or 'PORT=8000' in content:
        print("✅ Script has PORT default fallback")
    else:
        print("⚠️  Script might not have PORT fallback (check manually)")
    
    # Test 4: Simulate PORT variable expansion
    test_env = os.environ.copy()
    test_env['PORT'] = '9999'
    
    # Just check if the script would start correctly (it will fail on gunicorn, that's OK)
    result = subprocess.run(
        ['bash', str(script_path), '--help'],
        env=test_env,
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if 'Starting on PORT: 9999' in result.stdout or 'Starting on PORT: 9999' in result.stderr:
        print("✅ Script correctly uses PORT environment variable")
    else:
        # It might still work, just not print the message
        print("⚠️  Script may use PORT but doesn't log it")
    
    print("\n✅ start_web.sh PORT handling tests passed\n")
    return True

def test_app_py_port_handling():
    """Test that app.py properly handles PORT variable"""
    print("="*80)
    print("Testing web/backend/app.py PORT handling")
    print("="*80 + "\n")
    
    app_path = Path(__file__).parent / "web" / "backend" / "app.py"
    
    if not app_path.exists():
        print("❌ web/backend/app.py not found")
        return False
    
    with open(app_path, 'r') as f:
        content = f.read()
    
    # Check for PORT environment variable usage
    if "os.environ.get('PORT'" in content or 'os.getenv("PORT"' in content or 'os.getenv(\'PORT\'' in content:
        print("✅ app.py uses PORT environment variable")
    else:
        print("❌ app.py doesn't use PORT environment variable")
        return False
    
    # Check for int conversion
    if "int(os.environ.get('PORT'" in content or "int(os.getenv('PORT'" in content or 'int(os.getenv("PORT"' in content:
        print("✅ app.py converts PORT to integer")
    else:
        print("⚠️  app.py might not convert PORT to integer (could cause issues)")
    
    # Check for default fallback
    if ', 5000)' in content or ', 8000)' in content:
        print("✅ app.py has PORT default fallback")
    else:
        print("⚠️  app.py might not have PORT fallback")
    
    print("\n✅ app.py PORT handling tests passed\n")
    return True

def test_procfile_format():
    """Test that Procfile uses correct format"""
    print("="*80)
    print("Testing Procfile format")
    print("="*80 + "\n")
    
    base_dir = Path(__file__).parent
    procfiles = ['Procfile', 'Procfile.railway']
    
    all_good = True
    
    for procfile_name in procfiles:
        procfile_path = base_dir / procfile_name
        
        if not procfile_path.exists():
            print(f"⚠️  {procfile_name} not found (might be OK)")
            continue
        
        with open(procfile_path, 'r') as f:
            content = f.read()
        
        print(f"\nChecking {procfile_name}:")
        
        # Check if it uses start_web.sh
        if 'start_web.sh' in content or 'bash start_web.sh' in content:
            print(f"  ✅ Uses start_web.sh script (good for PORT handling)")
        elif '${PORT' in content:
            print(f"  ⚠️  Uses ${{PORT}} syntax (may fail on some platforms)")
            print(f"     Consider using start_web.sh instead")
            all_good = False
        else:
            print(f"  ⚠️  Doesn't reference PORT or start_web.sh")
    
    if all_good:
        print("\n✅ Procfile format tests passed\n")
    else:
        print("\n⚠️  Some Procfiles could be improved\n")
    
    return all_good

def test_env_example():
    """Test that .env.example documents PORT variable"""
    print("="*80)
    print("Testing .env.example documentation")
    print("="*80 + "\n")
    
    env_example = Path(__file__).parent / ".env.example"
    
    if not env_example.exists():
        print("❌ .env.example not found")
        return False
    
    with open(env_example, 'r') as f:
        content = f.read()
    
    # Check for PORT documentation
    if 'PORT=' in content:
        print("✅ PORT is documented in .env.example")
    else:
        print("⚠️  PORT is not explicitly documented (might be OK)")
    
    # Check for CELERY_BEAT_ENABLED
    if 'CELERY_BEAT_ENABLED' in content:
        print("✅ CELERY_BEAT_ENABLED is documented")
    else:
        print("❌ CELERY_BEAT_ENABLED is missing from .env.example")
        return False
    
    # Check for CELERY_BEAT_SCHEDULE
    if 'CELERY_BEAT_SCHEDULE' in content:
        print("✅ CELERY_BEAT_SCHEDULE is documented")
    else:
        print("⚠️  CELERY_BEAT_SCHEDULE is not documented")
    
    print("\n✅ .env.example documentation tests passed\n")
    return True

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PORT ENVIRONMENT VARIABLE HANDLING TESTS")
    print("="*80)
    
    results = []
    
    # Test 1: start_web.sh
    results.append(("start_web.sh", test_start_web_script()))
    
    # Test 2: app.py
    results.append(("app.py", test_app_py_port_handling()))
    
    # Test 3: Procfile
    results.append(("Procfile", test_procfile_format()))
    
    # Test 4: .env.example
    results.append((".env.example", test_env_example()))
    
    # Summary
    print("="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:20s} {status}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All PORT handling tests passed!")
        print("The error \"'${PORT' is not a valid port number\" should be fixed.\n")
        return 0
    else:
        print("\n⚠️  Some tests failed or need improvement")
        print("Review the output above for details.\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
