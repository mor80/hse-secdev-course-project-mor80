import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handler import (
    authentication_error_response,
    authorization_error_response,
    not_found_error_response,
    problem_response,
    validation_error_response,
)
from app.api.error_middleware import ErrorHandlingMiddleware
from app.api.middleware import RequestLoggingMiddleware
from app.api.v1 import admin, auth, upload, wishes
from app.config import settings


# Configure logging with custom formatter to handle missing request_id
class RequestIDFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "N/A"
        return super().format(record)


# Set up logging
handler = logging.StreamHandler()
handler.setFormatter(
    RequestIDFormatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"message": "%(message)s", "request_id": "%(request_id)s"}',
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler],
)

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME, version="1.0.0", description="Secure Wishlist API")

# Add error handling middleware first (outermost)
app.add_middleware(ErrorHandlingMiddleware)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.CORS_ORIGINS
        if settings.CORS_ORIGINS
        else ["http://localhost:3000", "http://localhost:8000"]
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(wishes.router, prefix="/api/v1/wishes", tags=["wishes"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["file-upload"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

# Add exception handlers for RFC 7807 compliance


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with RFC 7807 format."""
    if exc.status_code == 400:
        return problem_response(
            status_code=400,
            title="Bad Request",
            detail=str(exc.detail),
            type_uri="https://api.wishlist.com/errors/bad-request",
            instance=request.url.path,
            request=request,
        )
    elif exc.status_code == 401:
        return authentication_error_response(str(exc.detail), request)
    elif exc.status_code == 403:
        return authorization_error_response(str(exc.detail), request)
    elif exc.status_code == 404:
        return not_found_error_response("Resource", request)
    elif exc.status_code == 409:
        return problem_response(
            status_code=409,
            title="Conflict",
            detail=str(exc.detail),
            type_uri="https://api.wishlist.com/errors/conflict",
            instance=request.url.path,
            request=request,
        )
    else:
        from app.api.error_handler import internal_error_response

        return internal_error_response(
            str(exc.detail), request, production_mode=settings.ENV == "production"
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with RFC 7807 format."""
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


@app.get("/health")
async def health():
    return {"status": "ok", "service": "wishlist-api"}


@app.get("/")
async def root():
    return {"message": "Wishlist API", "version": "1.0.0", "docs": "/docs"}
