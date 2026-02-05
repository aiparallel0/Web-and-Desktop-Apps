"""
=============================================================================
CELERY CONFIGURATION VALIDATOR
=============================================================================

Validates Celery configuration to prevent runtime errors.
Checks for common misconfigurations before starting workers.

Usage:
    from web.backend.training.config_validator import validate_celery_config
    
    errors = validate_celery_config()
    if errors:
        print("Configuration errors found:", errors)
        sys.exit(1)

=============================================================================
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def validate_celery_config() -> List[str]:
    """
    Validate Celery configuration for common issues.
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check Redis/Broker URL
    redis_url = os.getenv('REDIS_URL')
    broker_url = os.getenv('CELERY_BROKER_URL', redis_url)
    
    if not broker_url:
        errors.append("CELERY_BROKER_URL or REDIS_URL must be set")
    elif not broker_url.startswith(('redis://', 'amqp://', 'sqs://')):
        errors.append(f"Invalid CELERY_BROKER_URL format: {broker_url}")
    
    # Check Result Backend
    result_backend = os.getenv('CELERY_RESULT_BACKEND', redis_url)
    if not result_backend:
        errors.append("CELERY_RESULT_BACKEND or REDIS_URL must be set")
    
    # Check Beat Schedule Configuration
    beat_enabled = os.getenv('CELERY_BEAT_ENABLED', 'false').lower() in ('true', '1', 'yes')
    beat_schedule_path = os.getenv('CELERY_BEAT_SCHEDULE', '/app/celerybeat/schedule.db')
    
    if beat_enabled:
        # Ensure beat schedule path is writable
        schedule_dir = os.path.dirname(beat_schedule_path)
        if not os.path.exists(schedule_dir):
            try:
                os.makedirs(schedule_dir, exist_ok=True)
                logger.info(f"Created beat schedule directory: {schedule_dir}")
            except Exception as e:
                errors.append(f"Cannot create beat schedule directory {schedule_dir}: {e}")
        elif not os.access(schedule_dir, os.W_OK):
            errors.append(f"Beat schedule directory not writable: {schedule_dir}")
    
    # Validate environment-based configuration types
    try:
        poll_interval = int(os.getenv('TRAINING_POLL_INTERVAL', '30'))
        if poll_interval < 1 or poll_interval > 3600:
            errors.append(f"TRAINING_POLL_INTERVAL must be 1-3600 seconds, got: {poll_interval}")
    except ValueError:
        errors.append("TRAINING_POLL_INTERVAL must be an integer")
    
    try:
        max_polls = int(os.getenv('TRAINING_MAX_POLL_COUNT', '720'))
        if max_polls < 1:
            errors.append(f"TRAINING_MAX_POLL_COUNT must be positive, got: {max_polls}")
    except ValueError:
        errors.append("TRAINING_MAX_POLL_COUNT must be an integer")
    
    return errors


def validate_celery_beat_schedule(beat_schedule: Dict[str, Any]) -> List[str]:
    """
    Validate Celery beat schedule configuration.
    
    Args:
        beat_schedule: Dictionary of scheduled tasks
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    if not isinstance(beat_schedule, dict):
        errors.append(f"beat_schedule must be a dict, got {type(beat_schedule).__name__}")
        return errors
    
    for task_name, task_config in beat_schedule.items():
        if not isinstance(task_config, dict):
            errors.append(f"Task '{task_name}' config must be a dict, got {type(task_config).__name__}")
            continue
        
        # Check required fields
        if 'task' not in task_config:
            errors.append(f"Task '{task_name}' missing required field 'task'")
        
        if 'schedule' not in task_config:
            errors.append(f"Task '{task_name}' missing required field 'schedule'")
        else:
            schedule = task_config['schedule']
            # Validate schedule type (number for seconds, or crontab)
            if not isinstance(schedule, (int, float)):
                # Could be a crontab object, which is acceptable
                if not hasattr(schedule, '__class__') or 'crontab' not in schedule.__class__.__name__.lower():
                    errors.append(f"Task '{task_name}' schedule must be number (seconds) or crontab object")
    
    return errors


def check_celery_connectivity() -> Optional[str]:
    """
    Check if Celery broker is accessible.
    
    Returns:
        Error message if connection fails, None if successful
    """
    try:
        from shared.utils.optional_imports import OptionalImport
        
        celery_import = OptionalImport('celery.Celery', 'pip install celery redis')
        if not celery_import.is_available:
            return "Celery not installed"
        
        from celery import Celery
        
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        broker_url = os.getenv('CELERY_BROKER_URL', redis_url)
        
        # Create temporary app to test connection
        app = Celery('test', broker=broker_url)
        
        # Try to inspect broker
        inspect = app.control.inspect(timeout=5.0)
        if inspect is None:
            return "Cannot connect to Celery broker"
        
        # Ping workers (may be empty, that's OK)
        stats = inspect.stats()
        logger.info(f"Celery broker connected successfully. Active workers: {len(stats) if stats else 0}")
        
        return None
        
    except Exception as e:
        return f"Celery connectivity check failed: {e}"


def run_full_validation() -> bool:
    """
    Run full configuration validation.
    
    Returns:
        True if all validations pass, False otherwise
    """
    print("\n" + "="*80)
    print("CELERY CONFIGURATION VALIDATION")
    print("="*80 + "\n")
    
    # Configuration validation
    config_errors = validate_celery_config()
    
    if config_errors:
        print("❌ Configuration Errors:")
        for error in config_errors:
            print(f"   • {error}")
        print()
    else:
        print("✅ Configuration validation passed\n")
    
    # Connectivity check
    conn_error = check_celery_connectivity()
    if conn_error:
        print(f"⚠️  Connectivity Warning: {conn_error}\n")
    else:
        print("✅ Celery broker connectivity OK\n")
    
    # Summary
    total_errors = len(config_errors)
    if conn_error:
        total_errors += 1
    
    print("="*80)
    if total_errors == 0:
        print("✅ All validations passed")
    else:
        print(f"❌ {total_errors} issue(s) found")
    print("="*80 + "\n")
    
    return total_errors == 0


if __name__ == '__main__':
    import sys
    success = run_full_validation()
    sys.exit(0 if success else 1)
