"""
Marketing automation workflows

Trigger-based automation for:
- User signup → Welcome series
- Trial start → Trial conversion series
- Subscription → Onboarding series
- Inactivity → Re-engagement series
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.marketing.automation",
            file_path=__file__,
            description="Marketing automation workflows and triggers",
            dependencies=["web.backend.database", "web.backend.marketing.email_sequences", 
                         "web.backend.marketing.email_sender"],
            exports=["enroll_user_in_sequence", "process_due_emails", "trigger_signup_automation",
                    "trigger_trial_automation", "trigger_subscription_automation"]
        ))
    except Exception:
        pass

def enroll_user_in_sequence(user_id: str, sequence_type: str, db_session) -> bool:
    """
    Enroll a user in an email sequence
    
    Args:
        user_id: User UUID
        sequence_type: Type of sequence (welcome, trial_conversion, etc.)
        db_session: Database session
        
    Returns:
        True if enrolled successfully, False otherwise
    """
    try:
        from web.backend.database import EmailSequence, EmailSequenceType, User
        
        # Check if user exists
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            return False
        
        # Check if already enrolled in this sequence
        existing = db_session.query(EmailSequence).filter(
            EmailSequence.user_id == user_id,
            EmailSequence.sequence_name == EmailSequenceType(sequence_type),
            EmailSequence.completed_at.is_(None)
        ).first()
        
        if existing:
            logger.info(f"User {user_id} already enrolled in {sequence_type}")
            return False
        
        # Create new sequence enrollment
        sequence = EmailSequence(
            user_id=user_id,
            sequence_name=EmailSequenceType(sequence_type),
            current_step=0,
            started_at=datetime.utcnow(),
            paused=False,
            unsubscribed=False
        )
        
        db_session.add(sequence)
        db_session.commit()
        
        logger.info(f"Enrolled user {user_id} in {sequence_type} sequence")
        return True
        
    except Exception as e:
        logger.error(f"Failed to enroll user in sequence: {e}")
        db_session.rollback()
        return False

def unenroll_user_from_sequence(user_id: str, sequence_type: str, db_session) -> bool:
    """
    Unenroll a user from an email sequence
    
    Args:
        user_id: User UUID
        sequence_type: Type of sequence
        db_session: Database session
        
    Returns:
        True if unenrolled successfully, False otherwise
    """
    try:
        from web.backend.database import EmailSequence, EmailSequenceType
        
        # Find active sequence
        sequence = db_session.query(EmailSequence).filter(
            EmailSequence.user_id == user_id,
            EmailSequence.sequence_name == EmailSequenceType(sequence_type),
            EmailSequence.completed_at.is_(None)
        ).first()
        
        if not sequence:
            logger.info(f"User {user_id} not enrolled in {sequence_type}")
            return False
        
        # Mark as unsubscribed
        sequence.unsubscribed = True
        sequence.completed_at = datetime.utcnow()
        db_session.commit()
        
        logger.info(f"Unenrolled user {user_id} from {sequence_type} sequence")
        return True
        
    except Exception as e:
        logger.error(f"Failed to unenroll user from sequence: {e}")
        db_session.rollback()
        return False

def load_email_template(template_name: str) -> str:
    """
    Load email template from file
    
    Args:
        template_name: Template filename
        
    Returns:
        Template HTML content
    """
    from pathlib import Path
    import os
    
    # Get template directory
    backend_dir = Path(__file__).parent.parent
    templates_dir = backend_dir / 'email_templates' / 'marketing'
    template_path = templates_dir / template_name
    
    if not template_path.exists():
        logger.error(f"Template not found: {template_path}")
        return f"<html><body><h1>Email Template Missing</h1><p>Template {template_name} not found.</p></body></html>"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load template {template_name}: {e}")
        return f"<html><body><h1>Template Error</h1><p>Failed to load template.</p></body></html>"

def render_email_template(template_html: str, context: Dict[str, Any]) -> str:
    """
    Render email template with context variables
    
    Simple template rendering using string replacement.
    For production, consider using Jinja2.
    
    Args:
        template_html: Template HTML content
        context: Dictionary of variables to replace
        
    Returns:
        Rendered HTML content
    """
    rendered = template_html
    for key, value in context.items():
        placeholder = f"{{{{{key}}}}}"
        rendered = rendered.replace(placeholder, str(value))
    return rendered

def process_due_emails(db_session) -> int:
    """
    Process all due emails in sequences
    
    Should be run periodically (e.g., hourly cron job)
    
    Args:
        db_session: Database session
        
    Returns:
        Number of emails sent
    """
    from web.backend.database import EmailSequence, User, EmailLog
    from web.backend.marketing.email_sequences import get_sequence_definition, calculate_next_send_date
    from web.backend.marketing.email_sender import get_email_sender
    
    sent_count = 0
    
    try:
        # Get all active sequences
        sequences = db_session.query(EmailSequence).filter(
            EmailSequence.completed_at.is_(None),
            EmailSequence.paused == False,
            EmailSequence.unsubscribed == False
        ).all()
        
        email_sender = get_email_sender()
        
        for seq in sequences:
            # Get sequence definition
            seq_type = seq.sequence_name.value if hasattr(seq.sequence_name, 'value') else seq.sequence_name
            seq_def = get_sequence_definition(seq_type)
            
            if not seq_def:
                logger.warning(f"Sequence definition not found: {seq_type}")
                continue
            
            # Get next step
            next_step = seq_def.get_next_step(seq.current_step)
            
            if not next_step:
                # Sequence complete
                seq.completed_at = datetime.utcnow()
                db_session.commit()
                logger.info(f"Sequence {seq_type} completed for user {seq.user_id}")
                continue
            
            # Check if it's time to send
            next_send_date = calculate_next_send_date(seq_type, seq.current_step, seq.started_at)
            
            if not next_send_date or next_send_date > datetime.utcnow():
                continue  # Not due yet
            
            # Get user
            user = db_session.query(User).filter(User.id == seq.user_id).first()
            if not user:
                logger.error(f"User {seq.user_id} not found")
                continue
            
            # Load and render template
            template_html = load_email_template(next_step.template_name)
            context = {
                'user_name': user.full_name or user.email.split('@')[0],
                'user_email': user.email,
                'company_name': user.company or '',
                'current_plan': user.plan.value if hasattr(user.plan, 'value') else user.plan,
                'unsubscribe_link': f"https://yourdomain.com/unsubscribe?user={seq.user_id}&seq={seq_type}"
            }
            
            rendered_html = render_email_template(template_html, context)
            
            # Send email
            result = email_sender.send_email(
                to_email=user.email,
                subject=next_step.subject,
                html_content=rendered_html,
                tracking_enabled=True,
                metadata={
                    'sequence_type': seq_type,
                    'step_number': str(next_step.step_number),
                    'user_id': str(seq.user_id)
                }
            )
            
            if result.get('success'):
                # Log email
                email_log = EmailLog(
                    user_id=seq.user_id,
                    email_address=user.email,
                    email_type=f"{seq_type}_step_{next_step.step_number}",
                    subject=next_step.subject,
                    template_version='1.0',
                    sent_at=datetime.utcnow(),
                    external_id=result.get('message_id'),
                    external_status='sent'
                )
                db_session.add(email_log)
                
                # Move to next step
                seq.current_step = next_step.step_number
                db_session.commit()
                
                sent_count += 1
                logger.info(f"Sent {seq_type} step {next_step.step_number} to {user.email}")
            else:
                logger.error(f"Failed to send email: {result.get('error')}")
        
        return sent_count
        
    except Exception as e:
        logger.error(f"Error processing due emails: {e}")
        db_session.rollback()
        return sent_count

def trigger_signup_automation(user_id: str, db_session) -> bool:
    """
    Trigger automation when user signs up
    
    Args:
        user_id: User UUID
        db_session: Database session
        
    Returns:
        True if triggered successfully
    """
    logger.info(f"Triggering signup automation for user {user_id}")
    return enroll_user_in_sequence(user_id, 'welcome', db_session)

def trigger_trial_automation(user_id: str, db_session) -> bool:
    """
    Trigger automation when user starts trial
    
    Args:
        user_id: User UUID
        db_session: Database session
        
    Returns:
        True if triggered successfully
    """
    logger.info(f"Triggering trial automation for user {user_id}")
    return enroll_user_in_sequence(user_id, 'trial_conversion', db_session)

def trigger_subscription_automation(user_id: str, db_session) -> bool:
    """
    Trigger automation when user subscribes
    
    Args:
        user_id: User UUID
        db_session: Database session
        
    Returns:
        True if triggered successfully
    """
    logger.info(f"Triggering subscription automation for user {user_id}")
    # Unenroll from trial conversion if active
    unenroll_user_from_sequence(user_id, 'trial_conversion', db_session)
    # Enroll in onboarding
    return enroll_user_in_sequence(user_id, 'onboarding', db_session)

def trigger_reengagement_automation(user_id: str, db_session) -> bool:
    """
    Trigger automation for inactive users
    
    Args:
        user_id: User UUID
        db_session: Database session
        
    Returns:
        True if triggered successfully
    """
    logger.info(f"Triggering re-engagement automation for user {user_id}")
    return enroll_user_in_sequence(user_id, 're_engagement', db_session)

__all__ = [
    'enroll_user_in_sequence',
    'unenroll_user_from_sequence',
    'process_due_emails',
    'trigger_signup_automation',
    'trigger_trial_automation',
    'trigger_subscription_automation',
    'trigger_reengagement_automation'
]
