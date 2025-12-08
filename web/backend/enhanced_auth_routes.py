"""
Enhanced Authentication Routes

Includes email verification, trial management, and referral tracking.
"""
import logging
import secrets
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, redirect
import uuid

from shared.utils.telemetry import get_tracer, set_span_attributes
from shared.utils.validation import validate_json_body
from web.backend.security.rate_limiting import rate_limit
from web.backend.decorators import require_auth

logger = logging.getLogger(__name__)

# Create Blueprint
enhanced_auth_bp = Blueprint('enhanced_auth', __name__, url_prefix='/api/auth')

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


@enhanced_auth_bp.route('/verify-email', methods=['GET'])
@rate_limit(requests=10, window=3600, error_message="Too many verification attempts")
def verify_email():
    """
    Verify user email using token from verification email.
    
    Query params:
        token: Email verification token
        
    Returns:
        Redirect to dashboard with success message
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("auth.verify_email") as span:
        try:
            token = request.args.get('token')
            if not token:
                return jsonify({'success': False, 'error': 'Verification token required'}), 400
            
            set_span_attributes(span, {
                "operation.type": "email_verification"
            })
            
            User = _get_models()
            
            with _get_db_context()() as db:
                # Find user with this verification token
                user = db.query(User).filter(
                    User.email_verification_token == token
                ).first()
                
                if not user:
                    logger.warning(f"Invalid verification token: {token[:10]}...")
                    return jsonify({'success': False, 'error': 'Invalid verification token'}), 400
                
                # Check if already verified
                if user.email_verified:
                    logger.info(f"Email already verified for user {user.id}")
                    return redirect('/dashboard.html?verified=already')
                
                # Verify email
                user.email_verified = True
                user.email_verification_token = None  # Clear token
                
                # Activate 14-day Pro trial
                from web.backend.trial_service import activate_trial
                trial_activated = activate_trial(user)
                
                # Generate referral code if not exists
                if not user.referral_code:
                    from web.backend.referral_service import generate_referral_code
                    user.referral_code = generate_referral_code(str(user.id))
                
                db.commit()
                
                set_span_attributes(span, {
                    "verification.success": True,
                    "trial.activated": trial_activated
                })
                
                logger.info(f"Email verified for user {user.id}, trial activated: {trial_activated}")
                
                # Send welcome email
                try:
                    from web.backend.email_service import get_email_service
                    email_service = get_email_service()
                    trial_end = user.trial_end_date.strftime('%B %d, %Y') if user.trial_end_date else 'N/A'
                    email_service.send_welcome_email(
                        user.email,
                        user.full_name or 'there',
                        user.referral_code,
                        trial_end
                    )
                except Exception as e:
                    logger.error(f"Failed to send welcome email: {e}")
                
                # Check if referred by someone
                referral_code = request.args.get('ref')
                if referral_code:
                    try:
                        from web.backend.referral_service import track_referral
                        track_referral(db, referral_code, str(user.id))
                    except Exception as e:
                        logger.error(f"Failed to track referral: {e}")
                
                # Redirect to dashboard
                return redirect('/dashboard.html?verified=true&trial=activated')
                
        except Exception as e:
            logger.error(f"Email verification error: {e}", exc_info=True)
            span.record_exception(e)
            return jsonify({'success': False, 'error': 'Verification failed'}), 500


@enhanced_auth_bp.route('/resend-verification', methods=['POST'])
@require_auth
@rate_limit(requests=3, window=3600, error_message="Too many resend attempts")
def resend_verification():
    """
    Resend verification email to user.
    
    Returns:
        200: Verification email sent
        400: Already verified or error
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("auth.resend_verification") as span:
        try:
            from flask import g
            user_id = g.user_id
            
            User = _get_models()
            
            with _get_db_context()() as db:
                user = db.query(User).filter(User.id == user_id).first()
                
                if not user:
                    return jsonify({'success': False, 'error': 'User not found'}), 404
                
                if user.email_verified:
                    return jsonify({'success': False, 'error': 'Email already verified'}), 400
                
                # Generate new verification token
                verification_token = secrets.token_urlsafe(32)
                user.email_verification_token = verification_token
                db.commit()
                
                # Send verification email
                from web.backend.email_service import get_email_service
                email_service = get_email_service()
                success = email_service.send_verification_email(
                    user.email,
                    user.full_name or 'there',
                    verification_token
                )
                
                if success:
                    logger.info(f"Verification email resent to user {user.id}")
                    return jsonify({
                        'success': True,
                        'message': 'Verification email sent'
                    }), 200
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to send verification email'
                    }), 500
                
        except Exception as e:
            logger.error(f"Resend verification error: {e}", exc_info=True)
            span.record_exception(e)
            return jsonify({'success': False, 'error': 'Failed to resend verification'}), 500


@enhanced_auth_bp.route('/trial-status', methods=['GET'])
@require_auth
def trial_status():
    """
    Get trial status for authenticated user.
    
    Returns:
        200: Trial status information
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("auth.trial_status") as span:
        try:
            from flask import g
            user_id = g.user_id
            
            User = _get_models()
            
            with _get_db_context()() as db:
                user = db.query(User).filter(User.id == user_id).first()
                
                if not user:
                    return jsonify({'success': False, 'error': 'User not found'}), 404
                
                from web.backend.trial_service import check_trial_status
                status = check_trial_status(user)
                
                return jsonify({
                    'success': True,
                    'trial': status
                }), 200
                
        except Exception as e:
            logger.error(f"Trial status error: {e}", exc_info=True)
            span.record_exception(e)
            return jsonify({'success': False, 'error': 'Failed to get trial status'}), 500


@enhanced_auth_bp.route('/referral-stats', methods=['GET'])
@require_auth
def referral_stats():
    """
    Get referral statistics for authenticated user.
    
    Returns:
        200: Referral statistics
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("auth.referral_stats") as span:
        try:
            from flask import g
            user_id = g.user_id
            
            with _get_db_context()() as db:
                from web.backend.referral_service import get_referral_service
                service = get_referral_service()
                stats = service.get_referral_stats(db, user_id)
                
                return jsonify({
                    'success': True,
                    'referrals': stats
                }), 200
                
        except Exception as e:
            logger.error(f"Referral stats error: {e}", exc_info=True)
            span.record_exception(e)
            return jsonify({'success': False, 'error': 'Failed to get referral stats'}), 500


def register_enhanced_auth_routes(app):
    """Register enhanced auth routes with Flask app."""
    app.register_blueprint(enhanced_auth_bp)
    logger.info("Enhanced auth routes registered")
