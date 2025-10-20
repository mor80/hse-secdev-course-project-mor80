import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.error_handler import (
    authentication_error_response,
    internal_error_response,
    validation_error_response,
)
from app.config import settings

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically convert exceptions to RFC 7807 problem details.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and handle any exceptions with RFC 7807 format.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with problem details on error
        """
        try:
            response = await call_next(request)
            return response

        except RequestValidationError as exc:
            logger.warning(
                f"Validation error: {exc}",
                extra={"path": request.url.path, "method": request.method},
            )

            errors = []
            for error in exc.errors():
                errors.append(
                    {
                        "field": " -> ".join(str(loc) for loc in error["loc"]),
                        "message": error["msg"],
                        "type": error["type"],
                    }
                )

            return validation_error_response(errors, request)

        except HTTPException as exc:
            logger.warning(
                f"HTTP exception: {exc.status_code} - {exc.detail}",
                extra={"path": request.url.path, "method": request.method},
            )

            if exc.status_code == 401:
                return authentication_error_response(str(exc.detail), request)
            elif exc.status_code == 403:
                from app.api.error_handler import authorization_error_response

                return authorization_error_response(str(exc.detail), request)
            elif exc.status_code == 404:
                from app.api.error_handler import not_found_error_response

                return not_found_error_response("Resource", request)
            else:
                return internal_error_response(
                    str(exc.detail), request, production_mode=settings.ENV == "production"
                )

        except Exception as exc:
            logger.error(
                f"Unhandled exception: {type(exc).__name__}: {exc}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            # Convert unhandled exceptions to RFC 7807 format
            return internal_error_response(
                str(exc) if settings.ENV != "production" else "Internal server error",
                request,
                production_mode=settings.ENV == "production",
            )
