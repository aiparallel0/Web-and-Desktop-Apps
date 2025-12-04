#!/usr/bin/env python3
"""
Production Configuration Validator

CRITICAL SECURITY TOOL - Prevents deployment with insecure configuration.

This script validates that your Receipt Extractor instance is properly configured
for production deployment. It checks for common security issues that could lead to
data breaches, unauthorized access, or service compromise.

BUSINESS PLAN IMPLEMENTATION:
- Validates JWT secret strength (must be 32+ characters, not default value)
- Checks database configuration (PostgreSQL required for production)
- Verifies environment settings (Flask debug mode, secret keys)
- Ensures HTTPS/SSL configuration
- Validates Stripe webhook secrets (if payments enabled)

Usage:
    python tools/validate_production_config.py [--strict] [--fix]

Options:
    --strict    Fail on warnings (not just errors)
    --fix       Offer to fix common issues automatically
    --env FILE  Specify .env file to validate (default: .env)

Exit Codes:
    0  - All checks passed
    1  - Critical errors found (MUST FIX before production)
    2  - Warnings found (should fix, but not critical)
"""

import os
import sys
import re
import secrets
from pathlib import Path
from typing import List, Tuple, Optional
import argparse

# ANSI Colors
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
BOLD = '\033[1m'
NC = '\033[0m'  # No Color


class ValidationError:
    """Represents a validation error or warning"""

    def __init__(self, severity: str, category: str, message: str, fix_hint: Optional[str] = None):
        self.severity = severity  # 'CRITICAL', 'ERROR', 'WARNING', 'INFO'
        self.category = category
        self.message = message
        self.fix_hint = fix_hint


class ProductionValidator:
    """Validates production configuration for security and correctness"""

    def __init__(self, env_file: str = '.env', strict: bool = False):
        self.env_file = Path(env_file)
        self.strict = strict
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.env_vars = {}

    def load_env(self):
        """Load environment variables from .env file"""
        if not self.env_file.exists():
            self.errors.append(ValidationError(
                'CRITICAL',
                'Configuration',
                f'.env file not found at {self.env_file}',
                'Copy .env.example to .env and configure with production values'
            ))
            return False

        try:
            with open(self.env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip().strip('"').strip("'")
                        self.env_vars[key.strip()] = value
                        # Also set in os.environ for checks that use os.getenv
                        os.environ[key.strip()] = value
            return True
        except Exception as e:
            self.errors.append(ValidationError(
                'CRITICAL',
                'Configuration',
                f'Failed to parse .env file: {e}',
                'Check .env file syntax (KEY=value format)'
            ))
            return False

    def get_env(self, key: str, default: str = '') -> str:
        """Get environment variable from loaded .env"""
        return self.env_vars.get(key, os.getenv(key, default))

    def validate_jwt_secret(self):
        """
        CRITICAL SECURITY CHECK - JWT Secret Validation

        From business plan:
        "Default JWT secret is 'change-this-secret-in-production-use-env-var'
         This is a CRITICAL vulnerability - anyone can forge tokens"
        """
        jwt_secret = self.get_env('JWT_SECRET', '')

        # List of insecure default/example secrets
        INSECURE_DEFAULTS = [
            'change-this-secret-in-production-use-env-var',
            'change-this-secret-in-production-use-env-var-min-32-chars',
            'dev-secret-key-change-in-production',
            'secret',
            'changeme',
            'password',
            'test',
            'development',
        ]

        # CRITICAL: Check for default/insecure secrets
        if jwt_secret.lower() in [s.lower() for s in INSECURE_DEFAULTS]:
            self.errors.append(ValidationError(
                'CRITICAL',
                'JWT Security',
                f'🚨 CRITICAL SECURITY VULNERABILITY: Using default JWT secret!\n'
                f'   Current value: "{jwt_secret}"\n'
                f'   ANYONE can forge authentication tokens and gain admin access!',
                f'Generate secure secret:\n'
                f'   python -c "import secrets; print(secrets.token_urlsafe(64))"\n'
                f'   Then set JWT_SECRET in .env to the generated value'
            ))
            return

        # ERROR: Secret too short
        if len(jwt_secret) < 32:
            self.errors.append(ValidationError(
                'ERROR',
                'JWT Security',
                f'JWT_SECRET too short ({len(jwt_secret)} chars). Minimum: 32 characters.\n'
                f'   Short secrets are vulnerable to brute-force attacks.',
                'Generate longer secret: python -c "import secrets; print(secrets.token_urlsafe(64))"'
            ))
            return

        # WARNING: Secret not cryptographically random
        if jwt_secret.isalnum() or jwt_secret.isalpha():
            self.warnings.append(ValidationError(
                'WARNING',
                'JWT Security',
                'JWT_SECRET appears to not be cryptographically random.\n'
                '   Use secrets.token_urlsafe() for proper randomness.',
                'Generate secure secret: python -c "import secrets; print(secrets.token_urlsafe(64))"'
            ))

        # SUCCESS
        print(f'{GREEN}✓{NC} JWT_SECRET: Secure ({len(jwt_secret)} characters)')

    def validate_flask_config(self):
        """Validate Flask-specific configuration"""
        flask_env = self.get_env('FLASK_ENV', 'development')
        flask_debug = self.get_env('FLASK_DEBUG', 'False').lower()
        debug = self.get_env('DEBUG', 'False').lower()
        secret_key = self.get_env('SECRET_KEY', '')

        # CRITICAL: Debug mode in production
        if flask_debug in ('true', '1', 'yes') or debug in ('true', '1', 'yes'):
            self.errors.append(ValidationError(
                'CRITICAL',
                'Flask Security',
                '🚨 Debug mode is ENABLED!\n'
                '   Debug mode exposes sensitive information and allows code execution.',
                'Set FLASK_DEBUG=False and DEBUG=False in .env'
            ))

        # ERROR: Wrong environment
        if flask_env != 'production':
            self.errors.append(ValidationError(
                'ERROR',
                'Flask Configuration',
                f'FLASK_ENV is set to "{flask_env}" (should be "production")',
                'Set FLASK_ENV=production in .env'
            ))

        # ERROR: Weak SECRET_KEY
        INSECURE_SECRET_KEYS = [
            'dev-secret-key-change-in-production',
            'secret',
            'changeme',
        ]
        if secret_key.lower() in [s.lower() for s in INSECURE_SECRET_KEYS]:
            self.errors.append(ValidationError(
                'ERROR',
                'Flask Security',
                f'Using insecure SECRET_KEY: "{secret_key}"',
                'Generate secure key: python -c "import secrets; print(secrets.token_hex(32))"'
            ))
        elif len(secret_key) < 24:
            self.warnings.append(ValidationError(
                'WARNING',
                'Flask Security',
                f'SECRET_KEY too short ({len(secret_key)} chars). Recommend 32+ characters.',
                'Generate longer key: python -c "import secrets; print(secrets.token_hex(32))"'
            ))
        else:
            print(f'{GREEN}✓{NC} Flask SECRET_KEY: Secure ({len(secret_key)} characters)')

        if flask_env == 'production' and flask_debug == 'false':
            print(f'{GREEN}✓{NC} Flask environment: production (debug disabled)')

    def validate_database_config(self):
        """
        Validate database configuration

        From business plan:
        "Currently defaults to SQLite
         Need PostgreSQL for production"
        """
        database_url = self.get_env('DATABASE_URL', '')
        use_sqlite = self.get_env('USE_SQLITE', 'True').lower()

        # CRITICAL: Using SQLite in production
        if use_sqlite in ('true', '1', 'yes') or 'sqlite' in database_url.lower():
            self.errors.append(ValidationError(
                'CRITICAL',
                'Database',
                '🚨 SQLite is NOT suitable for production!\n'
                '   SQLite has limitations with concurrent users and can corrupt under load.',
                'Set up PostgreSQL:\n'
                '   1. Create PostgreSQL database (Railway/Supabase/AWS RDS)\n'
                '   2. Set DATABASE_URL=postgresql://user:pass@host:port/dbname\n'
                '   3. Set USE_SQLITE=false'
            ))
            return

        # ERROR: No database URL configured
        if not database_url or database_url == 'sqlite:///./receipt_extractor.db':
            self.errors.append(ValidationError(
                'ERROR',
                'Database',
                'DATABASE_URL not configured',
                'Set DATABASE_URL to PostgreSQL connection string'
            ))
            return

        # Validate PostgreSQL connection string
        if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
            # Check for password in URL (should be present)
            if '@' not in database_url or ':' not in database_url.split('@')[0]:
                self.warnings.append(ValidationError(
                    'WARNING',
                    'Database',
                    'DATABASE_URL appears to be missing authentication',
                    'Ensure format: postgresql://user:password@host:port/database'
                ))
            else:
                print(f'{GREEN}✓{NC} Database: PostgreSQL configured')
        else:
            self.warnings.append(ValidationError(
                'WARNING',
                'Database',
                f'Unexpected DATABASE_URL format: {database_url[:20]}...',
                'Expected PostgreSQL connection string'
            ))

    def validate_stripe_config(self):
        """
        Validate Stripe payment configuration

        From business plan:
        "Need Stripe setup for payments"
        """
        stripe_secret = self.get_env('STRIPE_SECRET_KEY', '')
        stripe_webhook = self.get_env('STRIPE_WEBHOOK_SECRET', '')

        # INFO: Stripe not configured (optional feature)
        if not stripe_secret:
            print(f'{CYAN}ℹ{NC}  Stripe: Not configured (payments disabled)')
            return

        # ERROR: Using test key in production
        if stripe_secret.startswith('sk_test_'):
            self.errors.append(ValidationError(
                'ERROR',
                'Stripe Payments',
                'Using Stripe TEST key in production!\n'
                '   This will not process real payments.',
                'Use live key from Stripe Dashboard (starts with sk_live_)'
            ))
        elif stripe_secret.startswith('sk_live_'):
            # WARNING: Webhook secret missing
            if not stripe_webhook:
                self.warnings.append(ValidationError(
                    'WARNING',
                    'Stripe Payments',
                    'STRIPE_WEBHOOK_SECRET not configured.\n'
                    '   Webhooks will not be verified (security risk).',
                    'Get webhook secret from Stripe Dashboard → Developers → Webhooks'
                ))
            else:
                print(f'{GREEN}✓{NC} Stripe: Live mode with webhook secret')
        else:
            self.warnings.append(ValidationError(
                'WARNING',
                'Stripe Payments',
                f'Unexpected Stripe key format: {stripe_secret[:15]}...',
                'Should start with sk_live_ or sk_test_'
            ))

    def validate_https_config(self):
        """Validate HTTPS/SSL configuration"""
        flask_env = self.get_env('FLASK_ENV', 'development')

        # In production, we can't directly check HTTPS from env vars
        # but we can provide guidance
        if flask_env == 'production':
            print(f'{YELLOW}⚠{NC}  HTTPS: Cannot validate from .env file')
            self.warnings.append(ValidationError(
                'WARNING',
                'HTTPS/SSL',
                'Ensure HTTPS/SSL is configured on your deployment platform.\n'
                '   HTTP is insecure and will leak passwords/tokens.',
                'Configure SSL on:\n'
                '   - Railway: Automatic with custom domain\n'
                '   - Render: Automatic with custom domain\n'
                '   - AWS/GCP: Configure load balancer with SSL certificate'
            ))

    def validate_cors_config(self):
        """Validate CORS configuration"""
        cors_origins = self.get_env('CORS_ORIGINS', '')

        if not cors_origins:
            self.warnings.append(ValidationError(
                'WARNING',
                'CORS',
                'CORS_ORIGINS not configured',
                'Set CORS_ORIGINS to your frontend domain(s)'
            ))
        elif '*' in cors_origins:
            self.errors.append(ValidationError(
                'ERROR',
                'CORS Security',
                'CORS_ORIGINS set to wildcard (*) - allows any origin!',
                'Set specific origins: CORS_ORIGINS=https://yourdomain.com'
            ))
        elif cors_origins.startswith('http://'):
            self.warnings.append(ValidationError(
                'WARNING',
                'CORS',
                'CORS_ORIGINS uses HTTP (not HTTPS)\n'
                '   This reduces security.',
                'Use HTTPS for production: CORS_ORIGINS=https://yourdomain.com'
            ))
        else:
            print(f'{GREEN}✓{NC} CORS: Configured with specific origins')

    def validate_all(self) -> bool:
        """Run all validation checks"""
        print(f'{BOLD}{CYAN}╔════════════════════════════════════════════════════════════════╗{NC}')
        print(f'{BOLD}{CYAN}║                                                                ║{NC}')
        print(f'{BOLD}{CYAN}║     Production Configuration Validator v1.0                   ║{NC}')
        print(f'{BOLD}{CYAN}║     Receipt Extractor - Security Validation                   ║{NC}')
        print(f'{BOLD}{CYAN}║                                                                ║{NC}')
        print(f'{BOLD}{CYAN}╚════════════════════════════════════════════════════════════════╝{NC}')
        print()

        print(f'{BOLD}Loading configuration from: {self.env_file}{NC}')
        if not self.load_env():
            return False
        print()

        print(f'{BOLD}{BLUE}Running security checks...{NC}')
        print()

        # Run all checks
        self.validate_jwt_secret()
        self.validate_flask_config()
        self.validate_database_config()
        self.validate_stripe_config()
        self.validate_https_config()
        self.validate_cors_config()

        # Report results
        print()
        print(f'{BOLD}{"="*70}{NC}')
        print(f'{BOLD}Validation Results:{NC}')
        print(f'{"="*70}')
        print()

        # Show errors
        if self.errors:
            print(f'{BOLD}{RED}CRITICAL ERRORS ({len(self.errors)}):{NC}')
            print(f'{RED}{"─"*70}{NC}')
            for i, error in enumerate(self.errors, 1):
                print(f'{RED}[{error.severity}]{NC} {error.category}')
                print(f'  {error.message}')
                if error.fix_hint:
                    print(f'{YELLOW}  FIX: {error.fix_hint}{NC}')
                print()

        # Show warnings
        if self.warnings:
            print(f'{BOLD}{YELLOW}WARNINGS ({len(self.warnings)}):{NC}')
            print(f'{YELLOW}{"─"*70}{NC}')
            for i, warning in enumerate(self.warnings, 1):
                print(f'{YELLOW}[{warning.severity}]{NC} {warning.category}')
                print(f'  {warning.message}')
                if warning.fix_hint:
                    print(f'{CYAN}  FIX: {warning.fix_hint}{NC}')
                print()

        # Final verdict
        print(f'{BOLD}{"="*70}{NC}')
        if self.errors:
            print(f'{RED}{BOLD}❌ VALIDATION FAILED{NC}')
            print(f'{RED}Cannot deploy to production with {len(self.errors)} critical error(s).{NC}')
            print(f'{YELLOW}Fix all errors above before deploying.{NC}')
            return False
        elif self.warnings and self.strict:
            print(f'{YELLOW}{BOLD}⚠️  VALIDATION PASSED (with warnings){NC}')
            print(f'{YELLOW}Running in --strict mode: {len(self.warnings)} warning(s) found.{NC}')
            print(f'{YELLOW}Fix warnings before deploying.{NC}')
            return False
        elif self.warnings:
            print(f'{GREEN}{BOLD}✓ VALIDATION PASSED (with warnings){NC}')
            print(f'{YELLOW}{len(self.warnings)} warning(s) found - review before deploying.{NC}')
            return True
        else:
            print(f'{GREEN}{BOLD}✓ VALIDATION PASSED{NC}')
            print(f'{GREEN}Configuration is secure for production deployment.{NC}')
            return True


def main():
    parser = argparse.ArgumentParser(
        description='Validate production configuration for security',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Fail on warnings (not just errors)'
    )
    parser.add_argument(
        '--env',
        default='.env',
        help='Path to .env file (default: .env)'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Offer to fix common issues automatically (NOT IMPLEMENTED YET)'
    )

    args = parser.parse_args()

    validator = ProductionValidator(env_file=args.env, strict=args.strict)
    success = validator.validate_all()

    print()

    if args.fix:
        print(f'{YELLOW}--fix option not yet implemented{NC}')
        print()

    # Exit with appropriate code
    if success:
        if validator.warnings:
            sys.exit(2)  # Warnings found
        else:
            sys.exit(0)  # All good
    else:
        sys.exit(1)  # Critical errors


if __name__ == '__main__':
    main()
