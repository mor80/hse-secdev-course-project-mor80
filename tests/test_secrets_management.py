from unittest.mock import patch

from app.services.secrets_service import (
    generate_secure_secret,
    mask_secret,
    rotate_secret,
    sanitize_log_message,
    validate_environment_secrets,
    validate_secret_strength,
)


class TestSecretsManagement:
    """Test secrets management functionality."""

    def test_validate_secret_strength_jwt_key_positive(self):
        """Test valid JWT key validation."""
        # Strong JWT key
        strong_key = "a" * 32 + "b" * 32  # 64 chars with good entropy

        is_valid, error = validate_secret_strength(strong_key, "jwt_key")
        assert is_valid
        assert error == ""

    def test_validate_secret_strength_jwt_key_negative(self):
        """Test invalid JWT key validation."""
        # Weak JWT key
        weak_key = "123"  # Too short

        is_valid, error = validate_secret_strength(weak_key, "jwt_key")
        assert not is_valid
        assert "at least 32" in error

    def test_validate_secret_strength_jwt_key_insufficient_entropy(self):
        """Test JWT key with insufficient entropy."""
        # Key with low entropy
        low_entropy_key = "a" * 50  # All same character

        is_valid, error = validate_secret_strength(low_entropy_key, "jwt_key")
        assert not is_valid
        assert "insufficient entropy" in error

    def test_validate_secret_strength_db_password_positive(self):
        """Test valid database password validation."""
        # Strong database password
        strong_password = "MyStr0ng!Pass123"

        is_valid, error = validate_secret_strength(strong_password, "db_password")
        assert is_valid
        assert error == ""

    def test_validate_secret_strength_db_password_negative(self):
        """Test invalid database password validation."""
        # Weak database password
        weak_password = "123456"  # Too simple

        is_valid, error = validate_secret_strength(weak_password, "db_password")
        assert not is_valid
        assert "at least 12" in error

    def test_validate_secret_strength_db_password_complexity(self):
        """Test database password complexity requirements."""
        # Password missing complexity
        simple_password = "mypassword123"  # No uppercase, no special chars

        is_valid, error = validate_secret_strength(simple_password, "db_password")
        assert not is_valid
        assert "uppercase" in error or "special" in error

    def test_validate_secret_strength_empty_secret(self):
        """Test validation of empty secret."""
        is_valid, error = validate_secret_strength("", "general")
        assert not is_valid
        assert "cannot be empty" in error

    def test_validate_secret_strength_too_short(self):
        """Test validation of too short secret."""
        short_secret = "a" * 10  # Less than minimum 32

        is_valid, error = validate_secret_strength(short_secret, "general")
        assert not is_valid
        assert "too short" in error

    def test_validate_secret_strength_too_long(self):
        """Test validation of too long secret."""
        long_secret = "a" * 200  # More than maximum 128

        is_valid, error = validate_secret_strength(long_secret, "general")
        assert not is_valid
        assert "too long" in error

    def test_generate_secure_secret_jwt_key(self):
        """Test generation of secure JWT key."""
        secret = generate_secure_secret(32, "jwt_key")

        assert len(secret) == 32
        # JWT keys should be base64-url safe
        assert all(c.isalnum() or c in "-_" for c in secret)

    def test_generate_secure_secret_db_password(self):
        """Test generation of secure database password."""
        secret = generate_secure_secret(16, "db_password")

        assert len(secret) >= 16
        # Should contain mixed character types
        has_upper = any(c.isupper() for c in secret)
        has_lower = any(c.islower() for c in secret)
        has_digit = any(c.isdigit() for c in secret)
        has_special = any(c in "@$!%*?&" for c in secret)

        assert has_upper
        assert has_lower
        assert has_digit
        assert has_special

    def test_generate_secure_secret_general(self):
        """Test generation of general secure secret."""
        secret = generate_secure_secret(32, "general")

        assert len(secret) == 32
        # Should be base64-url safe
        assert all(c.isalnum() or c in "-_" for c in secret)

    def test_mask_secret_positive(self):
        """Test secret masking functionality."""
        secret = "my_secret_key_12345"
        masked = mask_secret(secret, show_chars=4)

        assert masked == "***REDACTED***12345"
        assert len(masked) == len("***REDACTED***") + 4

    def test_mask_secret_short_secret(self):
        """Test masking of short secret."""
        secret = "123"
        masked = mask_secret(secret, show_chars=4)

        assert masked == "***REDACTED***"

    def test_mask_secret_empty(self):
        """Test masking of empty secret."""
        secret = ""
        masked = mask_secret(secret)

        assert masked == "***REDACTED***"

    def test_sanitize_log_message(self):
        """Test log message sanitization."""
        message = "User login with password: mypassword123"
        secrets_to_mask = ["mypassword123"]

        sanitized = sanitize_log_message(message, secrets_to_mask)

        assert "mypassword123" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_sanitize_log_message_multiple_secrets(self):
        """Test sanitization with multiple secrets."""
        message = "API key: abc123, secret: xyz789"
        secrets_to_mask = ["abc123", "xyz789"]

        sanitized = sanitize_log_message(message, secrets_to_mask)

        assert "abc123" not in sanitized
        assert "xyz789" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_sanitize_log_message_no_secrets(self):
        """Test sanitization with no secrets to mask."""
        message = "Normal log message"
        secrets_to_mask = []

        sanitized = sanitize_log_message(message, secrets_to_mask)

        assert sanitized == message

    @patch("app.services.secrets_service.validate_secret_strength")
    def test_validate_environment_secrets_positive(self, mock_validate):
        """Test environment secrets validation success."""
        mock_validate.return_value = (True, "")

        # Mock settings
        with patch("app.config.settings") as mock_settings:
            mock_settings.SECRET_KEY = "valid_secret_key_32_chars_minimum"
            mock_settings.DATABASE_URL = "postgresql://user:validpass123@localhost/db"

            is_valid, errors = validate_environment_secrets()

            assert is_valid
            assert len(errors) == 0

    @patch("app.services.secrets_service.validate_secret_strength")
    def test_validate_environment_secrets_negative(self, mock_validate):
        """Test environment secrets validation failure."""
        mock_validate.return_value = (False, "Secret too weak")

        # Mock settings
        with patch("app.config.settings") as mock_settings:
            mock_settings.SECRET_KEY = "weak"
            mock_settings.DATABASE_URL = "postgresql://user:weak@localhost/db"

            is_valid, errors = validate_environment_secrets()

            assert not is_valid
            assert len(errors) > 0
            assert any("SECRET_KEY" in error for error in errors)

    def test_rotate_secret_jwt_key(self):
        """Test JWT key rotation."""
        success, message, new_secret = rotate_secret("jwt_key")

        assert success
        assert "rotation initiated" in message
        assert new_secret is not None
        assert len(new_secret) > 0

    def test_rotate_secret_db_password(self):
        """Test database password rotation."""
        success, message, new_secret = rotate_secret("db_password")

        assert success
        assert "rotation initiated" in message
        assert new_secret is not None
        assert len(new_secret) > 0

    def test_rotate_secret_unknown_type(self):
        """Test rotation of unknown secret type."""
        success, message, new_secret = rotate_secret("unknown_type")

        assert not success
        assert "Unknown secret type" in message
        assert new_secret is None

    def test_secret_validation_edge_cases(self):
        """Test edge cases in secret validation."""
        # Test exactly minimum length
        min_length_secret = "a" * 32
        is_valid, error = validate_secret_strength(min_length_secret, "jwt_key")
        assert is_valid

        # Test exactly maximum length
        max_length_secret = "a" * 128
        is_valid, error = validate_secret_strength(max_length_secret, "general")
        assert is_valid

        # Test one character over maximum
        too_long_secret = "a" * 129
        is_valid, error = validate_secret_strength(too_long_secret, "general")
        assert not is_valid
        assert "too long" in error

    def test_generate_secret_different_lengths(self):
        """Test secret generation with different lengths."""
        # Test minimum length
        secret_16 = generate_secure_secret(16, "general")
        assert len(secret_16) == 16

        # Test longer length
        secret_64 = generate_secure_secret(64, "general")
        assert len(secret_64) == 64

        # Test that secrets are different
        secret_1 = generate_secure_secret(32, "general")
        secret_2 = generate_secure_secret(32, "general")
        assert secret_1 != secret_2

    def test_mask_secret_different_show_chars(self):
        """Test masking with different show_chars values."""
        secret = "my_secret_key_12345"

        # Show 2 characters
        masked_2 = mask_secret(secret, show_chars=2)
        assert masked_2.endswith("45")

        # Show 6 characters
        masked_6 = mask_secret(secret, show_chars=6)
        assert masked_6.endswith("12345")

        # Show more than secret length
        masked_many = mask_secret(secret, show_chars=50)
        assert masked_many == "***REDACTED***"
