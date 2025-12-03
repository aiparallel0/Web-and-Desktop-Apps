"""
=============================================================================
ENCRYPTION UTILITIES - Token and Credential Encryption
=============================================================================

Provides secure encryption for storing API tokens and credentials.

Uses Fernet symmetric encryption from the cryptography library.

Environment Variables:
- ENCRYPTION_KEY: Base64-encoded Fernet key (generated if not set)

Usage:
    from integrations.encryption import encrypt_token, decrypt_token
    
    encrypted = encrypt_token("my-api-key")
    decrypted = decrypt_token(encrypted)

=============================================================================
"""

import os
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import cryptography
try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography not installed. Run: pip install cryptography>=41.0.0")


class CredentialEncryption:
    """
    Handles encryption and decryption of sensitive credentials.
    
    Uses Fernet symmetric encryption with a key derived from
    environment variable or auto-generated.
    """
    
    def __init__(self, key: str = None):
        """
        Initialize encryption handler.
        
        Args:
            key: Encryption key (defaults to ENCRYPTION_KEY env var)
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError(
                "cryptography required. Install with: pip install cryptography>=41.0.0"
            )
        
        self._key = key or os.getenv('ENCRYPTION_KEY')
        
        if not self._key:
            # Generate key from JWT_SECRET if available
            jwt_secret = os.getenv('JWT_SECRET', 'default-secret-for-development')
            self._key = self._derive_key(jwt_secret)
            logger.warning(
                "ENCRYPTION_KEY not set. Using derived key from JWT_SECRET. "
                "Set ENCRYPTION_KEY in production!"
            )
        
        try:
            self._fernet = Fernet(self._key.encode() if isinstance(self._key, str) else self._key)
        except Exception as e:
            # If key is invalid, generate new one
            logger.warning(f"Invalid encryption key, generating new one: {e}")
            self._key = Fernet.generate_key().decode()
            self._fernet = Fernet(self._key.encode())
    
    def _derive_key(self, password: str) -> str:
        """
        Derive a Fernet key from a password using PBKDF2.
        
        Args:
            password: Password to derive key from
            
        Returns:
            Base64-encoded Fernet key
        """
        # Use a fixed salt for consistency (not ideal, but works for dev)
        salt = b'receipt-extractor-salt'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode()
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        
        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str) -> Optional[str]:
        """
        Decrypt a string.
        
        Args:
            ciphertext: Base64-encoded encrypted string
            
        Returns:
            Decrypted string or None if decryption fails
        """
        if not ciphertext:
            return None
        
        try:
            decrypted = self._fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.error("Decryption failed: Invalid token")
            return None
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key.
        
        Returns:
            Base64-encoded key string
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography required")
        
        return Fernet.generate_key().decode()


# =============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# =============================================================================

_encryption_instance: Optional[CredentialEncryption] = None


def _get_encryption() -> CredentialEncryption:
    """Get or create encryption instance."""
    global _encryption_instance
    
    if _encryption_instance is None:
        _encryption_instance = CredentialEncryption()
    
    return _encryption_instance


def encrypt_token(token: str) -> str:
    """
    Encrypt an API token.
    
    Args:
        token: Token to encrypt
        
    Returns:
        Encrypted token string
    """
    return _get_encryption().encrypt(token)


def decrypt_token(encrypted: str) -> Optional[str]:
    """
    Decrypt an API token.
    
    Args:
        encrypted: Encrypted token string
        
    Returns:
        Decrypted token or None if decryption fails
    """
    return _get_encryption().decrypt(encrypted)


def encrypt_credentials(credentials: dict) -> str:
    """
    Encrypt a credentials dictionary.
    
    Args:
        credentials: Dictionary of credentials
        
    Returns:
        Encrypted JSON string
    """
    import json
    json_str = json.dumps(credentials)
    return _get_encryption().encrypt(json_str)


def decrypt_credentials(encrypted: str) -> Optional[dict]:
    """
    Decrypt a credentials dictionary.
    
    Args:
        encrypted: Encrypted JSON string
        
    Returns:
        Decrypted dictionary or None if decryption fails
    """
    import json
    
    decrypted = _get_encryption().decrypt(encrypted)
    if not decrypted:
        return None
    
    try:
        return json.loads(decrypted)
    except json.JSONDecodeError:
        logger.error("Failed to parse decrypted credentials as JSON")
        return None


def generate_encryption_key() -> str:
    """
    Generate a new encryption key for production use.
    
    Returns:
        Base64-encoded Fernet key
    
    Usage:
        python -c "from web.backend.integrations.encryption import generate_encryption_key; print(generate_encryption_key())"
    """
    return CredentialEncryption.generate_key()
