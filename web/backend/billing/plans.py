"""
=============================================================================
SUBSCRIPTION PLANS - Plan Definitions and Features
=============================================================================

Defines subscription plans, pricing, and feature limits for the
Receipt Extractor SaaS platform.

Usage:
    from billing.plans import SUBSCRIPTION_PLANS, get_plan_features
    
    pro_plan = SUBSCRIPTION_PLANS['pro']
    features = get_plan_features('pro')

=============================================================================
"""

from typing import Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# SUBSCRIPTION PLANS
# =============================================================================

SUBSCRIPTION_PLANS: Dict[str, Dict[str, Any]] = {
    'free': {
        'name': 'Free',
        'price': 0,
        'price_id': None,  # No Stripe price for free tier
        'description': 'Get started with basic receipt extraction',
        'features': {
            'receipts_per_month': 10,
            'storage_gb': 0.1,
            'cloud_training': False,
            'api_access': False,
            'priority_support': False,
            'custom_models': False,
            'batch_processing': False,
            'export_formats': ['json'],
            'max_file_size_mb': 5,
            'models_available': ['easyocr', 'tesseract'],
            'support_level': 'community'
        }
    },
    'pro': {
        'name': 'Pro',
        'price': 19,  # USD per month
        'price_id': os.getenv('STRIPE_PRICE_ID_PRO'),
        'description': 'For power users who need more extractions',
        'features': {
            'receipts_per_month': 500,
            'storage_gb': 5,
            'cloud_training': True,
            'api_access': True,
            'priority_support': False,
            'custom_models': False,
            'batch_processing': True,
            'export_formats': ['json', 'csv', 'excel'],
            'max_file_size_mb': 25,
            'models_available': ['all'],
            'support_level': 'email'
        }
    },
    'business': {
        'name': 'Business',
        'price': 49,  # USD per month
        'price_id': os.getenv('STRIPE_PRICE_ID_BUSINESS'),
        'description': 'For teams and businesses with high volume needs',
        'features': {
            'receipts_per_month': 2000,
            'storage_gb': 20,
            'cloud_training': True,
            'api_access': True,
            'priority_support': True,
            'custom_models': True,
            'batch_processing': True,
            'export_formats': ['json', 'csv', 'excel', 'pdf'],
            'max_file_size_mb': 50,
            'models_available': ['all'],
            'support_level': 'priority'
        }
    },
    'enterprise': {
        'name': 'Enterprise',
        'price': 'custom',
        'price_id': None,  # Custom pricing
        'description': 'Custom solutions for large organizations',
        'features': {
            'receipts_per_month': 'unlimited',
            'storage_gb': 100,
            'cloud_training': True,
            'api_access': True,
            'priority_support': True,
            'custom_models': True,
            'batch_processing': True,
            'export_formats': ['all'],
            'max_file_size_mb': 100,
            'models_available': ['all'],
            'support_level': 'dedicated',
            'on_premise': True,
            'sla': True,
            'custom_integrations': True
        }
    }
}

# =============================================================================
# PLAN HIERARCHY
# =============================================================================

PLAN_HIERARCHY = {
    'free': 0,
    'pro': 1,
    'business': 2,
    'enterprise': 3
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_plan_features(plan_name: str) -> Dict[str, Any]:
    """
    Get features for a specific plan.
    
    Args:
        plan_name: Name of the plan (free, pro, business, enterprise)
        
    Returns:
        Dictionary of plan features
        
    Raises:
        ValueError: If plan_name is invalid type
    """
    try:
        if not isinstance(plan_name, str):
            logger.warning(f"Invalid plan_name type: {type(plan_name)}")
            return SUBSCRIPTION_PLANS['free']['features']
        
        plan = SUBSCRIPTION_PLANS.get(plan_name.lower())
        if not plan:
            logger.warning(f"Plan not found: {plan_name}, returning free plan features")
            return SUBSCRIPTION_PLANS['free']['features']
        return plan['features']
    except Exception as e:
        logger.error(f"Error getting plan features for {plan_name}: {e}")
        return SUBSCRIPTION_PLANS['free']['features']


def is_feature_available(plan_name: str, feature: str) -> bool:
    """
    Check if a feature is available for a plan.
    
    Args:
        plan_name: Name of the plan
        feature: Feature to check
        
    Returns:
        True if feature is available
    """
    try:
        features = get_plan_features(plan_name)
        return bool(features.get(feature, False))
    except Exception as e:
        logger.error(f"Error checking feature {feature} for plan {plan_name}: {e}")
        return False


def get_plan_limit(plan_name: str, limit_name: str) -> Any:
    """
    Get a specific limit for a plan.
    
    Args:
        plan_name: Name of the plan
        limit_name: Name of the limit (e.g., 'receipts_per_month')
        
    Returns:
        Limit value or None
    """
    try:
        features = get_plan_features(plan_name)
        return features.get(limit_name)
    except Exception as e:
        logger.error(f"Error getting limit {limit_name} for plan {plan_name}: {e}")
        return None


def compare_plans(plan1: str, plan2: str) -> int:
    """
    Compare two plans by hierarchy.
    
    Returns:
        -1 if plan1 < plan2
        0 if plan1 == plan2
        1 if plan1 > plan2
    """
    try:
        h1 = PLAN_HIERARCHY.get(plan1, 0)
        h2 = PLAN_HIERARCHY.get(plan2, 0)
        
        if h1 < h2:
            return -1
        elif h1 > h2:
            return 1
        return 0
    except Exception as e:
        logger.error(f"Error comparing plans {plan1} and {plan2}: {e}")
        return 0


def is_plan_sufficient(user_plan: str, required_plan: str) -> bool:
    """
    Check if user's plan meets the minimum requirement.
    
    Args:
        user_plan: User's current plan
        required_plan: Minimum required plan
        
    Returns:
        True if user's plan is sufficient
    """
    try:
        return compare_plans(user_plan, required_plan) >= 0
    except Exception as e:
        logger.error(f"Error checking plan sufficiency: {e}")
        return False


def get_upgrade_recommendation(current_plan: str) -> Optional[str]:
    """
    Get the next plan to upgrade to.
    
    Args:
        current_plan: User's current plan
        
    Returns:
        Next plan name or None if already on highest plan
    """
    try:
        current_level = PLAN_HIERARCHY.get(current_plan, 0)
        
        for plan, level in PLAN_HIERARCHY.items():
            if level == current_level + 1:
                return plan
        
        return None
    except Exception as e:
        logger.error(f"Error getting upgrade recommendation for {current_plan}: {e}")
        return None


def get_all_plans() -> Dict[str, Dict[str, Any]]:
    """Get all available subscription plans."""
    try:
        return SUBSCRIPTION_PLANS.copy()
    except Exception as e:
        logger.error(f"Error getting all plans: {e}")
        return {}


def get_plan_price(plan_name: str) -> Any:
    """
    Get the price for a plan.
    
    Args:
        plan_name: Name of the plan
        
    Returns:
        Price (int for fixed, 'custom' for enterprise)
    """
    try:
        plan = SUBSCRIPTION_PLANS.get(plan_name)
        if not plan:
            logger.warning(f"Plan not found: {plan_name}, returning 0")
            return 0
        return plan.get('price', 0)
    except Exception as e:
        logger.error(f"Error getting price for plan {plan_name}: {e}")
        return 0
