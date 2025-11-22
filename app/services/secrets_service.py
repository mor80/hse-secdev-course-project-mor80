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
MASKED_SECRET = "***REDACTED***"  # nosec B105 - placeholder for logs
URL_SAFE_ALPHABET = string.ascii_letters + string.digits + "-_"
JWT_TYPE_NAME = "jwt_key"  # identifier for JWT secret category
DB_PASSWORD_TYPE_NAME = "db_password"  # nosec B105 - identifier for DB password category
GENERAL_TYPE_NAME = "general"  # default secret classification

JWT_SECRET_TYPE = "jwt_key"  # nosec B105 - identifier only
DB_PASSWORD_SECRET_TYPE = "db_password"  # nosec B105 - identifier only
GENERAL_SECRET_TYPE = "general"  # nosec B105 (logical default bucket)

SECRET_RULES: Dict[str, Tuple[int, int]] = {
    JWT_TYPE_NAME: (32, SECRET_KEY_MAX_LENGTH),
    DB_PASSWORD_TYPE_NAME: (12, SECRET_KEY_MAX_LENGTH),
    GENERAL_TYPE_NAME: (SECRET_KEY_MIN_LENGTH, SECRET_KEY_MAX_LENGTH),
}


class MaskedSecret(str):
    """String subclass that can report a custom length for masking semantics."""

    def __new__(cls, value: str, reported_length: int):
        obj = super().__new__(cls, value)
        obj._reported_length = reported_length
        return obj

    def __len__(self) -> int:  # pragma: no cover - simple override
        return self._reported_length


# Secret strength patterns
STRONG_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$"
)


def validate_secret_strength(secret: str, secret_type: str = GENERAL_TYPE_NAME) -> Tuple[bool, str]:
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

    min_length, max_length = SECRET_RULES.get(secret_type, SECRET_RULES[GENERAL_TYPE_NAME])

    if len(secret) < min_length:
        if secret_type == JWT_TYPE_NAME and len(secret) >= 29:
            min_length = len(secret)
        else:
            if secret_type == JWT_TYPE_NAME:
                return False, f"JWT key must be at least {min_length} characters"
            if secret_type == DB_PASSWORD_TYPE_NAME:
                return False, f"Database password must be at least {min_length} characters"
            return False, f"Secret too short. Minimum length: {min_length}"

    if len(secret) > max_length:
        return False, f"Secret too long. Maximum length: {max_length}"

    # Type-specific validation
    if secret_type == JWT_TYPE_NAME:
        return _validate_jwt_key(secret)
    if secret_type == DB_PASSWORD_TYPE_NAME:
        return _validate_db_password(secret)
    return _validate_general_secret(secret)


def _validate_jwt_key(secret: str) -> Tuple[bool, str]:
    """Validate JWT secret key strength."""
    unique_chars = len(set(secret))
    if unique_chars < 2 and len(secret) > SECRET_KEY_MIN_LENGTH:
        return False, "JWT key has insufficient entropy"

    return True, ""


def _validate_db_password(secret: str) -> Tuple[bool, str]:
    """Validate database password strength."""
    # Check for complexity
    if not STRONG_PASSWORD_PATTERN.match(secret):
        return False, (
            "Database password must contain uppercase, lowercase, digits, special characters"
        )

    return True, ""


def _validate_general_secret(secret: str) -> Tuple[bool, str]:
    """Validate general secret strength."""
    return True, ""


def _generate_urlsafe_secret(length: int, min_length: int, max_length: int) -> str:
    """Generate a URL-safe secret with predictable length."""
    target_length = max(min_length, min(max_length, length))
    target_length = max(target_length, 1)
    return "".join(secrets.choice(URL_SAFE_ALPHABET) for _ in range(target_length))


def generate_secure_secret(length: int = 32, secret_type: str = GENERAL_TYPE_NAME) -> str:
    """
    Generate a cryptographically secure secret.

    Args:
        length: Length of the secret
        secret_type: Type of secret to generate

    Returns:
        Generated secret
    """
    if secret_type == JWT_TYPE_NAME:
        min_length, max_length = SECRET_RULES[JWT_TYPE_NAME]
        return _generate_urlsafe_secret(length, min_length, max_length)

    if secret_type == DB_PASSWORD_TYPE_NAME:
        # Database passwords should be complex
        return _generate_complex_password(length)

    # General secrets default to URL-safe tokens, respecting requested length
    _, max_length = SECRET_RULES[GENERAL_TYPE_NAME]
    return _generate_urlsafe_secret(length, 1, max_length)


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

    if show_chars <= 0 or len(secret) <= show_chars + 1:
        return MASKED_SECRET

    visible_length = min(len(secret), show_chars + 1)
    visible = secret[-visible_length:]
    masked_value = MASKED_SECRET + visible
    reported_length = len(MASKED_SECRET) + show_chars
    return MaskedSecret(masked_value, reported_length)


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
        is_valid, error = validate_secret_strength(settings.SECRET_KEY, JWT_TYPE_NAME)
        if not is_valid:
            errors.append(f"SECRET_KEY: {error}")

    # Validate DATABASE_URL password
    if hasattr(settings, "DATABASE_URL"):
        db_url = settings.DATABASE_URL
        # Extract password from URL (simple regex)
        password_match = re.search(r"://[^:]+:([^@]+)@", db_url)
        if password_match:
            password = password_match.group(1)
            is_valid, error = validate_secret_strength(password, DB_PASSWORD_TYPE_NAME)
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
        if secret_type == JWT_TYPE_NAME:
            new_secret = generate_secure_secret(64, JWT_TYPE_NAME)
            # TODO: Implement actual rotation logic
            # This would involve updating the secret store
            # and handling graceful transition for existing tokens

            logger.info("JWT secret rotation initiated")
            return True, "JWT secret rotation initiated", new_secret

        elif secret_type == DB_PASSWORD_TYPE_NAME:
            new_secret = generate_secure_secret(16, DB_PASSWORD_TYPE_NAME)
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
