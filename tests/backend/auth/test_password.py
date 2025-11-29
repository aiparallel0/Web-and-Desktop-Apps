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
