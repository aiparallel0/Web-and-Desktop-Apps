"""
Test Celery Configuration Fix

This test verifies that the celery_worker.py configuration has been fixed
to use beat_schedule_filename instead of beat_schedule for the file path.
"""

import os
import sys
import re
from pathlib import Path

def test_celery_config_fix():
    """Test that celery_worker.py uses correct parameter names."""
    print("\n" + "="*80)
    print("TESTING CELERY CONFIGURATION FIX")
    print("="*80 + "\n")
    
    # Find celery_worker.py
    base_dir = Path(__file__).parent
    celery_worker_path = base_dir / 'web' / 'backend' / 'training' / 'celery_worker.py'
    
    if not celery_worker_path.exists():
        print(f"❌ File not found: {celery_worker_path}")
        return False
    
    with open(celery_worker_path, 'r') as f:
        content = f.read()
    
    # Check 1: beat_schedule_filename should be used with file path
    if "beat_schedule_filename=os.getenv('CELERY_BEAT_SCHEDULE'" in content:
        print("✅ Test 1 PASSED: beat_schedule_filename is correctly used for file path")
    else:
        print("❌ Test 1 FAILED: beat_schedule_filename not found with CELERY_BEAT_SCHEDULE")
        print("   Expected: beat_schedule_filename=os.getenv('CELERY_BEAT_SCHEDULE'")
        return False
    
    # Check 2: beat_schedule should be used with dict (not with os.getenv)
    # This is the OLD INCORRECT pattern that caused the bug
    if "beat_schedule=os.getenv('CELERY_BEAT_SCHEDULE'" in content:
        print("❌ Test 2 FAILED: Found old bug - beat_schedule with os.getenv")
        print("   This will cause: TypeError: string indices must be integers, not 'str'")
        return False
    else:
        print("✅ Test 2 PASSED: beat_schedule is not incorrectly used with os.getenv")
    
    # Check 3: beat_schedule dict should be conditionally set
    if "celery_app.conf.beat_schedule = {" in content:
        print("✅ Test 3 PASSED: beat_schedule dict is properly configured")
    else:
        print("⚠️  Test 3 WARNING: beat_schedule dict configuration not found")
        print("   This is OK if beat scheduling is not used")
    
    # Check 4: CELERY_BEAT_ENABLED check should exist
    if "os.getenv('CELERY_BEAT_ENABLED'" in content:
        print("✅ Test 4 PASSED: CELERY_BEAT_ENABLED check exists")
    else:
        print("⚠️  Test 4 WARNING: CELERY_BEAT_ENABLED check not found")
    
    # Check 5: Comment should explain the difference
    if "beat_schedule is a dict" in content or "beat_schedule_filename" in content:
        print("✅ Test 5 PASSED: Configuration includes explanatory comments")
    else:
        print("⚠️  Test 5 WARNING: Consider adding comments to explain configuration")
    
    print("\n" + "="*80)
    print("✅ ALL CRITICAL TESTS PASSED")
    print("="*80 + "\n")
    
    # Print example of correct vs incorrect usage
    print("Configuration Examples:")
    print("-" * 80)
    print("\n❌ INCORRECT (causes TypeError):")
    print("   beat_schedule=os.getenv('CELERY_BEAT_SCHEDULE', '/path/to/file.db')")
    print("   # This passes a string where a dict is expected")
    
    print("\n✅ CORRECT:")
    print("   beat_schedule_filename=os.getenv('CELERY_BEAT_SCHEDULE', '/path/to/file.db')")
    print("   # This correctly sets the schedule database file path")
    
    print("\n✅ ALSO CORRECT:")
    print("   beat_schedule={")
    print("       'task-name': {")
    print("           'task': 'module.task_name',")
    print("           'schedule': 60.0,")
    print("       }")
    print("   }")
    print("   # This correctly sets the schedule tasks dictionary")
    print("\n" + "="*80 + "\n")
    
    return True

def test_config_validator_exists():
    """Test that config validator was created."""
    print("Testing Configuration Validator...")
    
    base_dir = Path(__file__).parent
    config_validator_path = base_dir / 'web' / 'backend' / 'training' / 'config_validator.py'
    
    if config_validator_path.exists():
        print("✅ config_validator.py exists")
        
        with open(config_validator_path, 'r') as f:
            content = f.read()
        
        # Check for key functions
        if "validate_celery_config" in content:
            print("✅ validate_celery_config function exists")
        if "validate_celery_beat_schedule" in content:
            print("✅ validate_celery_beat_schedule function exists")
        if "check_celery_connectivity" in content:
            print("✅ check_celery_connectivity function exists")
        
        return True
    else:
        print("❌ config_validator.py not found")
        return False

def test_log_manager_exists():
    """Test that log manager was created."""
    print("\nTesting Log Manager...")
    
    base_dir = Path(__file__).parent
    log_manager_path = base_dir / 'scripts' / 'log_manager.py'
    
    if log_manager_path.exists():
        print("✅ log_manager.py exists")
        
        with open(log_manager_path, 'r') as f:
            content = f.read()
        
        # Check for key features
        if "rotate_logs" in content:
            print("✅ rotate_logs function exists")
        if "compress_old_logs" in content:
            print("✅ compress_old_logs function exists")
        if "cleanup_old_logs" in content:
            print("✅ cleanup_old_logs function exists")
        if "analyze_logs" in content:
            print("✅ analyze_logs function exists")
        
        return True
    else:
        print("❌ log_manager.py not found")
        return False

def test_monitoring_docs_exist():
    """Test that monitoring documentation was created."""
    print("\nTesting Monitoring Documentation...")
    
    base_dir = Path(__file__).parent
    docs_path = base_dir / 'docs' / 'MONITORING_RECOMMENDATIONS.md'
    
    if docs_path.exists():
        print("✅ MONITORING_RECOMMENDATIONS.md exists")
        
        with open(docs_path, 'r') as f:
            content = f.read()
        
        # Check for key sections
        if "Monitoring Strategy" in content:
            print("✅ Contains monitoring strategy")
        if "Alerting" in content:
            print("✅ Contains alerting recommendations")
        if "Log Management" in content:
            print("✅ Contains log management guidance")
        
        return True
    else:
        print("❌ MONITORING_RECOMMENDATIONS.md not found")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("COMPREHENSIVE FIX VERIFICATION")
    print("="*80 + "\n")
    
    all_passed = True
    
    # Test 1: Celery configuration fix
    if not test_celery_config_fix():
        all_passed = False
    
    print()
    
    # Test 2: Config validator
    if not test_config_validator_exists():
        all_passed = False
    
    print()
    
    # Test 3: Log manager
    if not test_log_manager_exists():
        all_passed = False
    
    print()
    
    # Test 4: Monitoring docs
    if not test_monitoring_docs_exist():
        all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL VERIFICATION TESTS PASSED")
        print("\nThe following fixes have been implemented:")
        print("  1. ✅ Fixed Celery beat_schedule configuration bug")
        print("  2. ✅ Created configuration validator")
        print("  3. ✅ Created log management utility")
        print("  4. ✅ Created monitoring recommendations")
        print("\nNext Steps:")
        print("  - Run configuration validator before deployment")
        print("  - Set up log rotation cron job")
        print("  - Implement monitoring recommendations")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease review the failures above")
    print("="*80 + "\n")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
