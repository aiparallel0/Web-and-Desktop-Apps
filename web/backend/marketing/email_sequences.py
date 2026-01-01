"""
Email sequence definitions for marketing automation

Defines email sequences for:
- Welcome series (3 emails over 7 days)
- Trial conversion series (5 emails over 14 days)
- Onboarding series (3 emails over 30 days)
- Re-engagement series (3 emails over 90 days)
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# CEFR integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.marketing.email_sequences",
            file_path=__file__,
            description="Email sequence definitions for marketing automation",
            dependencies=["web.backend.database"],
            exports=["EmailSequenceDefinition", "get_sequence_definition", "SEQUENCES"]
        ))
    except Exception:
        pass

@dataclass
class EmailStep:
    """Single step in an email sequence"""
    step_number: int
    delay_days: int  # Days after sequence start
    subject: str
    template_name: str
    description: str

@dataclass
class EmailSequenceDefinition:
    """Definition of an email sequence"""
    sequence_name: str
    sequence_type: str  # welcome, trial_conversion, onboarding, re_engagement
    description: str
    steps: List[EmailStep]
    
    def get_step(self, step_number: int) -> Optional[EmailStep]:
        """Get step by number"""
        for step in self.steps:
            if step.step_number == step_number:
                return step
        return None
    
    def get_next_step(self, current_step: int) -> Optional[EmailStep]:
        """Get next step after current"""
        next_step_num = current_step + 1
        return self.get_step(next_step_num)
    
    def total_steps(self) -> int:
        """Get total number of steps"""
        return len(self.steps)

# =============================================================================
# WELCOME SERIES (3 emails over 7 days)
# =============================================================================
WELCOME_SEQUENCE = EmailSequenceDefinition(
    sequence_name="welcome",
    sequence_type="welcome",
    description="Welcome new users and introduce key features",
    steps=[
        EmailStep(
            step_number=0,
            delay_days=0,
            subject="Welcome to Receipt Extractor! Let's get started 🚀",
            template_name="welcome_day0.html",
            description="Welcome email with getting started guide"
        ),
        EmailStep(
            step_number=1,
            delay_days=3,
            subject="Discover powerful features in Receipt Extractor",
            template_name="welcome_day3.html",
            description="Feature highlights and use case examples"
        ),
        EmailStep(
            step_number=2,
            delay_days=7,
            subject="Your trial is ending soon - upgrade to continue!",
            template_name="welcome_day7.html",
            description="Trial ending reminder with upgrade CTA"
        ),
    ]
)

# =============================================================================
# TRIAL CONVERSION SERIES (5 emails over 14 days)
# =============================================================================
TRIAL_CONVERSION_SEQUENCE = EmailSequenceDefinition(
    sequence_name="trial_conversion",
    sequence_type="trial_conversion",
    description="Convert trial users to paid subscribers",
    steps=[
        EmailStep(
            step_number=0,
            delay_days=1,
            subject="Your Receipt Extractor account is ready!",
            template_name="trial_day1.html",
            description="Account setup complete confirmation"
        ),
        EmailStep(
            step_number=1,
            delay_days=5,
            subject="Have you tried our batch processing feature?",
            template_name="trial_day5.html",
            description="Feature introduction and tips"
        ),
        EmailStep(
            step_number=2,
            delay_days=10,
            subject="Only 4 days left in your trial",
            template_name="trial_day10.html",
            description="Trial ending in 4 days reminder"
        ),
        EmailStep(
            step_number=3,
            delay_days=13,
            subject="Last day of your trial - don't lose access!",
            template_name="trial_day13.html",
            description="Last day trial reminder with urgency"
        ),
        EmailStep(
            step_number=4,
            delay_days=15,
            subject="Your trial has ended - special upgrade offer inside",
            template_name="trial_day15.html",
            description="Trial ended with special upgrade offer"
        ),
    ]
)

# =============================================================================
# ONBOARDING SERIES (for paid users - 4 emails over 30 days)
# =============================================================================
ONBOARDING_SEQUENCE = EmailSequenceDefinition(
    sequence_name="onboarding",
    sequence_type="onboarding",
    description="Onboard new paid subscribers",
    steps=[
        EmailStep(
            step_number=0,
            delay_days=0,
            subject="Thank you for subscribing to Receipt Extractor! 🎉",
            template_name="onboarding_day0.html",
            description="Thank you for subscribing"
        ),
        EmailStep(
            step_number=1,
            delay_days=2,
            subject="Get started with our API - complete guide",
            template_name="onboarding_day2.html",
            description="API documentation and integration guide"
        ),
        EmailStep(
            step_number=2,
            delay_days=7,
            subject="Unlock advanced features you might have missed",
            template_name="onboarding_day7.html",
            description="Advanced features walkthrough"
        ),
        EmailStep(
            step_number=3,
            delay_days=30,
            subject="How's your experience with Receipt Extractor?",
            template_name="onboarding_day30.html",
            description="Check-in and feedback request"
        ),
    ]
)

# =============================================================================
# RE-ENGAGEMENT SERIES (for inactive users - 3 emails over 90 days)
# =============================================================================
RE_ENGAGEMENT_SEQUENCE = EmailSequenceDefinition(
    sequence_name="re_engagement",
    sequence_type="re_engagement",
    description="Re-engage inactive users",
    steps=[
        EmailStep(
            step_number=0,
            delay_days=30,
            subject="We miss you! Check out what's new in Receipt Extractor",
            template_name="reengage_day30.html",
            description="We miss you message with new features"
        ),
        EmailStep(
            step_number=1,
            delay_days=60,
            subject="Special offer: 20% off your next month",
            template_name="reengage_day60.html",
            description="Special discount offer for inactive users"
        ),
        EmailStep(
            step_number=2,
            delay_days=90,
            subject="Final reminder: Your account will be deactivated soon",
            template_name="reengage_day90.html",
            description="Final reminder before account deactivation"
        ),
    ]
)

# =============================================================================
# SEQUENCE REGISTRY
# =============================================================================
SEQUENCES: Dict[str, EmailSequenceDefinition] = {
    "welcome": WELCOME_SEQUENCE,
    "trial_conversion": TRIAL_CONVERSION_SEQUENCE,
    "onboarding": ONBOARDING_SEQUENCE,
    "re_engagement": RE_ENGAGEMENT_SEQUENCE,
}

def get_sequence_definition(sequence_type: str) -> Optional[EmailSequenceDefinition]:
    """
    Get sequence definition by type
    
    Args:
        sequence_type: Type of sequence (welcome, trial_conversion, etc.)
        
    Returns:
        EmailSequenceDefinition or None if not found
    """
    return SEQUENCES.get(sequence_type)

def get_all_sequences() -> List[EmailSequenceDefinition]:
    """
    Get all sequence definitions
    
    Returns:
        List of all EmailSequenceDefinitions
    """
    return list(SEQUENCES.values())

def calculate_next_send_date(sequence_type: str, current_step: int, started_at: datetime) -> Optional[datetime]:
    """
    Calculate when the next email should be sent
    
    Args:
        sequence_type: Type of sequence
        current_step: Current step number (0-indexed)
        started_at: When the sequence started
        
    Returns:
        datetime when next email should be sent, or None if sequence is complete
    """
    sequence = get_sequence_definition(sequence_type)
    if not sequence:
        return None
    
    next_step = sequence.get_next_step(current_step)
    if not next_step:
        return None  # Sequence complete
    
    return started_at + timedelta(days=next_step.delay_days)

__all__ = [
    'EmailStep',
    'EmailSequenceDefinition',
    'get_sequence_definition',
    'get_all_sequences',
    'calculate_next_send_date',
    'SEQUENCES',
    'WELCOME_SEQUENCE',
    'TRIAL_CONVERSION_SEQUENCE',
    'ONBOARDING_SEQUENCE',
    'RE_ENGAGEMENT_SEQUENCE',
]
