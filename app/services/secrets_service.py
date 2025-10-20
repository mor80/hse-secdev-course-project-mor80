"""
Secrets management service with validation and rotation support.
Implements secure handling of application secrets.
"""

import logging
import re
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Security constants
SECRET_KEY_MIN_LENGTH = 32
SECRET_KEY_MAX_LENGTH = 128
ROTATION_INTERVAL_DAYS = 30
MASKED_SECRET = "***REDACTED***"

# Secret strength patterns
STRONG_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$"
)


def validate_secret_strength(secret: str, secret_type: str = "general") -> Tuple[bool, str]:
    """
    Validate secret strength based on type.

    Args:
        secret: Secret to validate
        secret_type: Type of secret (jwt_key, db_password, etc.)

    Returns:
        (is_valid, error_message)
    """
    if not secret:
        return False, "Secret cannot be empty"

    if len(secret) < SECRET_KEY_MIN_LENGTH:
        return False, f"Secret too short. Minimum length: {SECRET_KEY_MIN_LENGTH}"

    if len(secret) > SECRET_KEY_MAX_LENGTH:
        return False, f"Secret too long. Maximum length: {SECRET_KEY_MAX_LENGTH}"

    # Type-specific validation
    if secret_type == "jwt_key":
        return _validate_jwt_key(secret)
    elif secret_type == "db_password":
        return _validate_db_password(secret)
    else:
        return _validate_general_secret(secret)


def _validate_jwt_key(secret: str) -> Tuple[bool, str]:
    """Validate JWT secret key strength."""
    # JWT keys should be cryptographically strong
    if len(secret) < 32:
        return False, "JWT key must be at least 32 characters"

    # Check for sufficient entropy
    unique_chars = len(set(secret))
    if unique_chars < 16:
        return False, "JWT key has insufficient entropy"

    return True, ""


def _validate_db_password(secret: str) -> Tuple[bool, str]:
    """Validate database password strength."""
    if len(secret) < 12:
        return False, "Database password must be at least 12 characters"

    # Check for complexity
    if not STRONG_PASSWORD_PATTERN.match(secret):
        return False, (
            "Database password must contain: " "uppercase, lowercase, digits, special characters"
        )

    return True, ""


def _validate_general_secret(secret: str) -> Tuple[bool, str]:
    """Validate general secret strength."""
    # Basic entropy check
    unique_chars = len(set(secret))
    if unique_chars < 8:
        return False, "Secret has insufficient entropy"

    return True, ""


def generate_secure_secret(length: int = 32, secret_type: str = "general") -> str:
    """
    Generate a cryptographically secure secret.

    Args:
        length: Length of the secret
        secret_type: Type of secret to generate

    Returns:
        Generated secret
    """
    if secret_type == "jwt_key":
        # JWT keys should be base64-url safe
        return secrets.token_urlsafe(length)
    elif secret_type == "db_password":
        # Database passwords should be complex
        return _generate_complex_password(length)
    else:
        # General secrets
        return secrets.token_urlsafe(length)


def _generate_complex_password(length: int) -> str:
    """Generate a complex password with mixed character types."""
    if length < 12:
        length = 12

    # Ensure we have at least one of each required character type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("@$!%*?&"),
    ]

    # Fill the rest with random characters
    all_chars = string.ascii_letters + string.digits + "@$!%*?&"
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))

    # Shuffle to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)

    return "".join(password)


def mask_secret(secret: str, show_chars: int = 4) -> str:
    """
    Mask secret for logging and display.

    Args:
        secret: Secret to mask
        show_chars: Number of characters to show at the end

    Returns:
        Masked secret
    """
    if not secret:
        return MASKED_SECRET

    if len(secret) <= show_chars:
        return MASKED_SECRET

    return MASKED_SECRET + secret[-show_chars:]


def sanitize_log_message(message: str, secrets_to_mask: List[str]) -> str:
    """
    Sanitize log message by masking secrets.

    Args:
        message: Log message
        secrets_to_mask: List of secrets to mask

    Returns:
        Sanitized message
    """
    sanitized = message

    for secret in secrets_to_mask:
        if secret and secret in sanitized:
            sanitized = sanitized.replace(secret, mask_secret(secret))

    return sanitized


def validate_environment_secrets() -> Tuple[bool, List[str]]:
    """
    Validate all environment secrets on startup.

    Returns:
        (all_valid, list_of_errors)
    """
    errors = []

    # Import here to avoid circular imports
    from app.config import settings

    # Validate SECRET_KEY
    if hasattr(settings, "SECRET_KEY"):
        is_valid, error = validate_secret_strength(settings.SECRET_KEY, "jwt_key")
        if not is_valid:
            errors.append(f"SECRET_KEY: {error}")

    # Validate DATABASE_URL password
    if hasattr(settings, "DATABASE_URL"):
        db_url = settings.DATABASE_URL
        # Extract password from URL (simple regex)
        password_match = re.search(r"://[^:]+:([^@]+)@", db_url)
        if password_match:
            password = password_match.group(1)
            is_valid, error = validate_secret_strength(password, "db_password")
            if not is_valid:
                errors.append(f"DATABASE_PASSWORD: {error}")

    return len(errors) == 0, errors


def get_secret_rotation_status() -> Dict[str, any]:
    """
    Get status of secret rotation.

    Returns:
        Rotation status information
    """
    # This would typically check a database or secure store
    # For now, return mock data
    return {
        "last_rotation": datetime.now() - timedelta(days=15),
        "next_rotation": datetime.now() + timedelta(days=15),
        "rotation_interval_days": ROTATION_INTERVAL_DAYS,
        "requires_rotation": False,
    }


def rotate_secret(secret_type: str) -> Tuple[bool, str, Optional[str]]:
    """
    Rotate a secret (admin operation).

    Args:
        secret_type: Type of secret to rotate

    Returns:
        (success, message, new_secret)
    """
    try:
        if secret_type == "jwt_key":
            new_secret = generate_secure_secret(64, "jwt_key")
            # TODO: Implement actual rotation logic
            # This would involve updating the secret store
            # and handling graceful transition for existing tokens

            logger.info("JWT secret rotation initiated")
            return True, "JWT secret rotation initiated", new_secret

        elif secret_type == "db_password":
            new_secret = generate_secure_secret(16, "db_password")
            # TODO: Implement database password rotation
            # This would involve updating the database user password
            # and updating the connection string

            logger.info("Database password rotation initiated")
            return True, "Database password rotation initiated", new_secret

        else:
            return False, f"Unknown secret type: {secret_type}", None

    except Exception as e:
        logger.error(f"Secret rotation failed: {e}", exc_info=True)
        return False, f"Rotation failed: {str(e)}", None


def audit_secret_access(secret_type: str, operation: str, user_id: Optional[str] = None):
    """
    Audit secret access for security monitoring.

    Args:
        secret_type: Type of secret accessed
        operation: Operation performed (read, rotate, validate)
        user_id: User performing the operation
    """
    logger.info(
        f"Secret access: {secret_type} - {operation}",
        extra={
            "secret_type": secret_type,
            "operation": operation,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
        },
    )
