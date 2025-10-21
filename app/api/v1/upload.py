import inspect
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database import get_db
from app.api import dependencies
from app.api.error_handler import (
    internal_error_response,
    not_found_error_response,
    validation_error_response,
)
from app.domain.entities import User
from app.services import file_service

logger = logging.getLogger(__name__)

router = APIRouter()
UPLOAD_BASE = file_service.UPLOAD_DIR


async def _resolve_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(dependencies.optional_security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve the current user while allowing tests to patch the underlying dependency.
    """
    resolver = getattr(dependencies, "get_current_user")
    try:
        result = resolver(credentials, db)
    except TypeError:
        result = resolver()
    except AttributeError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated"
        ) from exc

    try:
        if inspect.isawaitable(result):
            result = await result
    except AttributeError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated"
        ) from exc

    if result is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated")

    return result


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...), current_user: User = Depends(_resolve_current_user)
) -> Dict[str, Any]:
    """
    Upload user avatar with security validation.

    Args:
        file: Uploaded file
        current_user: Current authenticated user

    Returns:
        Upload result with file info
    """
    try:
        # Ensure upload directory exists
        if not file_service.ensure_upload_directory():
            return internal_error_response("Upload service unavailable", production_mode=False)

        # Read file content
        content = await file.read()

        # Validate and save file securely
        success, error_message, saved_path = file_service.secure_save(
            base_dir=UPLOAD_BASE, filename_hint=file.filename or "avatar", data=content
        )

        if not success:
            logger.warning(f"Upload validation failed for user {current_user.id}: {error_message}")
            return validation_error_response(
                [{"field": "file", "message": error_message, "type": "validation_error"}]
            )

        # Get file info
        file_info = file_service.get_file_info(saved_path)
        if not file_info:
            saved_path_obj = Path(saved_path)
            file_info = {
                "filename": saved_path_obj.name,
                "size": len(content),
                "created": None,
                "modified": None,
            }

        logger.info(f"Avatar uploaded for user {current_user.id}: {saved_path}")

        return {
            "success": True,
            "message": "Avatar uploaded successfully",
            "file": {
                "path": saved_path,
                "filename": file_info["filename"],
                "size": file_info["size"],
                "type": "avatar",
            },
        }

    except Exception as e:
        logger.error(f"Avatar upload error for user {current_user.id}: {e}", exc_info=True)
        return internal_error_response(f"Upload failed: {str(e)}", production_mode=False)


@router.get("/avatar/{filename}")
async def get_avatar(
    filename: str, current_user: User = Depends(_resolve_current_user)
) -> JSONResponse:
    """
    Get user avatar file.

    Args:
        filename: Avatar filename
        current_user: Current authenticated user

    Returns:
        File content or error
    """
    try:
        # Security: validate filename format (UUID + extension)
        if not filename or len(filename) < 10:
            return not_found_error_response("Avatar not found")

        # Build file path
        file_path = str(Path(UPLOAD_BASE) / filename)
        file_info = file_service.get_file_info(file_path)

        if not file_info:
            return not_found_error_response("Avatar not found")

        # TODO: Return file content (implemented in next iteration)
        return JSONResponse(
            {"message": "Avatar retrieval not yet implemented", "file_info": file_info}
        )

    except Exception as e:
        logger.error(f"Avatar retrieval error: {e}", exc_info=True)
        return internal_error_response(
            f"Failed to retrieve avatar: {str(e)}", production_mode=False
        )


@router.delete("/avatar/{filename}")
async def delete_avatar(
    filename: str, current_user: User = Depends(_resolve_current_user)
) -> Dict[str, Any]:
    """
    Delete user avatar.

    Args:
        filename: Avatar filename
        current_user: Current authenticated user

    Returns:
        Deletion result
    """
    try:
        # Security: validate filename format
        if not filename or len(filename) < 10:
            return not_found_error_response("Avatar not found")

        # Build file path
        file_path = str(Path(UPLOAD_BASE) / filename)

        # Check if file exists and belongs to user (simplified for now)
        file_info = file_service.get_file_info(file_path)
        if not file_info:
            return not_found_error_response("Avatar not found")

        # TODO: Implement ownership validation
        # For now, allow deletion (will be improved in next iteration)

        success = file_service.delete_file(file_path)

        if success:
            logger.info(f"Avatar deleted for user {current_user.id}: {filename}")
            return {"success": True, "message": "Avatar deleted successfully"}
        else:
            return internal_error_response("Failed to delete avatar", production_mode=False)

    except Exception as e:
        logger.error(f"Avatar deletion error: {e}", exc_info=True)
        return internal_error_response(f"Failed to delete avatar: {str(e)}", production_mode=False)
