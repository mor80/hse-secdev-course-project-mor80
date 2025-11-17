import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Security constants
MAX_FILE_SIZE = 5_000_000  # 5MB
ALLOWED_TYPES = {"image/png", "image/jpeg"}
DEFAULT_UPLOAD_DIR = Path(tempfile.gettempdir()) / "wishlist_secure_uploads"
UPLOAD_DIR = os.getenv("UPLOAD_DIR") or str(DEFAULT_UPLOAD_DIR)

# Magic bytes for file type detection
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SOI = b"\xff\xd8"  # Start of Image
JPEG_EOI = b"\xff\xd9"  # End of Image


def sniff_image_type(data: bytes) -> Optional[str]:
    """
    Detect image type by magic bytes (not MIME type).

    Args:
        data: File content as bytes

    Returns:
        MIME type if detected, None otherwise
    """
    if not data:
        return None

    # Check PNG signature
    if data.startswith(PNG_SIGNATURE):
        return "image/png"

    # Check JPEG signature (starts with SOI, ends with EOI)
    if data.startswith(JPEG_SOI) and data.endswith(JPEG_EOI):
        return "image/jpeg"

    return None


def validate_file_size(data: bytes) -> Tuple[bool, str]:
    """
    Validate file size against security limits.

    Args:
        data: File content as bytes

    Returns:
        (is_valid, error_message)
    """
    if len(data) > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE} bytes"

    if len(data) == 0:
        return False, "Empty file not allowed"

    return True, ""


def validate_file_type(data: bytes) -> Tuple[bool, str]:
    """
    Validate file type using magic bytes detection.

    Args:
        data: File content as bytes

    Returns:
        (is_valid, error_message)
    """
    detected_type = sniff_image_type(data)

    if detected_type is None:
        return False, "Unsupported file type. Only PNG and JPEG images are allowed"

    if detected_type not in ALLOWED_TYPES:
        return False, f"File type {detected_type} not allowed"

    return True, ""


def secure_save(base_dir: str, filename_hint: str, data: bytes) -> Tuple[bool, str, Optional[str]]:
    """
    Securely save file with comprehensive security checks.

    Args:
        base_dir: Base directory for uploads
        filename_hint: Original filename (ignored for security)
        data: File content as bytes

    Returns:
        (success, error_message, saved_path)
    """
    try:
        # 1. Validate file size
        size_valid, size_error = validate_file_size(data)
        if not size_valid:
            logger.warning(f"File size validation failed: {size_error}")
            return False, size_error, None

        # 2. Validate file type using magic bytes
        type_valid, type_error = validate_file_type(data)
        if not type_valid:
            logger.warning(f"File type validation failed: {type_error}")
            return False, type_error, None

        # 3. Ensure upload directory exists
        upload_path = Path(base_dir).resolve(strict=True)
        upload_path.mkdir(parents=True, exist_ok=True)

        # 4. Generate secure filename (UUID + proper extension)
        detected_type = sniff_image_type(data)
        extension = ".png" if detected_type == "image/png" else ".jpg"
        secure_filename = f"{uuid.uuid4()}{extension}"

        # 5. Build final path with canonicalization
        final_path = (upload_path / secure_filename).resolve()

        # 6. Security check: ensure path is within upload directory
        if not str(final_path).startswith(str(upload_path)):
            logger.error(f"Path traversal attempt detected: {final_path}")
            return False, "Path traversal attack detected", None

        # 7. Check for symlinks in parent directories (security)
        for parent in final_path.parents:
            if parent.is_symlink():
                logger.error(f"Symlink detected in parent path: {parent}")
                return False, "Symlink in parent directory not allowed", None

        # 8. Write file atomically
        temp_path = final_path.with_suffix(final_path.suffix + ".tmp")
        try:
            with open(temp_path, "wb") as f:
                f.write(data)

            # Atomic move (prevents partial writes)
            temp_path.rename(final_path)

            logger.info(f"File saved securely: {final_path}")
            return True, "", str(final_path)

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise e

    except Exception as e:
        logger.error(f"File save error: {e}", exc_info=True)
        return False, f"File save failed: {str(e)}", None


def get_file_info(file_path: str) -> Optional[dict]:
    """
    Get secure file information.

    Args:
        file_path: Path to the file

    Returns:
        File info dict or None if not found
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return None

        # Security check: ensure file is within upload directory
        upload_path = Path(UPLOAD_DIR).resolve()
        if not str(path.resolve()).startswith(str(upload_path)):
            logger.warning(f"Access attempt outside upload directory: {file_path}")
            return None

        stat = path.stat()
        return {
            "filename": path.name,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
        }

    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        return None


def delete_file(file_path: str) -> bool:
    """
    Securely delete a file.

    Args:
        file_path: Path to the file

    Returns:
        True if deleted successfully
    """
    try:
        path = Path(file_path)

        # Security check: ensure file is within upload directory
        upload_path = Path(UPLOAD_DIR).resolve()
        if not str(path.resolve()).startswith(str(upload_path)):
            logger.warning(f"Delete attempt outside upload directory: {file_path}")
            return False

        if path.exists():
            path.unlink()
            logger.info(f"File deleted: {file_path}")
            return True

        return False

    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return False


def ensure_upload_directory() -> bool:
    """
    Ensure upload directory exists with proper permissions.

    Returns:
        True if directory is ready
    """
    try:
        upload_path = Path(UPLOAD_DIR)
        upload_path.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions (owner only)
        os.chmod(upload_path, 0o700)

        logger.info(f"Upload directory ready: {upload_path}")
        return True

    except Exception as e:
        logger.error(f"Error setting up upload directory: {e}")
        return False
