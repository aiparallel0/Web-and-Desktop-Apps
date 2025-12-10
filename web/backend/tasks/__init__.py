"""
Background tasks module

Provides task scheduling for:
- Email sending
- Analytics processing
- Scheduled reports
"""
import os
import logging
from typing import Optional

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.tasks",
            file_path=__file__,
            description="Background tasks for email and analytics processing",
            dependencies=[],
            exports=["setup_scheduler", "email_tasks", "analytics_tasks"]
        ))
    except Exception:
        pass


def setup_scheduler():
    """
    Setup task scheduler
    
    Uses APScheduler for simpler setup than Celery.
    For production, consider using Celery with Redis for distributed task queue.
    
    Returns:
        Scheduler instance
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = BackgroundScheduler()
        
        # Import tasks
        from .email_tasks import send_due_emails
        from .analytics_tasks import process_analytics_batch
        
        # Schedule email sending (hourly)
        scheduler.add_job(
            send_due_emails,
            trigger=CronTrigger(minute=0),  # Every hour at minute 0
            id='send_due_emails',
            name='Send due emails',
            replace_existing=True
        )
        
        # Schedule analytics processing (every 5 minutes)
        scheduler.add_job(
            process_analytics_batch,
            trigger=CronTrigger(minute='*/5'),  # Every 5 minutes
            id='process_analytics',
            name='Process analytics batch',
            replace_existing=True
        )
        
        logger.info("Task scheduler configured successfully")
        return scheduler
        
    except ImportError as e:
        logger.warning(f"APScheduler not available: {e}")
        logger.warning("Install with: pip install apscheduler")
        return None


def start_scheduler():
    """
    Start the background task scheduler
    """
    if os.getenv('ENABLE_EMAIL_AUTOMATION', 'false').lower() != 'true':
        logger.info("Email automation disabled, skipping scheduler")
        return None
    
    scheduler = setup_scheduler()
    if scheduler:
        scheduler.start()
        logger.info("Background task scheduler started")
        return scheduler
    else:
        logger.warning("Failed to start scheduler")
        return None


__all__ = [
    'setup_scheduler',
    'start_scheduler'
]
