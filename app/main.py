import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/health")
async def health():
    return {"status": "ok", "service": "wishlist-api"}


@app.get("/")
async def root():
    return {"message": "Wishlist API", "version": "1.0.0", "docs": "/docs"}
