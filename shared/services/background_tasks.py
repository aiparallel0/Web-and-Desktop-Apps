"""
=============================================================================
BACKGROUND TASKS - Celery Worker Module
=============================================================================

Provides Celery task definitions for background job processing.
This module is referenced by docker-compose for the celery-worker service.

Environment Variables:
- REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
- CELERY_BROKER_URL: Celery broker URL (defaults to REDIS_URL)
- CELERY_RESULT_BACKEND: Result backend URL (defaults to REDIS_URL)

Usage:
    # Start worker:
    celery -A shared.services.background_tasks worker --loglevel=info
    
    # Submit task from code:
    from shared.services.background_tasks import example_task
    result = example_task.delay(arg1, arg2)

=============================================================================
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from shared.utils.optional_imports import OptionalImport

logger = logging.getLogger(__name__)

# Redis/Celery configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

# Import Celery
celery_import = OptionalImport('celery.Celery', 'pip install celery redis')
Celery = celery_import.module
CELERY_AVAILABLE = celery_import.is_available

# Initialize Celery app (if available)
if CELERY_AVAILABLE:
    celery_app = Celery(
        'background_tasks',
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND
    )
    
    # Celery configuration
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1 hour max per task
        task_soft_time_limit=3300,  # 55 minutes soft limit
        worker_prefetch_multiplier=1,  # One task at a time per worker
        task_acks_late=True,  # Acknowledge after completion
        task_reject_on_worker_lost=True,
        result_expires=86400,  # Results expire after 24 hours
        # Beat scheduler configuration
        beat_schedule_filename=os.getenv('CELERY_BEAT_SCHEDULE', '/tmp/celerybeat-schedule.db'),
    )
    
    logger.info(f"Celery initialized with broker: {CELERY_BROKER_URL}")
else:
    celery_app = None
    logger.warning("Celery not available - background tasks disabled")

# =============================================================================
# CELERY TASKS
# =============================================================================

if CELERY_AVAILABLE:
    
    @celery_app.task(bind=True, name='background.process_email')
    def process_email_task(
        self,
        email_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process and send an email.
        
        Args:
            email_data: Dictionary containing email details (to, subject, body, etc.)
            
        Returns:
            Dictionary with processing result
        """
        try:
            from web.backend.email_service import EmailService
            
            email_service = EmailService()
            success = email_service.send_email(
                to=email_data.get('to'),
                subject=email_data.get('subject'),
                body=email_data.get('body'),
                html=email_data.get('html')
            )
            
            return {
                'success': success,
                'email': email_data.get('to'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Email processing failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @celery_app.task(bind=True, name='background.process_analytics')
    def process_analytics_task(
        self,
        analytics_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process analytics data.
        
        Args:
            analytics_data: Dictionary containing analytics event data
            
        Returns:
            Dictionary with processing result
        """
        try:
            from web.backend.analytics_routes import process_analytics_event
            
            result = process_analytics_event(analytics_data)
            
            return {
                'success': True,
                'event': analytics_data.get('event_type'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Analytics processing failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @celery_app.task(bind=True, name='background.cleanup_temp_files')
    def cleanup_temp_files_task(
        self,
        max_age_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Clean up temporary files older than specified age.
        
        Args:
            max_age_hours: Maximum age of temp files to keep
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            import os
            import time
            from pathlib import Path
            
            temp_dir = Path('/tmp')
            cutoff_time = time.time() - (max_age_hours * 3600)
            cleaned_count = 0
            
            # Clean up old temp files
            for temp_file in temp_dir.glob('receipt_*'):
                try:
                    if temp_file.stat().st_mtime < cutoff_time:
                        temp_file.unlink()
                        cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Failed to clean {temp_file}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} temporary files")
            
            return {
                'success': True,
                'cleaned_count': cleaned_count,
                'max_age_hours': max_age_hours,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @celery_app.task(bind=True, name='background.example_task')
    def example_task(
        self,
        arg1: str,
        arg2: int = 0
    ) -> Dict[str, Any]:
        """
        Example task for testing.
        
        Args:
            arg1: First argument
            arg2: Second argument (optional)
            
        Returns:
            Dictionary with task result
        """
        logger.info(f"Running example task with args: {arg1}, {arg2}")
        
        # Simulate some work
        import time
        time.sleep(1)
        
        return {
            'success': True,
            'result': f"Processed {arg1} with value {arg2}",
            'timestamp': datetime.utcnow().isoformat()
        }

# =============================================================================
# CELERY BEAT SCHEDULE
# =============================================================================

def configure_beat_schedule():
    """
    Configure Celery Beat schedule for periodic tasks.
    Call this before starting beat: python -c "from shared.services.background_tasks import configure_beat_schedule; configure_beat_schedule()"
    """
    if not celery_app:
        logger.warning("Celery not available - cannot configure beat schedule")
        return
    
    celery_app.conf.beat_schedule = {
        'cleanup-temp-files-daily': {
            'task': 'background.cleanup_temp_files',
            'schedule': 86400.0,  # Run every 24 hours
            'args': (24,)  # Clean files older than 24 hours
        },
    }
    
    logger.info("Celery Beat schedule configured")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_celery_app():
    """Get the Celery app instance."""
    return celery_app

def is_celery_available() -> bool:
    """Check if Celery is available."""
    return CELERY_AVAILABLE and celery_app is not None

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'celery_app',
    'get_celery_app',
    'is_celery_available',
    'configure_beat_schedule',
    'process_email_task',
    'process_analytics_task',
    'cleanup_temp_files_task',
    'example_task',
]
