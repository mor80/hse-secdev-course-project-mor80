import re
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, EmailStr, Field, field_validator

SAFE_URL_SCHEMES = {"http", "https"}
DISALLOWED_HTML_PATTERN = re.compile(
    r"<\s*/?\s*(script|iframe|object|embed|svg|style|link|img|video|body)", re.IGNORECASE
)
EVENT_HANDLER_PATTERN = re.compile(r"on\w+\s*=", re.IGNORECASE)


def _validate_safe_text(value: Optional[str], field_name: str) -> Optional[str]:
    if value is None:
        return None

    sanitized = value.strip()
    if not sanitized:
        raise ValueError(f"{field_name} cannot be empty or whitespace only")

    lowered = sanitized.lower()
    if "javascript:" in lowered or DISALLOWED_HTML_PATTERN.search(sanitized):
        raise ValueError(f"{field_name} contains disallowed HTML content")

    if EVENT_HANDLER_PATTERN.search(sanitized):
        raise ValueError(f"{field_name} contains HTML event handlers, which are not allowed")

    if any(ord(ch) < 32 and ch not in {"\t", "\n", "\r"} for ch in sanitized):
        raise ValueError(f"{field_name} contains control characters")

    return sanitized


def _validate_safe_link(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    candidate = value.strip()
    if not candidate:
        return None

    if "\n" in candidate or "\r" in candidate:
        raise ValueError("Link cannot contain newline characters")

    parsed = urlparse(candidate)
    scheme = (parsed.scheme or "").lower()
    if scheme not in SAFE_URL_SCHEMES:
        raise ValueError("Link must use HTTPS/HTTP scheme")

    if not parsed.netloc:
        raise ValueError("Link must include a hostname")

    if parsed.username or parsed.password:
        raise ValueError("Credentialed URLs are not allowed")

    if ".." in parsed.path:
        raise ValueError("Link path cannot contain traversal sequences")

    return candidate


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email")
    username: str = Field(..., min_length=3, max_length=50, description="Username")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72, description="Password (max 72 chars)")


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WishBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Wish title")
    link: Optional[str] = Field(None, max_length=500, description="Link to the item")
    price_estimate: Optional[Decimal] = Field(None, ge=0, description="Estimated price")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _validate_safe_text(value, "Title")

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: Optional[str]) -> Optional[str]:
        return _validate_safe_text(value, "Notes")

    @field_validator("link")
    @classmethod
    def validate_link(cls, value: Optional[str]) -> Optional[str]:
        return _validate_safe_link(value)


class WishCreate(WishBase):
    pass


class WishUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    link: Optional[str] = Field(None, max_length=500)
    price_estimate: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("title")
    @classmethod
    def validate_update_title(cls, value: Optional[str]) -> Optional[str]:
        return _validate_safe_text(value, "Title")

    @field_validator("notes")
    @classmethod
    def validate_update_notes(cls, value: Optional[str]) -> Optional[str]:
        return _validate_safe_text(value, "Notes")

    @field_validator("link")
    @classmethod
    def validate_update_link(cls, value: Optional[str]) -> Optional[str]:
        return _validate_safe_link(value)


class WishResponse(WishBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WishListResponse(BaseModel):
    items: List[WishResponse]
    total: int
    limit: int
    offset: int


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=255, description="Login identifier")
    password: str = Field(..., min_length=1, max_length=128, description="User password")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
