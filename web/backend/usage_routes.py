"""
Usage Tracking Routes

Provides API endpoints for usage statistics and limits.
"""
import logging
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify
from calendar import monthrange

from shared.utils.telemetry import get_tracer, set_span_attributes
from web.backend.decorators import require_auth
from web.backend.billing.plans import get_plan_features

logger = logging.getLogger(__name__)

# Create Blueprint
usage_bp = Blueprint('usage', __name__, url_prefix='/api/usage')

# Lazy imports
_db_context = None
_User = None


def _get_db_context():
    """Lazy import of database context."""
    global _db_context
    if _db_context is None:
        from web.backend.database import get_db_context
        _db_context = get_db_context
    return _db_context


def _get_models():
    """Lazy import of database models."""
    global _User
    if _User is None:
        from web.backend.database import User
        _User = User
    return _User


@usage_bp.route('/stats', methods=['GET'])
@require_auth
def usage_stats():
    """
    Get usage statistics for authenticated user.
    
    Returns:
        200: Usage statistics including receipts processed, storage used, and limits
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("usage.stats") as span:
        try:
            from flask import g
            user_id = g.user_id
            
            User = _get_models()
            
            with _get_db_context()() as db:
                user = db.query(User).filter(User.id == user_id).first()
                
                if not user:
                    return jsonify({'success': False, 'error': 'User not found'}), 404
                
                # Get plan features
                plan_name = user.plan.value if hasattr(user.plan, 'value') else str(user.plan)
                features = get_plan_features(plan_name)
                
                # Calculate usage
                receipts_processed = user.receipts_processed_month or 0
                receipts_limit = features.get('receipts_per_month', 10)
                if receipts_limit == 'unlimited':
                    receipts_limit = 999999  # Large number for unlimited
                
                storage_used = user.storage_used_bytes or 0
                storage_limit_gb = features.get('storage_gb', 0.1)
                storage_limit_bytes = int(storage_limit_gb * 1024 * 1024 * 1024)
                
                # Calculate reset date (1st of next month)
                now = datetime.utcnow()
                if now.month == 12:
                    next_month = datetime(now.year + 1, 1, 1)
                else:
                    next_month = datetime(now.year, now.month + 1, 1)
                reset_date = next_month.strftime('%B 1, %Y')
                
                # Calculate usage percentages
                receipts_percentage = min(100, int((receipts_processed / receipts_limit) * 100))
                storage_percentage = min(100, int((storage_used / storage_limit_bytes) * 100))
                
                set_span_attributes(span, {
                    "user.plan": plan_name,
                    "usage.receipts_percentage": receipts_percentage,
                    "usage.storage_percentage": storage_percentage
                })
                
                return jsonify({
                    'success': True,
                    'usage': {
                        'receipts_processed': receipts_processed,
                        'receipts_limit': receipts_limit,
                        'receipts_percentage': receipts_percentage,
                        'storage_used': storage_used,
                        'storage_limit': storage_limit_bytes,
                        'storage_percentage': storage_percentage,
                        'plan': plan_name,
                        'reset_date': reset_date
                    }
                }), 200
                
        except Exception as e:
            logger.error(f"Usage stats error: {e}", exc_info=True)
            span.record_exception(e)
            return jsonify({'success': False, 'error': 'Failed to get usage stats'}), 500


@usage_bp.route('/check-limit', methods=['POST'])
@require_auth
def check_usage_limit():
    """
    Check if user can process more receipts based on their plan limit.
    
    Request body:
        {
            "count": 1  # Number of receipts to check
        }
        
    Returns:
        200: Limit check result with can_proceed boolean
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("usage.check_limit") as span:
        try:
            from flask import g
            user_id = g.user_id
            
            data = request.get_json() or {}
            count = data.get('count', 1)
            
            User = _get_models()
            
            with _get_db_context()() as db:
                user = db.query(User).filter(User.id == user_id).first()
                
                if not user:
                    return jsonify({'success': False, 'error': 'User not found'}), 404
                
                # Get plan features
                plan_name = user.plan.value if hasattr(user.plan, 'value') else str(user.plan)
                features = get_plan_features(plan_name)
                
                receipts_processed = user.receipts_processed_month or 0
                receipts_limit = features.get('receipts_per_month', 10)
                
                # Unlimited plans can always proceed
                if receipts_limit == 'unlimited':
                    return jsonify({
                        'success': True,
                        'can_proceed': True,
                        'remaining': 999999,
                        'plan': plan_name
                    }), 200
                
                # Check if user has capacity
                remaining = receipts_limit - receipts_processed
                can_proceed = remaining >= count
                
                # Calculate usage percentage
                usage_percentage = min(100, int((receipts_processed / receipts_limit) * 100))
                
                set_span_attributes(span, {
                    "user.plan": plan_name,
                    "usage.can_proceed": can_proceed,
                    "usage.percentage": usage_percentage
                })
                
                # Determine if we should send usage alert
                should_alert = False
                alert_threshold = None
                if usage_percentage >= 90 and not hasattr(user, '_alert_90_sent'):
                    should_alert = True
                    alert_threshold = 90
                elif usage_percentage >= 75 and not hasattr(user, '_alert_75_sent'):
                    should_alert = True
                    alert_threshold = 75
                
                # Send usage alert if needed (async)
                if should_alert:
                    try:
                        from web.backend.email_service import get_email_service
                        email_service = get_email_service()
                        
                        # Calculate reset date
                        now = datetime.utcnow()
                        if now.month == 12:
                            next_month = datetime(now.year + 1, 1, 1)
                        else:
                            next_month = datetime(now.year, now.month + 1, 1)
                        reset_date = next_month.strftime('%B 1, %Y')
                        
                        email_service.send_usage_alert(
                            user.email,
                            user.full_name or 'there',
                            receipts_processed,
                            receipts_limit,
                            plan_name,
                            reset_date
                        )
                        
                        # Mark as sent (in-memory flag, would be DB flag in production)
                        setattr(user, f'_alert_{alert_threshold}_sent', True)
                    except Exception as e:
                        logger.error(f"Failed to send usage alert: {e}")
                
                return jsonify({
                    'success': True,
                    'can_proceed': can_proceed,
                    'remaining': remaining,
                    'processed': receipts_processed,
                    'limit': receipts_limit,
                    'percentage': usage_percentage,
                    'plan': plan_name,
                    'message': 'Limit reached. Please upgrade your plan.' if not can_proceed else None
                }), 200
                
        except Exception as e:
            logger.error(f"Check limit error: {e}", exc_info=True)
            span.record_exception(e)
            return jsonify({'success': False, 'error': 'Failed to check usage limit'}), 500


def register_usage_routes(app):
    """Register usage routes with Flask app."""
    app.register_blueprint(usage_bp)
    logger.info("Usage routes registered")
