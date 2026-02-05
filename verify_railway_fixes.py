#!/usr/bin/env python3
"""
Railway Deployment Fix Verification Script

This script verifies that all Railway deployment fixes are properly implemented.
Run this before deploying to Railway to ensure all issues are resolved.

Usage:
    python verify_railway_fixes.py
    
Exit codes:
    0 - All checks passed
    1 - One or more checks failed
"""

import os
import json
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_check(name, passed, details=None):
    """Print a check result."""
    status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
    print(f"{status} - {name}")
    if details:
        print(f"         {details}")


def check_file_exists(filepath, description):
    """Check if a file exists."""
    path = Path(filepath)
    exists = path.exists()
    print_check(description, exists, f"Path: {filepath}")
    return exists


def check_file_content(filepath, expected_content, description):
    """Check if file contains expected content."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        found = expected_content in content
        print_check(description, found, f"Looking for: {expected_content[:50]}...")
        return found
    except Exception as e:
        print_check(description, False, f"Error: {e}")
        return False


def main():
    """Run all verification checks."""
    print_header("RAILWAY DEPLOYMENT FIX VERIFICATION")
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: Procfile.railway exists
    checks_total += 1
    if check_file_exists('Procfile.railway', 'Procfile.railway exists'):
        checks_passed += 1
        
        # Check content
        checks_total += 1
        with open('Procfile.railway', 'r') as f:
            content = f.read()
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        web_only = len(lines) == 1 and lines[0].startswith('web:') and 'celery' not in content.lower()
        print_check('Procfile.railway is web-only', web_only)
        if web_only:
            checks_passed += 1
    
    # Check 2: Procfile beat uses /tmp
    checks_total += 1
    if check_file_content('Procfile', '--schedule=/tmp/celerybeat-schedule', 
                         'Procfile beat uses writable /tmp directory'):
        checks_passed += 1
    
    # Check 3: Procfile has no error handlers
    checks_total += 1
    with open('Procfile', 'r') as f:
        procfile_content = f.read()
    no_error_handlers = '2>&1 || echo' not in procfile_content
    print_check('Procfile has no ineffective error handlers', no_error_handlers)
    if no_error_handlers:
        checks_passed += 1
    
    # Check 4: Dockerfile creates celerybeat directory
    checks_total += 1
    if check_file_content('Dockerfile', 'mkdir -p logs celerybeat', 
                         'Dockerfile creates celerybeat directory'):
        checks_passed += 1
    
    # Check 5: Dockerfile sets permissions
    checks_total += 1
    dockerfile_content = Path('Dockerfile').read_text()
    has_permissions = 'chown -R receipt:receipt' in dockerfile_content and 'celerybeat' in dockerfile_content
    print_check('Dockerfile sets celerybeat permissions', has_permissions)
    if has_permissions:
        checks_passed += 1
    
    # Check 6: Dockerfile sets CELERY_BEAT_SCHEDULE env var
    checks_total += 1
    if check_file_content('Dockerfile', 'CELERY_BEAT_SCHEDULE=/app/celerybeat/schedule.db',
                         'Dockerfile sets CELERY_BEAT_SCHEDULE environment variable'):
        checks_passed += 1
    
    # Check 7: celery_worker uses env var for beat_schedule
    checks_total += 1
    if check_file_content('web/backend/training/celery_worker.py', 
                         "beat_schedule=os.getenv('CELERY_BEAT_SCHEDULE'",
                         'celery_worker.py uses environment variable for beat_schedule'):
        checks_passed += 1
    
    # Check 8: celery_worker has conditional beat schedule
    checks_total += 1
    if check_file_content('web/backend/training/celery_worker.py',
                         "if os.getenv('CELERY_BEAT_ENABLED'",
                         'celery_worker.py has conditional beat schedule'):
        checks_passed += 1
    
    # Check 9: railway.json configuration
    checks_total += 1
    try:
        with open('railway.json', 'r') as f:
            config = json.load(f)
        deploy = config.get('deploy', {})
        correct_config = (
            deploy.get('healthcheckPath') == '/api/health' and
            deploy.get('healthcheckTimeout') == 300 and
            deploy.get('numReplicas') == 1 and
            deploy.get('restartPolicyType') == 'ON_FAILURE'
        )
        print_check('railway.json has correct configuration', correct_config)
        if correct_config:
            checks_passed += 1
    except Exception as e:
        print_check('railway.json has correct configuration', False, f"Error: {e}")
    
    # Check 10: RAILWAY_SETUP.md exists and has content
    checks_total += 1
    if check_file_exists('RAILWAY_SETUP.md', 'RAILWAY_SETUP.md documentation exists'):
        checks_passed += 1
        
        checks_total += 1
        setup_content = Path('RAILWAY_SETUP.md').read_text()
        has_required_content = (
            'CELERY_BEAT_ENABLED' in setup_content and
            'Procfile.railway' in setup_content and
            'Quick Deploy' in setup_content
        )
        print_check('RAILWAY_SETUP.md has required content', has_required_content)
        if has_required_content:
            checks_passed += 1
    
    # Check 11: .dockerignore doesn't exclude training
    checks_total += 1
    dockerignore_content = Path('.dockerignore').read_text()
    lines = [line.strip() for line in dockerignore_content.split('\n') if line.strip()]
    exclusions = [line for line in lines if not line.startswith('#')]
    training_included = (
        'web/backend/training/' not in exclusions and
        'web/backend/training' not in exclusions
    )
    print_check('.dockerignore includes training modules', training_included)
    if training_included:
        checks_passed += 1
    
    # Print summary
    print_header("VERIFICATION SUMMARY")
    
    percentage = (checks_passed / checks_total * 100) if checks_total > 0 else 0
    print(f"Checks passed: {checks_passed}/{checks_total} ({percentage:.1f}%)")
    
    if checks_passed == checks_total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All checks passed! Ready for Railway deployment.{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Some checks failed. Please review and fix the issues above.{Colors.END}\n")
        print(f"{Colors.YELLOW}See RAILWAY_SETUP.md for deployment instructions.{Colors.END}")
        print(f"{Colors.YELLOW}See RAILWAY_FIX_VISUAL_COMPARISON.md for detailed changes.{Colors.END}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
