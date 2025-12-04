"""
JWT token creation and verification
"""
import os
import jwt
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import logging
import secrets

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'change-this-secret-in-production-use-env-var')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access tokens
REFRESH_TOKEN_EXPIRE_DAYS = 30  # Long-lived refresh tokens

if JWT_SECRET == 'change-this-secret-in-production-use-env-var':
    logger.warning(
        "Using default JWT_SECRET! "
        "Set JWT_SECRET environment variable in production!"
    )


def create_access_token(user_id: str, email: str, is_admin: bool = False) -> str:
    """
    Create a short-lived JWT access token

    Args:
        user_id: User's UUID
        email: User's email
        is_admin: Whether user is admin

    Returns:
        Encoded JWT token
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        'user_id': str(user_id),
        'email': email,
        'is_admin': is_admin,
        'iat': now,  # Issued at
        'exp': expires,  # Expires at
        'type': 'access'
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def create_refresh_token() -> tuple[str, str]:
    """
    Create a long-lived refresh token

    Returns:
        Tuple of (token, token_hash) where:
        - token: The actual token to return to client
        - token_hash: Hash to store in database
    """
    # Generate cryptographically secure random token
    token = secrets.token_urlsafe(32)

    # Hash the token for storage
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    return token, token_hash


def verify_access_token(token: str) -> Optional[Dict]:
    """
    Verify and decode an access token

    Args:
        token: JWT token to verify

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Verify it's an access token
        if payload.get('type') != 'access':
            logger.warning("Token is not an access token")
            return None

        return payload

    except jwt.ExpiredSignatureError:
        logger.debug("Access token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid access token: {e}")
        return None


def verify_refresh_token(token: str, stored_hash: str) -> bool:
    """
    Verify a refresh token against its stored hash

    Args:
        token: The refresh token from client
        stored_hash: The hash stored in database

    Returns:
        True if token is valid, False otherwise
    """
    try:
        # Hash the provided token
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Compare with stored hash (constant-time comparison)
        return secrets.compare_digest(token_hash, stored_hash)

    except Exception as e:
        logger.error(f"Error verifying refresh token: {e}")
        return False


def revoke_refresh_token(db, token: str) -> bool:
    """
    Revoke a refresh token

    Args:
        db: Database session
        token: The refresh token to revoke

    Returns:
        True if token was revoked, False if not found
    """
    from database.models import RefreshToken

    try:
        # Hash the token to find it in database
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Find and revoke the token
        refresh_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        if refresh_token:
            refresh_token.revoked = True
            refresh_token.revoked_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Revoked refresh token for user {refresh_token.user_id}")
            return True

        return False

    except Exception as e:
        logger.error(f"Error revoking refresh token: {e}")
        db.rollback()
        return False


def decode_token_without_verification(token: str) -> Optional[Dict]:
    """
    Decode a token without verifying signature
    Useful for debugging or extracting user_id from expired tokens

    Args:
        token: JWT token to decode

    Returns:
        Decoded payload (unverified)
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        return None
