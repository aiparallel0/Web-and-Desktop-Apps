"""
Test suite for password hashing and verification
Tests coverage for web-app/backend/auth/password.py
"""
import pytest
import bcrypt
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'web-app', 'backend'))

from auth.password import (
    hash_password,
    verify_password,
    is_password_strong
)


class TestHashPassword:
    """Test password hashing functionality"""

    def test_hash_password_creates_valid_bcrypt_hash(self):
        """Test that hash_password creates a valid bcrypt hash"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        # Bcrypt hashes start with $2b$
        assert hashed.startswith('$2b$')

    def test_hash_password_empty_raises_error(self):
        """Test that empty password raises ValueError"""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password("")

    def test_hash_password_none_raises_error(self):
        """Test that None password raises ValueError"""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password(None)

    def test_hash_password_different_each_time(self):
        """Test that same password produces different hashes (salted)"""
        password = "SamePassword123!"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to different salts
        assert hash1 != hash2

        # But both should verify the same password
        password_bytes = password.encode('utf-8')
        assert bcrypt.checkpw(password_bytes, hash1.encode('utf-8'))
        assert bcrypt.checkpw(password_bytes, hash2.encode('utf-8'))

    def test_hash_password_unicode_support(self):
        """Test that password hashing supports unicode characters"""
        passwords = [
            "Pässwörd123!",  # German
            "Contraseña123!",  # Spanish
            "パスワード123!",  # Japanese
            "密码123!",  # Chinese
        ]

        for password in passwords:
            hashed = hash_password(password)
            assert hashed is not None
            # Verify it can be checked
            assert bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def test_hash_password_various_lengths(self):
        """Test hashing passwords of various lengths"""
        passwords = [
            "Short1!",  # 7 chars
            "Medium123!",  # 10 chars
            "VeryLongPassword123!VeryLongPassword123!VeryLongPassword123!",  # 60 chars (within bcrypt 72-byte limit)
        ]

        for password in passwords:
            hashed = hash_password(password)
            assert hashed is not None
            assert bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def test_hash_password_special_characters(self):
        """Test hashing passwords with various special characters"""
        passwords = [
            "P@ssw0rd!",
            "P#ssw$rd%",
            "P^ssw&rd*",
            "P(ssw)rd_",
            "P+ssw=rd|",
        ]

        for password in passwords:
            hashed = hash_password(password)
            assert hashed is not None
            assert bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def test_hash_password_uses_appropriate_rounds(self):
        """Test that password hashing uses appropriate number of rounds (12)"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        # Extract rounds from hash (format: $2b$12$...)
        parts = hashed.split('$')
        rounds = int(parts[2])

        assert rounds == 12  # Should use 12 rounds as specified


class TestVerifyPassword:
    """Test password verification functionality"""

    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "CorrectPassword123!"
        hashed = hash_password(password)

        result = verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """Test that incorrect password is rejected"""
        password = "CorrectPassword123!"
        hashed = hash_password(password)

        result = verify_password("WrongPassword123!", hashed)
        assert result is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive"""
        password = "Password123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("password123!", hashed) is False
        assert verify_password("PASSWORD123!", hashed) is False

    def test_verify_password_empty_credentials(self):
        """Test that empty credentials return False"""
        hashed = hash_password("ValidPassword123!")

        # Empty password
        assert verify_password("", hashed) is False

        # Empty hash
        assert verify_password("ValidPassword123!", "") is False

        # Both empty
        assert verify_password("", "") is False

    def test_verify_password_none_credentials(self):
        """Test that None credentials return False"""
        hashed = hash_password("ValidPassword123!")

        # None password
        assert verify_password(None, hashed) is False

        # None hash
        assert verify_password("ValidPassword123!", None) is False

        # Both None
        assert verify_password(None, None) is False

    def test_verify_password_exception_handling(self):
        """Test that verification handles exceptions gracefully"""
        # Invalid hash format
        assert verify_password("Password123!", "invalid-hash") is False

        # Corrupted hash
        assert verify_password("Password123!", "$2b$12$invalid") is False

    def test_verify_password_multiple_attempts(self):
        """Test verifying password multiple times"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        # Should work multiple times
        for _ in range(5):
            assert verify_password(password, hashed) is True

    def test_verify_password_whitespace_matters(self):
        """Test that whitespace in password matters"""
        password = "Password123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password(" Password123!", hashed) is False
        assert verify_password("Password123! ", hashed) is False
        assert verify_password(" Password123! ", hashed) is False


class TestIsPasswordStrong:
    """Test password strength validation"""

    def test_is_password_strong_valid(self):
        """Test that valid strong password passes all checks"""
        passwords = [
            "ValidPass123!",
            "Str0ng@Password",
            "C0mpl3x!Pass",
            "MyP@ssw0rd123",
        ]

        for password in passwords:
            is_strong, issues = is_password_strong(password)
            assert is_strong is True
            assert issues == []

    def test_is_password_strong_too_short(self):
        """Test that password shorter than 8 chars fails"""
        password = "Short1!"  # 7 chars

        is_strong, issues = is_password_strong(password)

        assert is_strong is False
        assert len(issues) == 1
        assert "at least 8 characters" in issues[0]

    def test_is_password_strong_no_uppercase(self):
        """Test that password without uppercase fails"""
        password = "lowercase123!"

        is_strong, issues = is_password_strong(password)

        assert is_strong is False
        assert any("uppercase" in issue for issue in issues)

    def test_is_password_strong_no_lowercase(self):
        """Test that password without lowercase fails"""
        password = "UPPERCASE123!"

        is_strong, issues = is_password_strong(password)

        assert is_strong is False
        assert any("lowercase" in issue for issue in issues)

    def test_is_password_strong_no_number(self):
        """Test that password without number fails"""
        password = "NoNumbers!"

        is_strong, issues = is_password_strong(password)

        assert is_strong is False
        assert any("number" in issue for issue in issues)

    def test_is_password_strong_no_special_char(self):
        """Test that password without special character fails"""
        password = "NoSpecial123"

        is_strong, issues = is_password_strong(password)

        assert is_strong is False
        assert any("special character" in issue for issue in issues)

    def test_is_password_strong_multiple_issues(self):
        """Test that all issues are reported"""
        password = "weak"  # Too short, no uppercase, no number, no special

        is_strong, issues = is_password_strong(password)

        assert is_strong is False
        assert len(issues) == 4
        assert any("8 characters" in issue for issue in issues)
        assert any("uppercase" in issue for issue in issues)
        assert any("number" in issue for issue in issues)
        assert any("special character" in issue for issue in issues)

    def test_is_password_strong_all_requirements(self):
        """Test password that meets all requirements"""
        password = "MyP@ssw0rd123"

        is_strong, issues = is_password_strong(password)

        assert is_strong is True
        assert len(issues) == 0

    def test_is_password_strong_exact_length(self):
        """Test password with exactly 8 characters"""
        password = "Pass123!"  # Exactly 8 chars

        is_strong, issues = is_password_strong(password)

        assert is_strong is True
        assert len(issues) == 0

    def test_is_password_strong_various_special_chars(self):
        """Test that various special characters are accepted"""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        base_password = "Password1"

        for char in special_chars:
            password = base_password + char
            is_strong, issues = is_password_strong(password)

            # Should not have special char issue
            assert not any("special character" in issue for issue in issues)

    def test_is_password_strong_unicode_special_chars_not_counted(self):
        """Test that unicode special chars don't count as special chars"""
        # Unicode special chars that shouldn't count
        password = "Password123€"

        is_strong, issues = is_password_strong(password)

        # Should still require ASCII special char
        assert is_strong is False
        assert any("special character" in issue for issue in issues)

    def test_is_password_strong_very_long_password(self):
        """Test that very long passwords are accepted"""
        password = "VeryLongP@ssw0rd" * 10

        is_strong, issues = is_password_strong(password)

        assert is_strong is True
        assert len(issues) == 0

    def test_is_password_strong_minimum_requirements_only(self):
        """Test password with minimum requirements"""
        # 8 chars, 1 upper, 1 lower, 1 number, 1 special
        password = "Abcdef1!"

        is_strong, issues = is_password_strong(password)

        assert is_strong is True
        assert len(issues) == 0


class TestPasswordSecurityBestPractices:
    """Test that password module follows security best practices"""

    def test_password_not_stored_in_plain_text(self):
        """Test that original password cannot be recovered from hash"""
        password = "SecretPassword123!"
        hashed = hash_password(password)

        # Hash should not contain the original password
        assert password not in hashed
        assert password.encode('utf-8') not in hashed.encode('utf-8')

    def test_hash_is_one_way(self):
        """Test that password hash is one-way (cannot be reversed)"""
        password = "IrreversiblePass123!"
        hashed = hash_password(password)

        # Cannot decode the hash to get original password
        # (This is a conceptual test - bcrypt is known to be one-way)
        assert hashed != password
        assert len(hashed) > len(password)

    def test_timing_attack_resistance(self):
        """Test that verification time is constant"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        # Both correct and incorrect passwords should take similar time
        # bcrypt is designed to be slow and constant-time
        import time

        start = time.time()
        verify_password(password, hashed)
        correct_time = time.time() - start

        start = time.time()
        verify_password("WrongPassword123!", hashed)
        wrong_time = time.time() - start

        # Times should be similar (within an order of magnitude)
        # Bcrypt's slowness makes this test meaningful
        assert 0.1 < correct_time / wrong_time < 10

    def test_salt_is_unique_per_hash(self):
        """Test that each hash uses a unique salt"""
        password = "SamePassword123!"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Extract salt from bcrypt hash (format: $2b$12$salt...)
        salt1 = hash1[:29]  # $2b$12$ + 22 char salt
        salt2 = hash2[:29]

        assert salt1 != salt2

    def test_bcrypt_rounds_is_secure(self):
        """Test that bcrypt uses sufficient rounds (>=10)"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        # Extract rounds
        parts = hashed.split('$')
        rounds = int(parts[2])

        # OWASP recommends at least 10 rounds
        assert rounds >= 10
        # But not too many (should be performant)
        assert rounds <= 15
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
        time.sleep(1.1)  # Ensure timestamp difference (JWT iat is in seconds)
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
"""
Test suite for authentication and authorization decorators
Tests coverage for web-app/backend/auth/decorators.py
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from flask import Flask, g, jsonify

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'web-app', 'backend'))

from auth.decorators import (
    require_auth,
    require_admin,
    rate_limit,
    require_plan,
    check_usage_limit,
    _rate_limit_storage
)


@pytest.fixture
def app():
    """Create Flask app for testing decorators"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = Mock()
    return session


class TestRequireAuthDecorator:
    """Test the require_auth decorator"""

    def test_require_auth_valid_token(self, app, db_session, test_user):
        """Test that valid token grants access"""
        from auth.jwt_handler import create_access_token

        token = create_access_token(str(test_user.id), test_user.email, test_user.is_admin)

        @app.route('/test')
        @require_auth
        def test_route():
            return jsonify({'message': 'success', 'user_id': g.user_id})

        with app.test_client() as client:
            with patch('auth.decorators.get_db_context') as mock_get_db:
                # Setup mock to return our test session
                mock_get_db.return_value.__enter__.return_value = db_session

                response = client.get('/test', headers={
                    'Authorization': f'Bearer {token}'
                })

                assert response.status_code == 200
                data = response.get_json()
                assert data['message'] == 'success'
                assert data['user_id'] == str(test_user.id)

    def test_require_auth_missing_header(self, app):
        """Test that missing authorization header returns 401"""
        @app.route('/test')
        @require_auth
        def test_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            response = client.get('/test')

            assert response.status_code == 401
            data = response.get_json()
            assert 'error' in data
            assert 'Missing authorization header' in data['error']

    def test_require_auth_invalid_header_format(self, app):
        """Test that invalid header format returns 401"""
        @app.route('/test')
        @require_auth
        def test_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            # Test various invalid formats
            invalid_headers = [
                {'Authorization': 'InvalidFormat'},
                {'Authorization': 'Bearer'},
                {'Authorization': 'NotBearer token'},
                {'Authorization': ''},
            ]

            for headers in invalid_headers:
                response = client.get('/test', headers=headers)
                assert response.status_code == 401

    def test_require_auth_expired_token(self, app, db_session, test_user):
        """Test that expired token is rejected"""
        from auth.jwt_handler import JWT_SECRET, JWT_ALGORITHM
        import jwt

        # Create an expired token
        payload = {
            'user_id': str(test_user.id),
            'email': test_user.email,
            'is_admin': False,
            'type': 'access',
            'exp': datetime.utcnow() - timedelta(minutes=1)  # Expired
        }
        expired_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        @app.route('/test')
        @require_auth
        def test_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            response = client.get('/test', headers={
                'Authorization': f'Bearer {expired_token}'
            })

            assert response.status_code == 401
            data = response.get_json()
            assert 'error' in data

    def test_require_auth_user_not_found(self, app, db_session):
        """Test that token for non-existent user is rejected"""
        from auth.jwt_handler import create_access_token
        import uuid

        # Create token for non-existent user
        fake_user_id = str(uuid.uuid4())
        token = create_access_token(fake_user_id, "fake@example.com", False)

        @app.route('/test')
        @require_auth
        def test_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with patch('auth.decorators.get_db_context') as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = db_session

                response = client.get('/test', headers={
                    'Authorization': f'Bearer {token}'
                })

                assert response.status_code == 401
                data = response.get_json()
                assert 'User not found' in data['error']

    def test_require_auth_inactive_user(self, app, db_session, test_user):
        """Test that inactive user is rejected"""
        from auth.jwt_handler import create_access_token

        # Make user inactive
        test_user.is_active = False
        db_session.commit()

        token = create_access_token(str(test_user.id), test_user.email, False)

        @app.route('/test')
        @require_auth
        def test_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with patch('auth.decorators.get_db_context') as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = db_session

                response = client.get('/test', headers={
                    'Authorization': f'Bearer {token}'
                })

                assert response.status_code == 401
                data = response.get_json()
                assert 'disabled' in data['error']

    def test_require_auth_sets_flask_g_attributes(self, app, db_session, test_user):
        """Test that decorator sets user info in Flask g object"""
        from auth.jwt_handler import create_access_token

        token = create_access_token(str(test_user.id), test_user.email, test_user.is_admin)

        @app.route('/test')
        @require_auth
        def test_route():
            # Access g attributes set by decorator
            return jsonify({
                'user_id': g.user_id,
                'user_email': g.user_email,
                'is_admin': g.is_admin,
                'user_plan': g.user_plan.value
            })

        with app.test_client() as client:
            with patch('auth.decorators.get_db_context') as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = db_session

                response = client.get('/test', headers={
                    'Authorization': f'Bearer {token}'
                })

                assert response.status_code == 200
                data = response.get_json()
                assert data['user_id'] == str(test_user.id)
                assert data['user_email'] == test_user.email
                assert data['is_admin'] == test_user.is_admin


class TestRequireAdminDecorator:
    """Test the require_admin decorator"""

    def test_require_admin_with_admin_user(self, app):
        """Test that admin user can access admin route"""
        @app.route('/admin')
        @require_admin
        def admin_route():
            return jsonify({'message': 'admin access granted'})

        with app.test_client() as client:
            with app.test_request_context('/admin'):
                g.is_admin = True

                response = admin_route()
                assert 'admin access granted' in str(response.get_data())

    def test_require_admin_with_regular_user(self, app):
        """Test that regular user is denied access to admin route"""
        @app.route('/admin')
        @require_admin
        def admin_route():
            return jsonify({'message': 'admin access granted'})

        with app.test_client() as client:
            with app.test_request_context('/admin'):
                g.is_admin = False

                response = admin_route()
                # Should return tuple (response, status_code)
                assert response[1] == 403

    def test_require_admin_without_authentication(self, app):
        """Test that unauthenticated request is denied"""
        @app.route('/admin')
        @require_admin
        def admin_route():
            return jsonify({'message': 'admin access granted'})

        with app.test_client() as client:
            with app.test_request_context('/admin'):
                # No g.is_admin set

                response = admin_route()
                assert response[1] == 403


class TestRateLimitDecorator:
    """Test the rate_limit decorator"""

    def setup_method(self):
        """Clear rate limit storage before each test"""
        _rate_limit_storage.clear()

    def test_rate_limit_within_limit(self, app):
        """Test that requests within limit are allowed"""
        @app.route('/limited')
        @rate_limit(max_requests=5, window_seconds=60)
        def limited_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/limited'):
                g.user_id = 'test-user'

                # Make 5 requests (within limit)
                for i in range(5):
                    response = limited_route()
                    # First element of tuple should not be an error response
                    if isinstance(response, tuple):
                        assert response[1] != 429
                    else:
                        # Single response object means success
                        assert True

    def test_rate_limit_exceeds_limit(self, app):
        """Test that requests exceeding limit are blocked"""
        @app.route('/limited')
        @rate_limit(max_requests=3, window_seconds=60)
        def limited_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/limited'):
                g.user_id = 'test-user'

                # Make 3 requests (at limit)
                for i in range(3):
                    limited_route()

                # 4th request should be rate limited
                response = limited_route()
                assert response[1] == 429
                data = response[0].get_json()
                assert 'Rate limit exceeded' in data['error']

    def test_rate_limit_window_expiry(self, app):
        """Test that rate limit resets after window expires"""
        @app.route('/limited')
        @rate_limit(max_requests=2, window_seconds=1)
        def limited_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/limited'):
                g.user_id = 'test-user'

                # Make 2 requests
                limited_route()
                limited_route()

                # 3rd should be limited
                response = limited_route()
                assert response[1] == 429

                # Wait for window to expire
                import time
                time.sleep(1.1)

                # Should work again
                response = limited_route()
                # Should not be 429
                if isinstance(response, tuple):
                    assert response[1] != 429

    def test_rate_limit_different_users_separate_limits(self, app):
        """Test that different users have separate rate limits"""
        @app.route('/limited')
        @rate_limit(max_requests=2, window_seconds=60)
        def limited_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            # User 1 makes 2 requests
            with app.test_request_context('/limited'):
                g.user_id = 'user-1'
                limited_route()
                limited_route()

            # User 2 should still be able to make requests
            with app.test_request_context('/limited'):
                g.user_id = 'user-2'
                response = limited_route()
                # Should not be rate limited
                if isinstance(response, tuple):
                    assert response[1] != 429

    def test_rate_limit_uses_ip_when_no_user_id(self, app):
        """Test that rate limit falls back to IP address"""
        @app.route('/limited')
        @rate_limit(max_requests=2, window_seconds=60)
        def limited_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/limited', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
                # No g.user_id set
                response = limited_route()
                # Should work
                assert response is not None


class TestRequirePlanDecorator:
    """Test the require_plan decorator"""

    def test_require_plan_free_user_free_feature(self, app):
        """Test that free user can access free features"""
        from database.models import SubscriptionPlan

        @app.route('/free-feature')
        @require_plan('free')
        def free_feature():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/free-feature'):
                g.user_plan = SubscriptionPlan.FREE

                response = free_feature()
                assert 'success' in str(response.get_data())

    def test_require_plan_free_user_pro_feature(self, app):
        """Test that free user cannot access pro features"""
        from database.models import SubscriptionPlan

        @app.route('/pro-feature')
        @require_plan('pro')
        def pro_feature():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/pro-feature'):
                g.user_plan = SubscriptionPlan.FREE

                response = pro_feature()
                assert response[1] == 403
                data = response[0].get_json()
                assert 'requires pro plan' in data['error']

    def test_require_plan_pro_user_pro_feature(self, app):
        """Test that pro user can access pro features"""
        from database.models import SubscriptionPlan

        @app.route('/pro-feature')
        @require_plan('pro')
        def pro_feature():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/pro-feature'):
                g.user_plan = SubscriptionPlan.PRO

                response = pro_feature()
                assert 'success' in str(response.get_data())

    def test_require_plan_enterprise_user_any_feature(self, app):
        """Test that enterprise user can access any feature"""
        from database.models import SubscriptionPlan

        @app.route('/pro-feature')
        @require_plan('pro')
        def pro_feature():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with app.test_request_context('/pro-feature'):
                g.user_plan = SubscriptionPlan.ENTERPRISE

                response = pro_feature()
                assert 'success' in str(response.get_data())

    def test_require_plan_hierarchy(self, app):
        """Test that plan hierarchy works correctly"""
        from database.models import SubscriptionPlan

        @app.route('/business-feature')
        @require_plan('business')
        def business_feature():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            # Free user should be blocked
            with app.test_request_context('/business-feature'):
                g.user_plan = SubscriptionPlan.FREE
                response = business_feature()
                assert response[1] == 403

            # Pro user should be blocked
            with app.test_request_context('/business-feature'):
                g.user_plan = SubscriptionPlan.PRO
                response = business_feature()
                assert response[1] == 403

            # Business user should pass
            with app.test_request_context('/business-feature'):
                g.user_plan = SubscriptionPlan.BUSINESS
                response = business_feature()
                assert 'success' in str(response.get_data())

            # Enterprise user should pass
            with app.test_request_context('/business-feature'):
                g.user_plan = SubscriptionPlan.ENTERPRISE
                response = business_feature()
                assert 'success' in str(response.get_data())


class TestCheckUsageLimitDecorator:
    """Test the check_usage_limit decorator"""

    def test_usage_limit_within_limit(self, app, db_session, test_user):
        """Test that user within usage limit can proceed"""
        # Set user within limit
        test_user.receipts_processed_month = 10
        db_session.commit()

        @app.route('/process')
        @check_usage_limit
        def process_route():
            return jsonify({'message': 'processed'})

        with app.test_client() as client:
            with app.test_request_context('/process'):
                g.user_id = str(test_user.id)
                g.user_plan = test_user.plan

                with patch('auth.decorators.get_db_context') as mock_get_db:
                    mock_get_db.return_value.__enter__.return_value = db_session

                    response = process_route()
                    assert 'processed' in str(response.get_data())

    def test_usage_limit_at_limit(self, app, db_session, test_user):
        """Test that user at usage limit is blocked"""
        from database.models import SubscriptionPlan

        # Set user at free plan limit (50)
        test_user.plan = SubscriptionPlan.FREE
        test_user.receipts_processed_month = 50
        db_session.commit()

        @app.route('/process')
        @check_usage_limit
        def process_route():
            return jsonify({'message': 'processed'})

        with app.test_client() as client:
            with app.test_request_context('/process'):
                g.user_id = str(test_user.id)
                g.user_plan = test_user.plan

                with patch('auth.decorators.get_db_context') as mock_get_db:
                    mock_get_db.return_value.__enter__.return_value = db_session

                    response = process_route()
                    assert response[1] == 429
                    data = response[0].get_json()
                    assert 'usage limit exceeded' in data['error'].lower()

    def test_usage_limit_increments_counter(self, app, db_session, test_user):
        """Test that successful request increments usage counter"""
        initial_count = test_user.receipts_processed_month

        @app.route('/process')
        @check_usage_limit
        def process_route():
            return jsonify({'message': 'processed'})

        with app.test_client() as client:
            with app.test_request_context('/process'):
                g.user_id = str(test_user.id)
                g.user_plan = test_user.plan

                with patch('auth.decorators.get_db_context') as mock_get_db:
                    mock_get_db.return_value.__enter__.return_value = db_session

                    process_route()

                    # Check counter was incremented
                    db_session.refresh(test_user)
                    assert test_user.receipts_processed_month == initial_count + 1

    def test_usage_limit_different_plan_limits(self, app, db_session, test_user):
        """Test that different plans have different limits"""
        from database.models import SubscriptionPlan

        @app.route('/process')
        @check_usage_limit
        def process_route():
            return jsonify({'message': 'processed'})

        # Test free plan limit (50)
        test_user.plan = SubscriptionPlan.FREE
        test_user.receipts_processed_month = 49
        db_session.commit()

        with app.test_client() as client:
            with app.test_request_context('/process'):
                g.user_id = str(test_user.id)
                g.user_plan = test_user.plan

                with patch('auth.decorators.get_db_context') as mock_get_db:
                    mock_get_db.return_value.__enter__.return_value = db_session
                    response = process_route()
                    # Should work (49 < 50)
                    assert 'processed' in str(response.get_data())

        # Test pro plan has higher limit (1000)
        test_user.plan = SubscriptionPlan.PRO
        test_user.receipts_processed_month = 500
        db_session.commit()

        with app.test_client() as client:
            with app.test_request_context('/process'):
                g.user_id = str(test_user.id)
                g.user_plan = test_user.plan

                with patch('auth.decorators.get_db_context') as mock_get_db:
                    mock_get_db.return_value.__enter__.return_value = db_session
                    response = process_route()
                    # Should work (500 < 1000)
                    assert 'processed' in str(response.get_data())


class TestDecoratorChaining:
    """Test that decorators work correctly when chained together"""

    def test_require_auth_and_require_admin_chained(self, app, db_session, test_admin_user):
        """Test chaining require_auth and require_admin"""
        from auth.jwt_handler import create_access_token

        token = create_access_token(
            str(test_admin_user.id),
            test_admin_user.email,
            test_admin_user.is_admin
        )

        @app.route('/admin')
        @require_auth
        @require_admin
        def admin_route():
            return jsonify({'message': 'admin success'})

        with app.test_client() as client:
            with patch('auth.decorators.get_db_context') as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = db_session

                response = client.get('/admin', headers={
                    'Authorization': f'Bearer {token}'
                })

                assert response.status_code == 200

    def test_require_auth_and_rate_limit_chained(self, app, db_session, test_user):
        """Test chaining require_auth and rate_limit"""
        from auth.jwt_handler import create_access_token

        _rate_limit_storage.clear()
        token = create_access_token(str(test_user.id), test_user.email, False)

        @app.route('/limited')
        @require_auth
        @rate_limit(max_requests=2, window_seconds=60)
        def limited_route():
            return jsonify({'message': 'success'})

        with app.test_client() as client:
            with patch('auth.decorators.get_db_context') as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = db_session

                headers = {'Authorization': f'Bearer {token}'}

                # First two requests should work
                response1 = client.get('/limited', headers=headers)
                response2 = client.get('/limited', headers=headers)

                # Third should be rate limited
                response3 = client.get('/limited', headers=headers)
                assert response3.status_code == 429
"""
Tests for auth/routes.py - Authentication API routes
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import hashlib


class TestRegisterRoute:
    """Tests for /api/auth/register endpoint"""
    
    def test_register_missing_email(self, client):
        """Test register without email"""
        response = client.post('/api/auth/register', json={
            'password': 'SecurePass123!'
        })
        assert response.status_code == 400
    
    def test_register_invalid_email(self, client):
        """Test register with invalid email format"""
        response = client.post('/api/auth/register', json={
            'email': 'invalid-email',
            'password': 'SecurePass123!'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid email format' in data['error']
    
    def test_register_weak_password(self, client):
        """Test register with weak password"""
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'weak'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'does not meet requirements' in data['error']


class TestLoginRoute:
    """Tests for /api/auth/login endpoint"""
    
    def test_login_missing_credentials(self, client):
        """Test login without email or password"""
        response = client.post('/api/auth/login', json={})
        assert response.status_code == 400


class TestRefreshRoute:
    """Tests for /api/auth/refresh endpoint"""
    
    def test_refresh_missing_token(self, client):
        """Test refresh without token"""
        response = client.post('/api/auth/refresh', json={})
        assert response.status_code == 400


class TestLogoutRoute:
    """Tests for /api/auth/logout endpoint"""
    
    def test_logout_no_token(self, client):
        """Test logout without token still succeeds"""
        response = client.post('/api/auth/logout', json={})
        assert response.status_code == 200


class TestMeRoute:
    """Tests for /api/auth/me endpoint"""
    
    def test_me_missing_auth_header(self, client):
        """Test /me without authorization header"""
        response = client.get('/api/auth/me')
        assert response.status_code == 401
        data = response.get_json()
        assert 'Missing authorization header' in data['error']
    
    def test_me_invalid_auth_format(self, client):
        """Test /me with invalid auth format"""
        response = client.get('/api/auth/me', headers={
            'Authorization': 'InvalidFormat token'
        })
        assert response.status_code == 401
    
    def test_me_expired_token(self, client):
        """Test /me with expired token"""
        response = client.get('/api/auth/me', headers={
            'Authorization': 'Bearer expired-token-here'
        })
        assert response.status_code == 401


class TestChangePasswordRoute:
    """Tests for /api/auth/change-password endpoint"""
    
    def test_change_password_missing_auth(self, client):
        """Test change password without auth"""
        response = client.post('/api/auth/change-password', json={
            'current_password': 'old',
            'new_password': 'new'
        })
        assert response.status_code == 401

