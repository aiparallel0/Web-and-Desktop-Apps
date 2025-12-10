"""
Marketing API routes

Provides endpoints for:
- Event tracking
- Email preferences
- Campaign management (admin only)
"""
import logging
from flask import Blueprint, request, jsonify, g
from datetime import datetime
from typing import Dict, Any, Optional

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
            module_id="web.backend.marketing.routes",
            file_path=__file__,
            description="Marketing API routes for event tracking and email management",
            dependencies=["web.backend.database", "web.backend.analytics", "web.backend.marketing"],
            exports=["marketing_bp"]
        ))
    except Exception:
        pass

# Create Blueprint
marketing_bp = Blueprint('marketing', __name__, url_prefix='/api/marketing')


@marketing_bp.route('/track-event', methods=['POST'])
def track_event():
    """
    Track an analytics event
    
    Expected payload:
    {
        "event": "receipt_uploaded",
        "properties": {
            "model_id": "ocr_tesseract",
            "processing_time": 1.5
        },
        "user_id": "user_uuid" (optional),
        "session_id": "session_123" (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'event' not in data:
            return jsonify({'success': False, 'error': 'Event name required'}), 400
        
        # Get tracker
        from web.backend.analytics.tracker import get_tracker
        tracker = get_tracker()
        
        # Track event
        success = tracker.track(
            event_name=data['event'],
            properties=data.get('properties', {}),
            user_id=data.get('user_id'),
            session_id=data.get('session_id', request.headers.get('X-Session-Id'))
        )
        
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to track event'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@marketing_bp.route('/email/subscribe', methods=['POST'])
def subscribe_to_emails():
    """
    Subscribe user to email sequence
    
    Expected payload:
    {
        "user_id": "user_uuid",
        "sequence_type": "welcome"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data or 'sequence_type' not in data:
            return jsonify({'success': False, 'error': 'user_id and sequence_type required'}), 400
        
        from web.backend.marketing.automation import enroll_user_in_sequence
        from web.backend.database import get_db_context
        
        with get_db_context() as db:
            success = enroll_user_in_sequence(
                user_id=data['user_id'],
                sequence_type=data['sequence_type'],
                db_session=db
            )
        
        if success:
            return jsonify({'success': True, 'message': 'Subscribed to email sequence'}), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to subscribe'}), 500
            
    except Exception as e:
        logger.error(f"Error subscribing to emails: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@marketing_bp.route('/email/unsubscribe', methods=['POST'])
def unsubscribe_from_emails():
    """
    Unsubscribe user from email sequence
    
    Expected payload:
    {
        "user_id": "user_uuid",
        "sequence_type": "welcome"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data or 'sequence_type' not in data:
            return jsonify({'success': False, 'error': 'user_id and sequence_type required'}), 400
        
        from web.backend.marketing.automation import unenroll_user_from_sequence
        from web.backend.database import get_db_context
        
        with get_db_context() as db:
            success = unenroll_user_from_sequence(
                user_id=data['user_id'],
                sequence_type=data['sequence_type'],
                db_session=db
            )
        
        if success:
            return jsonify({'success': True, 'message': 'Unsubscribed from email sequence'}), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to unsubscribe'}), 500
            
    except Exception as e:
        logger.error(f"Error unsubscribing from emails: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@marketing_bp.route('/email/preferences', methods=['GET'])
def get_email_preferences():
    """
    Get user's email preferences
    
    Query params:
    - user_id: User UUID
    """
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'user_id required'}), 400
        
        from web.backend.database import EmailSequence, get_db_context
        
        with get_db_context() as db:
            sequences = db.query(EmailSequence).filter(
                EmailSequence.user_id == user_id,
                EmailSequence.completed_at.is_(None)
            ).all()
            
            preferences = []
            for seq in sequences:
                seq_name = seq.sequence_name.value if hasattr(seq.sequence_name, 'value') else seq.sequence_name
                preferences.append({
                    'sequence_type': seq_name,
                    'current_step': seq.current_step,
                    'started_at': seq.started_at.isoformat(),
                    'paused': seq.paused,
                    'unsubscribed': seq.unsubscribed
                })
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'preferences': preferences
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting email preferences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@marketing_bp.route('/email/preferences', methods=['PUT'])
def update_email_preferences():
    """
    Update user's email preferences
    
    Expected payload:
    {
        "user_id": "user_uuid",
        "sequence_type": "welcome",
        "paused": true
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data or 'sequence_type' not in data:
            return jsonify({'success': False, 'error': 'user_id and sequence_type required'}), 400
        
        from web.backend.database import EmailSequence, EmailSequenceType, get_db_context
        
        with get_db_context() as db:
            sequence = db.query(EmailSequence).filter(
                EmailSequence.user_id == data['user_id'],
                EmailSequence.sequence_name == EmailSequenceType(data['sequence_type']),
                EmailSequence.completed_at.is_(None)
            ).first()
            
            if not sequence:
                return jsonify({'success': False, 'error': 'Sequence not found'}), 404
            
            # Update preferences
            if 'paused' in data:
                sequence.paused = data['paused']
            if 'unsubscribed' in data:
                sequence.unsubscribed = data['unsubscribed']
                if data['unsubscribed']:
                    sequence.completed_at = datetime.utcnow()
            
            db.commit()
        
        return jsonify({'success': True, 'message': 'Preferences updated'}), 200
        
    except Exception as e:
        logger.error(f"Error updating email preferences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Admin routes (require admin authentication)
@marketing_bp.route('/admin/analytics/dashboard', methods=['GET'])
def get_analytics_dashboard():
    """
    Get analytics dashboard data (admin only)
    
    Query params:
    - days: Number of days to analyze (default: 30)
    """
    try:
        # TODO: Add admin authentication check
        # if not g.user.is_admin:
        #     return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        days = int(request.args.get('days', 30))
        
        from web.backend.analytics.conversion_funnel import get_funnel_metrics
        from web.backend.database import get_db_context
        
        with get_db_context() as db:
            metrics = get_funnel_metrics(days=days, db_session=db)
        
        return jsonify({
            'success': True,
            'data': metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@marketing_bp.route('/admin/campaigns', methods=['GET'])
def list_campaigns():
    """
    List all email campaigns (admin only)
    """
    try:
        # TODO: Add admin authentication check
        
        from web.backend.marketing.email_sequences import get_all_sequences
        
        sequences = get_all_sequences()
        campaigns = []
        
        for seq in sequences:
            campaigns.append({
                'sequence_type': seq.sequence_type,
                'sequence_name': seq.sequence_name,
                'description': seq.description,
                'total_steps': seq.total_steps(),
                'steps': [
                    {
                        'step_number': step.step_number,
                        'delay_days': step.delay_days,
                        'subject': step.subject,
                        'description': step.description
                    }
                    for step in seq.steps
                ]
            })
        
        return jsonify({
            'success': True,
            'campaigns': campaigns
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@marketing_bp.route('/admin/send-campaign', methods=['POST'])
def send_campaign():
    """
    Send email campaign manually (admin only)
    
    Expected payload:
    {
        "user_ids": ["user_uuid1", "user_uuid2"],
        "template_name": "welcome_day0.html",
        "subject": "Welcome!",
        "test_mode": false
    }
    """
    try:
        # TODO: Add admin authentication check
        
        data = request.get_json()
        
        if not data or 'user_ids' not in data or 'template_name' not in data:
            return jsonify({'success': False, 'error': 'user_ids and template_name required'}), 400
        
        from web.backend.marketing.email_sender import get_email_sender
        from web.backend.marketing.automation import load_email_template, render_email_template
        from web.backend.database import User, get_db_context
        
        # Load template
        template_html = load_email_template(data['template_name'])
        email_sender = get_email_sender()
        
        sent_count = 0
        errors = []
        
        with get_db_context() as db:
            for user_id in data['user_ids']:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    errors.append(f"User {user_id} not found")
                    continue
                
                # Render template
                context = {
                    'user_name': user.full_name or user.email.split('@')[0],
                    'user_email': user.email,
                    'company_name': user.company or '',
                    'current_plan': user.plan.value if hasattr(user.plan, 'value') else user.plan,
                    'unsubscribe_link': f"https://yourdomain.com/unsubscribe?user={user_id}"
                }
                
                rendered_html = render_email_template(template_html, context)
                
                # Send email
                if not data.get('test_mode', False):
                    result = email_sender.send_email(
                        to_email=user.email,
                        subject=data.get('subject', 'Email from Receipt Extractor'),
                        html_content=rendered_html,
                        tracking_enabled=True
                    )
                    
                    if result.get('success'):
                        sent_count += 1
                    else:
                        errors.append(f"Failed to send to {user.email}: {result.get('error')}")
                else:
                    # Test mode - just log
                    logger.info(f"[TEST MODE] Would send email to {user.email}")
                    sent_count += 1
        
        return jsonify({
            'success': True,
            'sent_count': sent_count,
            'errors': errors,
            'test_mode': data.get('test_mode', False)
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending campaign: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


__all__ = ['marketing_bp']
