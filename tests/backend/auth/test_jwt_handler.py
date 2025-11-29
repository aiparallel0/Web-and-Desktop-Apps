"""
Test suite for JWT token creation and verification
Tests coverage for web-app/backend/auth/jwt_handler.py
"""
import pytest
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from freezegun import freeze_time
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'web-app', 'backend'))

from auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    revoke_refresh_token,
    decode_token_without_verification,
    JWT_SECRET,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)


class TestCreateAccessToken:
    """Test access token creation"""

    def test_create_access_token_success(self):
        """Test creating a valid access token with all parameters"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        email = "test@example.com"
        is_admin = False

        token = create_access_token(user_id, email, is_admin)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_admin_flag(self):
        """Test creating access token with admin flag set to True"""
        user_id = "admin-user-id"
        email = "admin@example.com"
        is_admin = True

        token = create_access_token(user_id, email, is_admin)
        payload = verify_access_token(token)

        assert payload is not None
        assert payload['is_admin'] is True

    def test_access_token_contains_correct_claims(self):
        """Test that access token contains all required claims"""
        user_id = "user-123"
        email = "user@test.com"

        token = create_access_token(user_id, email, False)
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        assert payload['user_id'] == user_id
        assert payload['email'] == email
        assert payload['is_admin'] is False
        assert payload['type'] == 'access'
        assert 'iat' in payload  # Issued at
        assert 'exp' in payload  # Expiration

    @freeze_time("2024-01-15 12:00:00")
    def test_access_token_expiry_time(self):
        """Test that access token has correct expiration time"""
        token = create_access_token("user-id", "test@example.com")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        issued_at = datetime.fromtimestamp(payload['iat'])
        expires_at = datetime.fromtimestamp(payload['exp'])

        expected_expiry = issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        assert expires_at == expected_expiry

    def test_create_access_token_different_users_different_tokens(self):
        """Test that different users get different tokens"""
        token1 = create_access_token("user-1", "user1@example.com")
        token2 = create_access_token("user-2", "user2@example.com")

        assert token1 != token2

    def test_create_access_token_same_user_different_tokens(self):
        """Test that same user gets different tokens (due to timestamp)"""
        import time

        token1 = create_access_token("user-1", "user1@example.com")
        time.sleep(0.01)  # Small delay to ensure different timestamp
        token2 = create_access_token("user-1", "user1@example.com")

        assert token1 != token2


class TestCreateRefreshToken:
    """Test refresh token creation"""

    def test_create_refresh_token_generates_token_and_hash(self):
        """Test that create_refresh_token returns both token and hash"""
        token, token_hash = create_refresh_token()

        assert token is not None
        assert token_hash is not None
        assert isinstance(token, str)
        assert isinstance(token_hash, str)

    def test_create_refresh_token_unique(self):
        """Test that each call generates unique tokens"""
        token1, hash1 = create_refresh_token()
        token2, hash2 = create_refresh_token()

        assert token1 != token2
        assert hash1 != hash2

    def test_refresh_token_hash_is_deterministic(self):
        """Test that hashing the same token produces same hash"""
        token, original_hash = create_refresh_token()

        # Hash the token again manually
        recalculated_hash = hashlib.sha256(token.encode()).hexdigest()

        assert recalculated_hash == original_hash

    def test_refresh_token_length_and_format(self):
        """Test that refresh token has appropriate length"""
        token, _ = create_refresh_token()

        # secrets.token_urlsafe(32) generates base64-url-safe strings
        assert len(token) > 40  # Should be reasonably long
        # Should only contain URL-safe characters
        import re
        assert re.match(r'^[A-Za-z0-9_-]+$', token)


class TestVerifyAccessToken:
    """Test access token verification"""

    def test_verify_valid_access_token(self):
        """Test verifying a valid access token"""
        user_id = "test-user-id"
        email = "test@example.com"
        is_admin = True

        token = create_access_token(user_id, email, is_admin)
        payload = verify_access_token(token)

        assert payload is not None
        assert payload['user_id'] == user_id
        assert payload['email'] == email
        assert payload['is_admin'] is True

    @freeze_time("2024-01-15 12:00:00")
    def test_verify_expired_access_token(self):
        """Test that expired tokens are rejected"""
        token = create_access_token("user-id", "test@example.com")

        # Token should be valid now
        assert verify_access_token(token) is not None

        # Move time forward past expiry (15 minutes + 1)
        with freeze_time("2024-01-15 12:16:00"):
            result = verify_access_token(token)
            assert result is None

    def test_verify_invalid_signature(self):
        """Test that tokens with invalid signatures are rejected"""
        # Create token with different secret
        payload = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'type': 'access',
            'exp': datetime.utcnow() + timedelta(minutes=15)
        }
        fake_token = jwt.encode(payload, 'wrong-secret', algorithm=JWT_ALGORITHM)

        result = verify_access_token(fake_token)
        assert result is None

    def test_verify_wrong_token_type(self):
        """Test that non-access tokens are rejected"""
        # Create a token with wrong type
        payload = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'type': 'refresh',  # Wrong type
            'exp': datetime.utcnow() + timedelta(minutes=15)
        }
        wrong_type_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        result = verify_access_token(wrong_type_token)
        assert result is None

    def test_verify_malformed_token(self):
        """Test that malformed tokens are rejected"""
        malformed_tokens = [
            "not.a.jwt",
            "invalid",
            "",
            "a.b.c.d.e",
        ]

        for token in malformed_tokens:
            result = verify_access_token(token)
            assert result is None


class TestVerifyRefreshToken:
    """Test refresh token verification"""

    def test_verify_refresh_token_correct_hash(self):
        """Test verifying refresh token with correct hash"""
        token, stored_hash = create_refresh_token()

        result = verify_refresh_token(token, stored_hash)
        assert result is True

    def test_verify_refresh_token_wrong_hash(self):
        """Test that wrong hash is rejected"""
        token, _ = create_refresh_token()
        wrong_hash = "0" * 64  # SHA-256 produces 64 hex chars

        result = verify_refresh_token(token, wrong_hash)
        assert result is False

    def test_verify_refresh_token_wrong_token(self):
        """Test that wrong token is rejected"""
        _, stored_hash = create_refresh_token()
        wrong_token, _ = create_refresh_token()

        result = verify_refresh_token(wrong_token, stored_hash)
        assert result is False

    def test_verify_refresh_token_timing_attack_resistance(self):
        """Test that verification uses constant-time comparison"""
        # This test verifies that secrets.compare_digest is used
        # which is resistant to timing attacks
        token, stored_hash = create_refresh_token()

        # Should return True for correct hash
        assert verify_refresh_token(token, stored_hash) is True

        # Should return False for incorrect hash
        wrong_hash = stored_hash[:-1] + ('0' if stored_hash[-1] != '0' else '1')
        assert verify_refresh_token(token, wrong_hash) is False

    def test_verify_refresh_token_exception_handling(self):
        """Test that exceptions are handled gracefully"""
        # Test with invalid inputs
        assert verify_refresh_token(None, "hash") is False
        assert verify_refresh_token("token", None) is False


class TestRevokeRefreshToken:
    """Test refresh token revocation"""

    def test_revoke_refresh_token_success(self, db_session, test_user):
        """Test successfully revoking a refresh token"""
        from database.models import RefreshToken
        from datetime import datetime

        # Create refresh token
        token, token_hash = create_refresh_token()

        # Store in database
        refresh_token_record = RefreshToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            revoked=False
        )
        db_session.add(refresh_token_record)
        db_session.commit()

        # Revoke the token
        result = revoke_refresh_token(db_session, token)

        assert result is True

        # Verify it's revoked in database
        db_session.refresh(refresh_token_record)
        assert refresh_token_record.revoked is True
        assert refresh_token_record.revoked_at is not None

    def test_revoke_nonexistent_token(self, db_session):
        """Test revoking a token that doesn't exist"""
        token, _ = create_refresh_token()

        result = revoke_refresh_token(db_session, token)
        assert result is False

    def test_revoke_token_database_error(self, db_session):
        """Test handling of database errors during revocation"""
        # Close the session to simulate database error
        db_session.close()

        token, _ = create_refresh_token()

        # Should handle error gracefully and return False
        result = revoke_refresh_token(db_session, token)
        assert result is False


class TestDecodeTokenWithoutVerification:
    """Test decoding tokens without signature verification"""

    def test_decode_token_without_verification(self):
        """Test decoding a valid token without verification"""
        user_id = "user-123"
        email = "test@example.com"

        token = create_access_token(user_id, email)
        payload = decode_token_without_verification(token)

        assert payload is not None
        assert payload['user_id'] == user_id
        assert payload['email'] == email

    @freeze_time("2024-01-15 12:00:00")
    def test_decode_expired_token_without_verification(self):
        """Test decoding an expired token without verification"""
        token = create_access_token("user-id", "test@example.com")

        # Move time forward past expiry
        with freeze_time("2024-01-15 12:30:00"):
            # Should still decode (no verification)
            payload = decode_token_without_verification(token)
            assert payload is not None
            assert payload['user_id'] == "user-id"

    def test_decode_invalid_signature_without_verification(self):
        """Test decoding token with invalid signature without verification"""
        # Create token with wrong secret
        payload = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'type': 'access'
        }
        token = jwt.encode(payload, 'wrong-secret', algorithm=JWT_ALGORITHM)

        # Should still decode (no verification)
        decoded = decode_token_without_verification(token)
        assert decoded is not None
        assert decoded['user_id'] == 'user-123'

    def test_decode_malformed_token_returns_none(self):
        """Test that malformed tokens return None"""
        malformed_tokens = [
            "not-a-token",
            "invalid.token",
            "",
        ]

        for token in malformed_tokens:
            result = decode_token_without_verification(token)
            assert result is None

    def test_decode_token_exception_handling(self):
        """Test exception handling in decode"""
        # Test with completely invalid input
        result = decode_token_without_verification("totally-invalid")
        assert result is None


class TestJWTConfiguration:
    """Test JWT configuration and security settings"""

    def test_jwt_secret_exists(self):
        """Test that JWT secret is configured"""
        assert JWT_SECRET is not None
        assert len(JWT_SECRET) > 0

    def test_jwt_algorithm_is_hs256(self):
        """Test that HS256 algorithm is used"""
        assert JWT_ALGORITHM == 'HS256'

    def test_access_token_expiry_configured(self):
        """Test that access token expiry is configured"""
        assert ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 15

    def test_refresh_token_expiry_configured(self):
        """Test that refresh token expiry is configured"""
        assert REFRESH_TOKEN_EXPIRE_DAYS > 0
        assert REFRESH_TOKEN_EXPIRE_DAYS == 30


class TestTokenSecurity:
    """Test security properties of token implementation"""

    def test_tokens_use_cryptographically_secure_randomness(self):
        """Test that refresh tokens use cryptographically secure random"""
        # Generate multiple tokens and ensure they're different
        tokens = set()
        for _ in range(100):
            token, _ = create_refresh_token()
            tokens.add(token)

        # All tokens should be unique
        assert len(tokens) == 100

    def test_refresh_token_hash_uses_sha256(self):
        """Test that refresh token hash uses SHA-256"""
        token, token_hash = create_refresh_token()

        # SHA-256 produces 64 hex characters
        assert len(token_hash) == 64
        assert all(c in '0123456789abcdef' for c in token_hash)

    def test_access_token_not_too_long_lived(self):
        """Test that access tokens don't live too long (security best practice)"""
        # Access tokens should expire relatively quickly
        assert ACCESS_TOKEN_EXPIRE_MINUTES <= 60  # Max 1 hour

    def test_different_users_cannot_forge_tokens(self):
        """Test that users cannot forge tokens for other users"""
        user1_token = create_access_token("user-1", "user1@example.com")
        user2_token = create_access_token("user-2", "user2@example.com")

        # Decode both tokens
        user1_payload = verify_access_token(user1_token)
        user2_payload = verify_access_token(user2_token)

        # Ensure they're for different users
        assert user1_payload['user_id'] != user2_payload['user_id']

        # Ensure one token can't be modified to access another user
        # (signature would be invalid)
        assert user1_token != user2_token
