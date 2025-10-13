import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.middleware import RequestLoggingMiddleware
from app.api.v1 import admin, auth, wishes
from app.config import settings
from app.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DuplicateError,
    NotFoundError,
)
from app.domain.exceptions import ValidationError as DomainValidationError

logging.basicConfig(
    level=logging.INFO,
    format=(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"message": "%(message)s", "request_id": "%(request_id)s"}'
    ),
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME, version="1.0.0", description="Secure Wishlist API")

app.add_middleware(RequestLoggingMiddleware)

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
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Invalid request data",
            "details": exc.errors(),
        },
    )


@app.exception_handler(DomainValidationError)
async def domain_validation_exception_handler(request: Request, exc: DomainValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"code": "VALIDATION_ERROR", "message": str(exc), "details": {}},
    )


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"code": "AUTHENTICATION_ERROR", "message": str(exc), "details": {}},
    )


@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"code": "AUTHORIZATION_ERROR", "message": str(exc), "details": {}},
    )


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"code": "NOT_FOUND", "message": str(exc), "details": {}},
    )


@app.exception_handler(DuplicateError)
async def duplicate_exception_handler(request: Request, exc: DuplicateError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"code": "DUPLICATE_ERROR", "message": str(exc), "details": {}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_ERROR",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code, "message": detail, "details": {}},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"request_id": getattr(request.state, "request_id", "unknown")},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "details": {},
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "wishlist-api"}


@app.get("/")
async def root():
    return {"message": "Wishlist API", "version": "1.0.0", "docs": "/docs"}
