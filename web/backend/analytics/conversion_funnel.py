"""
Conversion funnel analysis

Track and analyze user progression through conversion funnels:
- Signup funnel (landing → signup → verified → trial)
- Activation funnel (trial → first receipt → API call → active)
- Conversion funnel (trial → upgrade prompt → payment → subscription)
- Retention funnel (subscription → month 1 → month 2 → month 3)
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.analytics.conversion_funnel",
            file_path=__file__,
            description="Conversion funnel analysis and metrics",
            dependencies=["web.backend.database"],
            exports=["FunnelDefinition", "track_funnel_step", "analyze_funnel", "get_funnel_metrics"]
        ))
    except Exception:
        pass

class FunnelDefinition:
    """Definition of a conversion funnel"""
    
    def __init__(self, funnel_type: str, steps: List[str], description: str = ""):
        """
        Initialize funnel definition
        
        Args:
            funnel_type: Type of funnel (signup, activation, etc.)
            steps: List of step names in order
            description: Description of the funnel
        """
        self.funnel_type = funnel_type
        self.steps = steps
        self.description = description
    
    def get_step_index(self, step_name: str) -> int:
        """Get index of a step"""
        try:
            return self.steps.index(step_name)
        except ValueError:
            return -1
    
    def get_next_step(self, current_step: str) -> Optional[str]:
        """Get next step after current"""
        index = self.get_step_index(current_step)
        if index >= 0 and index < len(self.steps) - 1:
            return self.steps[index + 1]
        return None
    
    def is_complete(self, completed_steps: List[str]) -> bool:
        """Check if funnel is complete"""
        return all(step in completed_steps for step in self.steps)

# =============================================================================
# FUNNEL DEFINITIONS
# =============================================================================

SIGNUP_FUNNEL = FunnelDefinition(
    funnel_type="signup",
    steps=[
        "landing_page_view",
        "signup_click",
        "account_created",
        "email_verified",
        "trial_started"
    ],
    description="User signup and trial start funnel"
)

ACTIVATION_FUNNEL = FunnelDefinition(
    funnel_type="activation",
    steps=[
        "trial_started",
        "first_receipt_uploaded",
        "first_api_call",
        "five_receipts_processed"
    ],
    description="User activation and engagement funnel"
)

CONVERSION_FUNNEL = FunnelDefinition(
    funnel_type="conversion",
    steps=[
        "trial_started",
        "upgrade_prompt_viewed",
        "pricing_page_visited",
        "checkout_started",
        "subscription_created"
    ],
    description="Trial to paid conversion funnel"
)

RETENTION_FUNNEL = FunnelDefinition(
    funnel_type="retention",
    steps=[
        "subscription_created",
        "month_1_active",
        "month_2_active",
        "month_3_active"
    ],
    description="Subscription retention funnel"
)

FUNNELS = {
    "signup": SIGNUP_FUNNEL,
    "activation": ACTIVATION_FUNNEL,
    "conversion": CONVERSION_FUNNEL,
    "retention": RETENTION_FUNNEL
}

def track_funnel_step(
    user_id: str,
    funnel_type: str,
    step_name: str,
    metadata: Optional[Dict[str, Any]] = None,
    db_session = None
) -> bool:
    """
    Track user completion of a funnel step
    
    Args:
        user_id: User UUID
        funnel_type: Type of funnel
        step_name: Name of the step completed
        metadata: Additional step metadata
        db_session: Database session (optional)
        
    Returns:
        True if tracked successfully
    """
    try:
        from web.backend.database import ConversionFunnel, FunnelType, get_db_context
        
        # Validate funnel type
        try:
            funnel_enum = FunnelType(funnel_type)
        except ValueError:
            logger.error(f"Invalid funnel type: {funnel_type}")
            return False
        
        # Use provided session or create new one
        if db_session:
            funnel = ConversionFunnel(
                user_id=user_id,
                funnel_type=funnel_enum,
                step_name=step_name,
                completed_at=datetime.utcnow(),
                metadata=metadata or {}
            )
            db_session.add(funnel)
            db_session.commit()
        else:
            with get_db_context() as db:
                funnel = ConversionFunnel(
                    user_id=user_id,
                    funnel_type=funnel_enum,
                    step_name=step_name,
                    completed_at=datetime.utcnow(),
                    metadata=metadata or {}
                )
                db.add(funnel)
                db.commit()
        
        logger.info(f"Tracked funnel step: {funnel_type}/{step_name} for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to track funnel step: {e}")
        return False

def get_user_funnel_progress(
    user_id: str,
    funnel_type: str,
    db_session = None
) -> List[str]:
    """
    Get list of completed steps for a user in a funnel
    
    Args:
        user_id: User UUID
        funnel_type: Type of funnel
        db_session: Database session (optional)
        
    Returns:
        List of completed step names
    """
    try:
        from web.backend.database import ConversionFunnel, FunnelType, get_db_context
        
        funnel_enum = FunnelType(funnel_type)
        
        if db_session:
            steps = db_session.query(ConversionFunnel).filter(
                ConversionFunnel.user_id == user_id,
                ConversionFunnel.funnel_type == funnel_enum
            ).all()
        else:
            with get_db_context() as db:
                steps = db.query(ConversionFunnel).filter(
                    ConversionFunnel.user_id == user_id,
                    ConversionFunnel.funnel_type == funnel_enum
                ).all()
        
        return [step.step_name for step in steps]
        
    except Exception as e:
        logger.error(f"Failed to get funnel progress: {e}")
        return []

def analyze_funnel(
    funnel_type: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db_session = None
) -> Dict[str, Any]:
    """
    Analyze funnel conversion rates
    
    Args:
        funnel_type: Type of funnel to analyze
        start_date: Start date for analysis (optional)
        end_date: End date for analysis (optional)
        db_session: Database session (optional)
        
    Returns:
        Dictionary with funnel metrics
    """
    try:
        from web.backend.database import ConversionFunnel, FunnelType, get_db_context
        
        funnel_enum = FunnelType(funnel_type)
        funnel_def = FUNNELS.get(funnel_type)
        
        if not funnel_def:
            logger.error(f"Unknown funnel type: {funnel_type}")
            return {}
        
        # Query funnel data
        if db_session:
            query = db_session.query(ConversionFunnel).filter(
                ConversionFunnel.funnel_type == funnel_enum
            )
        else:
            with get_db_context() as db:
                query = db.query(ConversionFunnel).filter(
                    ConversionFunnel.funnel_type == funnel_enum
                )
        
        if start_date:
            query = query.filter(ConversionFunnel.completed_at >= start_date)
        if end_date:
            query = query.filter(ConversionFunnel.completed_at <= end_date)
        
        # Group by user and count completions per step
        user_steps = defaultdict(set)
        
        if db_session:
            steps = query.all()
        else:
            with get_db_context() as db:
                query = db.query(ConversionFunnel).filter(
                    ConversionFunnel.funnel_type == funnel_enum
                )
                if start_date:
                    query = query.filter(ConversionFunnel.completed_at >= start_date)
                if end_date:
                    query = query.filter(ConversionFunnel.completed_at <= end_date)
                steps = query.all()
        
        for step in steps:
            user_id = str(step.user_id)
            user_steps[user_id].add(step.step_name)
        
        # Calculate metrics per step
        step_metrics = []
        total_users = len(user_steps)
        
        for i, step_name in enumerate(funnel_def.steps):
            users_completed = sum(1 for steps in user_steps.values() if step_name in steps)
            
            # Calculate drop-off
            if i > 0:
                prev_step = funnel_def.steps[i - 1]
                users_at_prev = sum(1 for steps in user_steps.values() if prev_step in steps)
                drop_off_rate = ((users_at_prev - users_completed) / users_at_prev * 100) if users_at_prev > 0 else 0
            else:
                drop_off_rate = 0
            
            conversion_rate = (users_completed / total_users * 100) if total_users > 0 else 0
            
            step_metrics.append({
                'step_name': step_name,
                'step_number': i,
                'users_completed': users_completed,
                'conversion_rate': round(conversion_rate, 2),
                'drop_off_rate': round(drop_off_rate, 2)
            })
        
        # Overall funnel completion
        users_completed_all = sum(
            1 for steps in user_steps.values()
            if all(step in steps for step in funnel_def.steps)
        )
        
        overall_conversion = (users_completed_all / total_users * 100) if total_users > 0 else 0
        
        return {
            'funnel_type': funnel_type,
            'total_users': total_users,
            'users_completed': users_completed_all,
            'overall_conversion_rate': round(overall_conversion, 2),
            'steps': step_metrics,
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze funnel: {e}")
        return {}

def get_funnel_metrics(
    days: int = 30,
    db_session = None
) -> Dict[str, Any]:
    """
    Get metrics for all funnels over the last N days
    
    Args:
        days: Number of days to analyze
        db_session: Database session (optional)
        
    Returns:
        Dictionary with metrics for all funnels
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    metrics = {}
    for funnel_type in FUNNELS.keys():
        metrics[funnel_type] = analyze_funnel(
            funnel_type,
            start_date=start_date,
            end_date=end_date,
            db_session=db_session
        )
    
    return {
        'period_days': days,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'funnels': metrics
    }

__all__ = [
    'FunnelDefinition',
    'SIGNUP_FUNNEL',
    'ACTIVATION_FUNNEL',
    'CONVERSION_FUNNEL',
    'RETENTION_FUNNEL',
    'FUNNELS',
    'track_funnel_step',
    'get_user_funnel_progress',
    'analyze_funnel',
    'get_funnel_metrics'
]
