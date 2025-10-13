from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Wish
from app.domain.models import WishCreate, WishUpdate


class WishRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, wish: WishCreate, owner_id: int) -> Wish:
        db_wish = Wish(**wish.model_dump(), owner_id=owner_id)
        self.db.add(db_wish)
        await self.db.commit()
        await self.db.refresh(db_wish)
        return db_wish

    async def get_by_id(
        self, wish_id: int, owner_id: Optional[int] = None
    ) -> Optional[Wish]:
        query = select(Wish).where(Wish.id == wish_id)
        if owner_id is not None:
            query = query.where(Wish.owner_id == owner_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self, limit: int = 10, offset: int = 0, price_filter: Optional[float] = None
    ) -> List[Wish]:
        query = select(Wish)

        if price_filter is not None:
            query = query.where(Wish.price_estimate <= price_filter)

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_owner(
        self,
        owner_id: int,
        limit: int = 10,
        offset: int = 0,
        price_filter: Optional[float] = None,
    ) -> List[Wish]:
        query = select(Wish).where(Wish.owner_id == owner_id)

        if price_filter is not None:
            query = query.where(Wish.price_estimate <= price_filter)

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(
        self, wish_id: int, wish_update: WishUpdate, owner_id: Optional[int] = None
    ) -> Optional[Wish]:
        db_wish = await self.get_by_id(wish_id, owner_id)
        if not db_wish:
            return None

        update_data = wish_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_wish, field, value)

        await self.db.commit()
        await self.db.refresh(db_wish)
        return db_wish

    async def delete(self, wish_id: int, owner_id: Optional[int] = None) -> bool:
        db_wish = await self.get_by_id(wish_id, owner_id)
        if not db_wish:
            return False

        await self.db.delete(db_wish)
        await self.db.commit()
        return True

    async def count_all(self, price_filter: Optional[float] = None) -> int:
        query = select(func.count()).select_from(Wish)

        if price_filter is not None:
            query = query.where(Wish.price_estimate <= price_filter)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def count_by_owner(
        self, owner_id: int, price_filter: Optional[float] = None
    ) -> int:
        query = select(func.count()).select_from(Wish).where(Wish.owner_id == owner_id)

        if price_filter is not None:
            query = query.where(Wish.price_estimate <= price_filter)

        result = await self.db.execute(query)
        return result.scalar_one()
