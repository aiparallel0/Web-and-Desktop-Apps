"""
Email sending background tasks

Scheduled tasks for:
- Sending due emails in sequences
- Cleaning up old email logs
- Reporting email metrics
"""
import logging
from datetime import datetime, timedelta

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
            module_id="web.backend.tasks.email_tasks",
            file_path=__file__,
            description="Background tasks for email sending and management",
            dependencies=["web.backend.marketing.automation"],
            exports=["send_due_emails", "cleanup_old_email_logs"]
        ))
    except Exception:
        pass


def send_due_emails():
    """
    Send all due emails in active sequences
    
    This task should run hourly via cron or APScheduler
    """
    try:
        from web.backend.marketing.automation import process_due_emails
        from web.backend.database import get_db_context
        
        logger.info("Starting email sending task...")
        
        with get_db_context() as db:
            sent_count = process_due_emails(db)
        
        logger.info(f"Email sending task completed. Sent {sent_count} emails.")
        return sent_count
        
    except Exception as e:
        logger.error(f"Error in send_due_emails task: {e}")
        return 0


def cleanup_old_email_logs(days: int = 90):
    """
    Clean up email logs older than N days
    
    Args:
        days: Number of days to keep logs (default: 90)
    """
    try:
        from web.backend.database import EmailLog, get_db_context
        
        logger.info(f"Cleaning up email logs older than {days} days...")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with get_db_context() as db:
            deleted_count = db.query(EmailLog).filter(
                EmailLog.sent_at < cutoff_date
            ).delete()
            db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old email logs")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up email logs: {e}")
        return 0


def generate_email_report(days: int = 7):
    """
    Generate email performance report
    
    Args:
        days: Number of days to report on (default: 7)
        
    Returns:
        Dictionary with email metrics
    """
    try:
        from web.backend.database import EmailLog, get_db_context
        
        logger.info(f"Generating email report for last {days} days...")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with get_db_context() as db:
            # Total sent
            total_sent = db.query(EmailLog).filter(
                EmailLog.sent_at >= cutoff_date
            ).count()
            
            # Opened
            total_opened = db.query(EmailLog).filter(
                EmailLog.sent_at >= cutoff_date,
                EmailLog.opened_at.isnot(None)
            ).count()
            
            # Clicked
            total_clicked = db.query(EmailLog).filter(
                EmailLog.sent_at >= cutoff_date,
                EmailLog.clicked_at.isnot(None)
            ).count()
            
            # Bounced
            total_bounced = db.query(EmailLog).filter(
                EmailLog.sent_at >= cutoff_date,
                EmailLog.bounced_at.isnot(None)
            ).count()
        
        report = {
            'period_days': days,
            'total_sent': total_sent,
            'total_opened': total_opened,
            'total_clicked': total_clicked,
            'total_bounced': total_bounced,
            'open_rate': round((total_opened / total_sent * 100) if total_sent > 0 else 0, 2),
            'click_rate': round((total_clicked / total_sent * 100) if total_sent > 0 else 0, 2),
            'bounce_rate': round((total_bounced / total_sent * 100) if total_sent > 0 else 0, 2)
        }
        
        logger.info(f"Email report: {report}")
        return report
        
    except Exception as e:
        logger.error(f"Error generating email report: {e}")
        return {}


__all__ = [
    'send_due_emails',
    'cleanup_old_email_logs',
    'generate_email_report'
]
