#!/usr/bin/env python3
"""
Generate secure secrets for production deployment

This script generates cryptographically secure random strings
for use in production environment variables.

Usage:
    python3 generate-secrets.py
"""

import secrets
import sys

def generate_secret(length=48):
    """Generate a URL-safe random string of specified length"""
    return secrets.token_urlsafe(length)

def main():
    print("=" * 70)
    print("Receipt Extractor - Production Secrets Generator")
    print("=" * 70)
    print()
    print("Copy these values to your .env file or Railway environment variables")
    print()
    print("-" * 70)
    
    # Generate secrets
    secret_key = generate_secret(48)
    jwt_secret = generate_secret(48)
    
    print("SECRET_KEY=" + secret_key)
    print()
    print("JWT_SECRET=" + jwt_secret)
    print()
    print("-" * 70)
    print()
    print("✓ Secrets generated successfully!")
    print()
    print("IMPORTANT:")
    print("1. Keep these secrets secure - never commit to git")
    print("2. Use different secrets for development and production")
    print("3. Store production secrets in Railway/hosting provider")
    print()
    print("Next steps:")
    print("1. Copy the SECRET_KEY above")
    print("2. Copy the JWT_SECRET above")
    print("3. Add them to Railway environment variables")
    print("   OR add them to your .env file for local testing")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
