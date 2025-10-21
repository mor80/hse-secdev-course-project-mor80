import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ProblemDetail(BaseModel):
    """RFC 7807 Problem Details model."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str
    correlation_id: str
    instance: Optional[str] = None
    message: Optional[str] = None
    validation_errors: Optional[List[Dict[str, Any]]] = None
    extensions: Optional[Dict[str, Any]] = None


def create_problem(
    status_code: int,
    title: str,
    detail: str,
    type_uri: str = "about:blank",
    instance: Optional[str] = None,
    extensions: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    validation_errors: Optional[List[Dict[str, Any]]] = None,
) -> ProblemDetail:
    """
    Create a standardized problem detail response.

    Args:
        status_code: HTTP status code
        title: Human-readable title
        detail: Detailed error message
        type_uri: URI identifying the problem type
        instance: URI identifying the specific occurrence
        extensions: Additional fields
        request: FastAPI request object for correlation ID

    Returns:
        ProblemDetail object
    """
    correlation_id = str(uuid4())

    # Log the error with correlation ID for debugging
    logger.error(
        f"Error {status_code}: {title} - {detail}",
        extra={
            "correlation_id": correlation_id,
            "status_code": status_code,
            "type_uri": type_uri,
            "instance": instance,
        },
    )

    return ProblemDetail(
        type=type_uri,
        title=title,
        status=status_code,
        detail=detail,
        correlation_id=correlation_id,
        instance=instance,
        message=detail,
        validation_errors=validation_errors,
        extensions=extensions,
    )


def problem_response(
    status_code: int,
    title: str,
    detail: str,
    type_uri: str = "about:blank",
    instance: Optional[str] = None,
    extensions: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    validation_errors: Optional[List[Dict[str, Any]]] = None,
) -> JSONResponse:
    """
    Create a JSONResponse with RFC 7807 problem details.

    Returns:
        JSONResponse with problem details
    """
    problem = create_problem(
        status_code=status_code,
        title=title,
        detail=detail,
        type_uri=type_uri,
        instance=instance,
        extensions=extensions,
        request=request,
        validation_errors=validation_errors,
    )

    return JSONResponse(content=problem.model_dump(exclude_none=True), status_code=status_code)


def validation_error_response(errors: list, request: Optional[Request] = None) -> JSONResponse:
    """
    Create a validation error response following RFC 7807.

    Args:
        errors: List of validation errors
        request: FastAPI request object

    Returns:
        JSONResponse with validation problem details
    """
    return problem_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Validation Error",
        detail="Request validation failed",
        type_uri="https://api.wishlist.com/errors/validation-error",
        instance=request.url.path if request else None,
        validation_errors=errors,
        request=request,
    )


def authentication_error_response(
    detail: str = "Authentication failed", request: Optional[Request] = None
) -> JSONResponse:
    """
    Create an authentication error response.

    Args:
        detail: Error detail message
        request: FastAPI request object

    Returns:
        JSONResponse with auth problem details
    """
    return problem_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        title="Authentication Error",
        detail=detail,
        type_uri="https://api.wishlist.com/errors/auth-error",
        instance=request.url.path if request else None,
        request=request,
    )


def authorization_error_response(
    detail: str = "Insufficient permissions", request: Optional[Request] = None
) -> JSONResponse:
    """
    Create an authorization error response.

    Args:
        detail: Error detail message
        request: FastAPI request object

    Returns:
        JSONResponse with authorization problem details
    """
    return problem_response(
        status_code=status.HTTP_403_FORBIDDEN,
        title="Authorization Error",
        detail=detail,
        type_uri="https://api.wishlist.com/errors/authz-error",
        instance=request.url.path if request else None,
        request=request,
    )


def not_found_error_response(
    resource: str = "Resource", request: Optional[Request] = None
) -> JSONResponse:
    """
    Create a not found error response.

    Args:
        resource: Name of the resource that was not found
        request: FastAPI request object

    Returns:
        JSONResponse with not found problem details
    """
    return problem_response(
        status_code=status.HTTP_404_NOT_FOUND,
        title="Not Found",
        detail=f"{resource} not found",
        type_uri="https://api.wishlist.com/errors/not-found",
        instance=request.url.path if request else None,
        request=request,
    )


def internal_error_response(
    detail: str = "Internal server error",
    request: Optional[Request] = None,
    production_mode: bool = False,
) -> JSONResponse:
    """
    Create an internal server error response.

    Args:
        detail: Error detail message
        request: FastAPI request object
        production_mode: If True, mask sensitive details

    Returns:
        JSONResponse with internal error problem details
    """
    if production_mode:
        detail = "An internal error occurred. Please try again later."

    return problem_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail=detail,
        type_uri="https://api.wishlist.com/errors/internal-error",
        instance=request.url.path if request else None,
        request=request,
    )
