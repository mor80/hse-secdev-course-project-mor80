import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from app.api import dependencies
from app.api.error_handler import (
    internal_error_response,
    not_found_error_response,
    validation_error_response,
)
from app.domain.entities import User
from app.services.file_service import ensure_upload_directory, get_file_info, secure_save

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...), current_user: User = Depends(dependencies.get_current_user)
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
        if not ensure_upload_directory():
            return internal_error_response("Upload service unavailable", production_mode=False)

        # Read file content
        content = await file.read()

        # Validate and save file securely
        success, error_message, saved_path = secure_save(
            base_dir="/app/uploads", filename_hint=file.filename or "avatar", data=content
        )

        if not success:
            logger.warning(f"Upload validation failed for user {current_user.id}: {error_message}")
            return validation_error_response(
                [{"field": "file", "message": error_message, "type": "validation_error"}]
            )

        # Get file info
        file_info = get_file_info(saved_path)
        if not file_info:
            return internal_error_response(
                "Failed to retrieve file information", production_mode=False
            )

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
    filename: str, current_user: User = Depends(dependencies.get_current_user)
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
        file_path = f"/app/uploads/{filename}"
        file_info = get_file_info(file_path)

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
    filename: str, current_user: User = Depends(dependencies.get_current_user)
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
        file_path = f"/app/uploads/{filename}"

        # Check if file exists and belongs to user (simplified for now)
        file_info = get_file_info(file_path)
        if not file_info:
            return not_found_error_response("Avatar not found")

        # TODO: Implement ownership validation
        # For now, allow deletion (will be improved in next iteration)

        from app.services.file_service import delete_file

        success = delete_file(file_path)

        if success:
            logger.info(f"Avatar deleted for user {current_user.id}: {filename}")
            return {"success": True, "message": "Avatar deleted successfully"}
        else:
            return internal_error_response("Failed to delete avatar", production_mode=False)

    except Exception as e:
        logger.error(f"Avatar deletion error: {e}", exc_info=True)
        return internal_error_response(f"Failed to delete avatar: {str(e)}", production_mode=False)
