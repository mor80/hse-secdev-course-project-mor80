import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.repositories.wish_repository import WishRepository
from app.domain.entities import User, UserRole
from app.domain.models import WishCreate, WishUpdate
from app.services.auth_service import get_password_hash
from tests.conftest import TestingSessionLocal


async def _create_user(session: AsyncSession, email: str, username: str) -> User:
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER.value,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_wish_repository_scopes_operations_by_owner(test_db):
    async with TestingSessionLocal() as session:
        repo = WishRepository(session)
        owner_one = await _create_user(session, "owner1@example.com", "owner1")
        owner_two = await _create_user(session, "owner2@example.com", "owner2")

        wish_one = await repo.create(
            WishCreate(
                title="Owner One Wish",
                link="https://example.com/one",
                price_estimate=150.50,
                notes="first",
            ),
            owner_one.id,
        )
        await repo.create(
            WishCreate(
                title="Owner Two Wish",
                link="https://example.com/two",
                price_estimate=75.00,
                notes="second",
            ),
            owner_two.id,
        )

        assert await repo.get_by_id(wish_one.id, owner_one.id) is not None
        assert await repo.get_by_id(wish_one.id, owner_two.id) is None

        owner_one_wishes = await repo.get_by_owner(
            owner_one.id, limit=5, offset=0, price_filter=200
        )
        assert len(owner_one_wishes) == 1
        assert owner_one_wishes[0].owner_id == owner_one.id

        all_wishes = await repo.get_all(limit=10, offset=0, price_filter=200)
        assert len(all_wishes) == 2

        count_all = await repo.count_all(price_filter=200)
        assert count_all == 2

        count_owner_one = await repo.count_by_owner(owner_one.id, price_filter=200)
        assert count_owner_one == 1


@pytest.mark.asyncio
async def test_wish_repository_update_and_delete_enforce_owner(test_db):
    async with TestingSessionLocal() as session:
        repo = WishRepository(session)
        owner = await _create_user(session, "owner3@example.com", "owner3")
        attacker = await _create_user(session, "attacker@example.com", "attacker")

        wish = await repo.create(
            WishCreate(title="Secure Camera", link="https://safe.example/cam", notes="night mode"),
            owner.id,
        )

        updated = await repo.update(
            wish.id,
            WishUpdate(notes="updated note", price_estimate=999.99),
            owner_id=owner.id,
        )
        assert updated.notes == "updated note"

        unauthorized_update = await repo.update(
            wish.id,
            WishUpdate(notes="malicious change"),
            owner_id=attacker.id,
        )
        assert unauthorized_update is None

        assert await repo.delete(wish.id, owner_id=attacker.id) is False
        assert await repo.delete(wish.id, owner_id=owner.id) is True
        assert await repo.delete(wish.id, owner_id=owner.id) is False
