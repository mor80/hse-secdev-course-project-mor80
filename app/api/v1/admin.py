from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database import get_db
from app.api.dependencies import get_current_admin_user
from app.domain.entities import User
from app.domain.models import UserResponse

router = APIRouter()


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of users to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    result = await db.execute(select(User).order_by(User.id).offset(offset).limit(limit))
    users = result.scalars().all()
    return users
