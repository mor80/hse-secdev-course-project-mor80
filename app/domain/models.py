from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email")
    username: str = Field(..., min_length=3, max_length=50, description="Username")


class UserCreate(UserBase):
    password: str = Field(
        ..., min_length=8, max_length=72, description="Password (max 72 chars)"
    )


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


class WishCreate(WishBase):
    pass


class WishUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    link: Optional[str] = Field(None, max_length=500)
    price_estimate: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=1000)


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


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
