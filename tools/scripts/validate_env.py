#!/usr/bin/env python3
"""
Environment Validation Script

Validates that all required environment variables are set.
Checks configuration files and provides helpful error messages.

Usage:
    python tools/scripts/validate_env.py
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple


# Required environment variables for different configurations
REQUIRED_VARS = {
    "core": [
        "SECRET_KEY",
        "DATABASE_URL",
    ],
    "auth": [
        "JWT_SECRET_KEY",
    ],
    "optional": [
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "S3_BUCKET_NAME",
        "GOOGLE_DRIVE_CREDENTIALS",
        "DROPBOX_ACCESS_TOKEN",
        "HUGGINGFACE_TOKEN",
        "OPENAI_API_KEY",
        "ENABLE_CEFR",
    ]
}


def check_env_vars(var_list: List[str], required: bool = True) -> Tuple[List[str], List[str]]:
    """
    Check if environment variables are set.
    
    Args:
        var_list: List of environment variable names
        required: Whether these are required or optional
        
    Returns:
        Tuple of (found, missing) variable names
    """
    found = []
    missing = []
    
    for var in var_list:
        if os.getenv(var):
            found.append(var)
        else:
            missing.append(var)
    
    return found, missing


def check_env_file() -> bool:
    """Check if .env file exists."""
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if env_file.exists():
        print(f"✅ .env file found at {env_file}")
        return True
    else:
        print(f"⚠️ .env file not found at {env_file}")
        if env_example.exists():
            print(f"   Copy {env_example} to {env_file} and configure it")
        return False


def main():
    """Run environment validation."""
    print("🔍 Environment Validation")
    print("=" * 60)
    
    # Check .env file
    print("\n📄 Checking for .env file...")
    env_exists = check_env_file()
    
    # Check required core variables
    print("\n🔴 Required Core Variables:")
    core_found, core_missing = check_env_vars(REQUIRED_VARS["core"], required=True)
    
    for var in core_found:
        value = os.getenv(var)
        masked_value = value[:10] + "..." if len(value) > 10 else "***"
        print(f"  ✅ {var} = {masked_value}")
    
    for var in core_missing:
        print(f"  ❌ {var} is NOT SET (REQUIRED)")
    
    # Check auth variables
    print("\n🔐 Authentication Variables:")
    auth_found, auth_missing = check_env_vars(REQUIRED_VARS["auth"], required=True)
    
    for var in auth_found:
        value = os.getenv(var)
        masked_value = value[:10] + "..." if len(value) > 10 else "***"
        print(f"  ✅ {var} = {masked_value}")
    
    for var in auth_missing:
        print(f"  ❌ {var} is NOT SET (REQUIRED)")
    
    # Check optional variables
    print("\n⚪ Optional Variables (for features):")
    opt_found, opt_missing = check_env_vars(REQUIRED_VARS["optional"], required=False)
    
    for var in opt_found:
        value = os.getenv(var)
        masked_value = value[:10] + "..." if len(value) > 10 else "***"
        print(f"  ✅ {var} = {masked_value}")
    
    if opt_missing:
        print(f"  ℹ️  {len(opt_missing)} optional variables not set (features may be disabled)")
    
    # Check CEFR status
    print("\n🔧 CEFR Framework:")
    enable_cefr = os.getenv("ENABLE_CEFR", "false").lower() == "true"
    print(f"  ENABLE_CEFR = {enable_cefr}")
    if enable_cefr:
        print("  ✅ CEFR auto-tuning is ENABLED")
    else:
        print("  ℹ️  CEFR auto-tuning is DISABLED (optional)")
    
    # Summary
    print("\n" + "=" * 60)
    total_missing = len(core_missing) + len(auth_missing)
    
    if total_missing > 0:
        print(f"❌ Environment validation FAILED ({total_missing} required variables missing)")
        print("\n⚠️  Missing required variables:")
        for var in core_missing + auth_missing:
            print(f"    - {var}")
        print("\n💡 Tips:")
        print("    1. Copy .env.example to .env")
        print("    2. Fill in the required values")
        print("    3. Re-run this script to validate")
        return 1
    else:
        print("✅ All required environment variables are set")
        print(f"ℹ️  Optional features: {len(opt_found)}/{len(REQUIRED_VARS['optional'])} configured")
        return 0


if __name__ == "__main__":
    sys.exit(main())
