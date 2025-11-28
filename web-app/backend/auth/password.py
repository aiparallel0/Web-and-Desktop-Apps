"""
Password hashing and verification using bcrypt
"""
import bcrypt
import logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password as string
    """
    if not password:
        raise ValueError("Password cannot be empty")

    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds is secure and performant
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash

    Args:
        password: Plain text password to verify
        password_hash: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    if not password or not password_hash:
        return False

    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def is_password_strong(password: str) -> tuple[bool, list[str]]:
    """
    Check if password meets strength requirements

    Requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains number
    - Contains special character

    Args:
        password: Password to check

    Returns:
        Tuple of (is_strong, list_of_issues)
    """
    issues = []

    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")

    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one number")

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        issues.append("Password must contain at least one special character")

    return (len(issues) == 0, issues)
