from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database import get_db
from app.adapters.repositories.wish_repository import WishRepository
from app.api import dependencies
from app.domain.entities import User, UserRole
from app.domain.models import WishCreate, WishListResponse, WishResponse, WishUpdate

router = APIRouter()


@router.post("/", response_model=WishResponse, status_code=status.HTTP_201_CREATED)
async def create_wish(
    wish: WishCreate,
    current_user: User = Depends(dependencies.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    repository = WishRepository(db)
    db_wish = await repository.create(wish, current_user.id)
    return db_wish


@router.get("/{wish_id}", response_model=WishResponse)
async def get_wish(
    wish_id: int,
    current_user: Optional[User] = Depends(dependencies.get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    repository = WishRepository(db)
    if current_user is None:
        owner_id = None
    else:
        owner_id = None if current_user.role == UserRole.ADMIN.value else current_user.id
    db_wish = await repository.get_by_id(wish_id, owner_id)
    if not db_wish:
        raise HTTPException(status_code=404, detail="Wish not found")
    return db_wish


@router.get("/", response_model=WishListResponse)
async def get_wishes(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    price_filter: Optional[float] = Query(None, ge=0, description="Filter by maximum price"),
    current_user: User = Depends(dependencies.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    repository = WishRepository(db)

    if current_user.role == UserRole.ADMIN.value:
        wishes = await repository.get_all(limit, offset, price_filter)
        total = await repository.count_all(price_filter)
    else:
        wishes = await repository.get_by_owner(current_user.id, limit, offset, price_filter)
        total = await repository.count_by_owner(current_user.id, price_filter)

    return WishListResponse(items=wishes, total=total, limit=limit, offset=offset)


@router.patch("/{wish_id}", response_model=WishResponse)
async def update_wish(
    wish_id: int,
    wish_update: WishUpdate,
    current_user: User = Depends(dependencies.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    repository = WishRepository(db)
    owner_id = None if current_user.role == UserRole.ADMIN.value else current_user.id
    db_wish = await repository.update(wish_id, wish_update, owner_id)
    if not db_wish:
        raise HTTPException(status_code=404, detail="Wish not found")
    return db_wish


@router.delete("/{wish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wish(
    wish_id: int,
    current_user: User = Depends(dependencies.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    repository = WishRepository(db)
    owner_id = None if current_user.role == UserRole.ADMIN.value else current_user.id
    success = await repository.delete(wish_id, owner_id)
    if not success:
        raise HTTPException(status_code=404, detail="Wish not found")
    return None
