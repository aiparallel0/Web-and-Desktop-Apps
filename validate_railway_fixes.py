#!/usr/bin/env python3
"""
Simple validation script for Railway deployment fixes.
Validates the changes made to fix Railway deployment issues.
"""

import os
import sys

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_failure(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")
    return False

def main():
    print_header("RAILWAY DEPLOYMENT FIX VALIDATION")
    
    all_passed = True
    
    # Test 1: Procfile only has web process
    print("\n1. Testing Procfile...")
    try:
        with open('Procfile', 'r') as f:
            procfile_content = f.read()
        
        if 'web:' in procfile_content and 'gunicorn' in procfile_content:
            print_success("Procfile has web process with gunicorn")
        else:
            all_passed = print_failure("Procfile missing web process or gunicorn")
        
        # Check that worker and beat are removed (not as commented lines starting with process name)
        has_worker = any(line.strip().startswith('worker:') for line in procfile_content.split('\n'))
        has_beat = any(line.strip().startswith('beat:') for line in procfile_content.split('\n'))
        
        if not has_worker and not has_beat:
            print_success("Procfile does NOT have worker or beat processes (correct for Railway)")
        else:
            if has_worker:
                all_passed = print_failure("Procfile still has worker process (should be removed)")
            if has_beat:
                all_passed = print_failure("Procfile still has beat process (should be removed)")
    except FileNotFoundError:
        all_passed = print_failure("Procfile not found")
    except Exception as e:
        all_passed = print_failure(f"Error reading Procfile: {e}")
    
    # Test 2: Aptfile exists and has tesseract-ocr
    print("\n2. Testing Aptfile...")
    try:
        with open('Aptfile', 'r') as f:
            aptfile_content = f.read()
        
        if 'tesseract-ocr' in aptfile_content:
            print_success("Aptfile contains tesseract-ocr")
        else:
            all_passed = print_failure("Aptfile missing tesseract-ocr")
    except FileNotFoundError:
        all_passed = print_failure("Aptfile not found")
    except Exception as e:
        all_passed = print_failure(f"Error reading Aptfile: {e}")
    
    # Test 3: railway.json is correct
    print("\n3. Testing railway.json...")
    try:
        import json
        with open('railway.json', 'r') as f:
            railway_config = json.load(f)
        
        if railway_config.get('deploy', {}).get('healthcheckPath') == '/api/health':
            print_success("railway.json has correct health check path")
        else:
            all_passed = print_failure("railway.json missing or incorrect health check path")
        
        if railway_config.get('deploy', {}).get('healthcheckTimeout', 0) >= 300:
            print_success("railway.json has adequate health check timeout")
        else:
            all_passed = print_failure("railway.json health check timeout too short")
    except FileNotFoundError:
        all_passed = print_failure("railway.json not found")
    except Exception as e:
        all_passed = print_failure(f"Error reading railway.json: {e}")
    
    # Test 4: .env.example has required variables
    print("\n4. Testing .env.example...")
    try:
        with open('.env.example', 'r') as f:
            env_example_content = f.read()
        
        required_vars = ['SECRET_KEY', 'JWT_SECRET']
        for var in required_vars:
            # Check for variable definition (VAR=value), not just mentions in comments
            if f'\n{var}=' in env_example_content or env_example_content.startswith(f'{var}='):
                print_success(f".env.example has {var} variable defined")
            else:
                all_passed = print_failure(f".env.example missing {var} variable definition")
    except FileNotFoundError:
        all_passed = print_failure(".env.example not found")
    except Exception as e:
        all_passed = print_failure(f"Error reading .env.example: {e}")
    
    # Summary
    print_header("VALIDATION SUMMARY")
    if all_passed:
        print_success("All validations passed! Ready for Railway deployment.")
        print("\n⚠️  NEXT STEPS:")
        print("  1. Set SECRET_KEY environment variable in Railway dashboard")
        print("  2. Set JWT_SECRET environment variable in Railway dashboard")
        print("  3. Deploy to Railway - it will automatically use Aptfile")
        print("  4. Monitor deployment logs")
        print("  5. Test health check: curl https://your-app.railway.app/api/health")
        return 0
    else:
        print_failure("Some validations failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
