"""
Analytics processing background tasks

Scheduled tasks for:
- Processing analytics events in batches
- Generating daily/weekly reports
- Cleaning up old analytics data
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
            module_id="web.backend.tasks.analytics_tasks",
            file_path=__file__,
            description="Background tasks for analytics processing",
            dependencies=["web.backend.analytics"],
            exports=["process_analytics_batch", "cleanup_old_analytics", "generate_daily_report"]
        ))
    except Exception:
        pass


def process_analytics_batch():
    """
    Process analytics events in batch
    
    This task could aggregate events, calculate metrics, etc.
    Currently a placeholder for future batch processing logic.
    """
    try:
        from web.backend.database import AnalyticsEvent, get_db_context
        
        logger.info("Processing analytics batch...")
        
        # Example: Count events in last 5 minutes
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        
        with get_db_context() as db:
            recent_count = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.created_at >= cutoff_time
            ).count()
        
        logger.info(f"Processed {recent_count} events in last 5 minutes")
        return recent_count
        
    except Exception as e:
        logger.error(f"Error processing analytics batch: {e}")
        return 0


def cleanup_old_analytics(days: int = 365):
    """
    Clean up analytics events older than N days
    
    Args:
        days: Number of days to keep analytics (default: 365)
    """
    try:
        from web.backend.database import AnalyticsEvent, get_db_context
        
        logger.info(f"Cleaning up analytics older than {days} days...")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with get_db_context() as db:
            deleted_count = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.created_at < cutoff_date
            ).delete()
            db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old analytics events")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up analytics: {e}")
        return 0


def generate_daily_report():
    """
    Generate daily analytics report
    
    Returns:
        Dictionary with daily metrics
    """
    try:
        from web.backend.database import AnalyticsEvent, User, get_db_context
        from web.backend.analytics.conversion_funnel import get_funnel_metrics
        
        logger.info("Generating daily analytics report...")
        
        # Get yesterday's date range
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        start_time = datetime.combine(yesterday, datetime.min.time())
        end_time = datetime.combine(yesterday, datetime.max.time())
        
        with get_db_context() as db:
            # Event counts
            total_events = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.created_at >= start_time,
                AnalyticsEvent.created_at <= end_time
            ).count()
            
            # New users
            new_users = db.query(User).filter(
                User.created_at >= start_time,
                User.created_at <= end_time
            ).count()
            
            # Active users (users who generated events)
            active_users = db.query(AnalyticsEvent.user_id).filter(
                AnalyticsEvent.created_at >= start_time,
                AnalyticsEvent.created_at <= end_time,
                AnalyticsEvent.user_id.isnot(None)
            ).distinct().count()
            
            # Get funnel metrics for yesterday
            funnel_metrics = get_funnel_metrics(days=1, db_session=db)
        
        report = {
            'date': yesterday.isoformat(),
            'total_events': total_events,
            'new_users': new_users,
            'active_users': active_users,
            'funnel_metrics': funnel_metrics
        }
        
        logger.info(f"Daily report generated: {report}")
        return report
        
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return {}


def calculate_user_engagement_score(user_id: str, days: int = 30):
    """
    Calculate engagement score for a user
    
    Args:
        user_id: User UUID
        days: Number of days to analyze (default: 30)
        
    Returns:
        Engagement score (0-100)
    """
    try:
        from web.backend.database import AnalyticsEvent, Receipt, get_db_context
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with get_db_context() as db:
            # Count events
            event_count = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.created_at >= cutoff_date
            ).count()
            
            # Count receipts processed
            receipt_count = db.query(Receipt).filter(
                Receipt.user_id == user_id,
                Receipt.created_at >= cutoff_date
            ).count()
            
            # Simple engagement score calculation
            # 1 point per event (max 50), 5 points per receipt (max 50)
            event_score = min(event_count, 50)
            receipt_score = min(receipt_count * 5, 50)
            
            total_score = event_score + receipt_score
        
        logger.debug(f"User {user_id} engagement score: {total_score}")
        return total_score
        
    except Exception as e:
        logger.error(f"Error calculating engagement score: {e}")
        return 0


__all__ = [
    'process_analytics_batch',
    'cleanup_old_analytics',
    'generate_daily_report',
    'calculate_user_engagement_score'
]
