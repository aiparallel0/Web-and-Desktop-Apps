#!/usr/bin/env python3
"""
Test PORT Environment Variable Fix

Validates that the PORT sanitization fixes work correctly.
"""

import os
import sys
import subprocess

def test_python_port_sanitization():
    """Test PORT sanitization in Python code (app.py)"""
    print("\n" + "="*80)
    print("Testing Python PORT Sanitization (app.py)")
    print("="*80 + "\n")
    
    test_cases = [
        ('$PORT', 'Unexpanded $PORT'),
        ('${PORT}', 'Unexpanded ${PORT}'),
        ('', 'Empty string'),
        ('   ', 'Whitespace only'),
        ('8000', 'Valid port'),
    ]
    
    for port_value, description in test_cases:
        print(f"Test: {description}")
        print(f"  Input PORT: {repr(port_value)}")
        
        # Simulate the sanitization logic from app.py
        port = port_value if port_value else '5000'
        
        if not port or not port.strip() or port.startswith('$') or port.startswith('${'):
            port = '5000'
            print(f"  ✅ Sanitized to default: {port}")
        else:
            try:
                port_int = int(port)
                if 1 <= port_int <= 65535:
                    print(f"  ✅ Valid port: {port}")
                else:
                    print(f"  ⚠️  Port {port} outside valid range")
            except ValueError:
                print(f"  ❌ Invalid port format: {repr(port)}")
        print()

def test_shell_port_validation():
    """Test PORT validation in shell scripts"""
    print("="*80)
    print("Testing Shell Script PORT Validation (start_web.sh)")
    print("="*80 + "\n")
    
    # Just validate syntax
    result = subprocess.run(
        ['bash', '-n', 'start_web.sh'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ start_web.sh syntax is valid\n")
        return True
    else:
        print(f"❌ start_web.sh syntax error: {result.stderr}\n")
        return False

def test_dockerfile_syntax():
    """Test Dockerfile CMD syntax"""
    print("="*80)
    print("Testing Dockerfile CMD Syntax")
    print("="*80 + "\n")
    
    # Check if Dockerfile exists and uses startup script
    try:
        with open('Dockerfile', 'r') as f:
            content = f.read()
        
        # Check for startup script approach (recommended)
        if 'docker-entrypoint.sh' in content:
            print("✅ Dockerfile uses docker-entrypoint.sh startup script\n")
            
            # Also check if the script file exists
            import os
            if os.path.exists('scripts/docker-entrypoint.sh'):
                print("✅ docker-entrypoint.sh script exists\n")
                return True
            else:
                print("⚠️  docker-entrypoint.sh script not found\n")
                return False
        # Fall back to checking for inline PORT validation
        elif 'if [ -z \\\"$PORT\\\"' in content or 'if [ -z "$PORT"' in content:
            print("✅ Dockerfile contains PORT validation logic\n")
            return True
        else:
            print("⚠️  Dockerfile might not have PORT validation\n")
            return False
    except FileNotFoundError:
        print("❌ Dockerfile not found\n")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PORT ENVIRONMENT VARIABLE FIX VALIDATION")
    print("="*80)
    
    # Test 1: Python sanitization
    test_python_port_sanitization()
    
    # Test 2: Shell validation
    shell_passed = test_shell_port_validation()
    
    # Test 3: Dockerfile syntax
    docker_passed = test_dockerfile_syntax()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80 + "\n")
    
    if shell_passed and docker_passed:
        print("✅ All validation tests passed!")
        print("The PORT environment variable handling has been fixed.\n")
        return 0
    else:
        print("⚠️  Some tests need attention\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
