import pytest


@pytest.mark.asyncio
async def test_admin_can_access_all_users(client, test_db):
    # Admin тесты требуют создания admin пользователя на уровне БД
    # Так как мы не можем установить роль через API, создадим через database fixture
    from app.adapters.database import get_db
    from app.adapters.repositories.user_repository import UserRepository
    from app.domain.entities import UserRole
    from app.domain.models import UserCreate
    from app.main import app
    from app.services.auth_service import get_password_hash

    # Используем test database напрямую через dependency
    async for db in app.dependency_overrides[get_db]():
        repository = UserRepository(db)

        # Create admin
        user_data = UserCreate(
            email="admin@example.com", username="admin", password="admin123"
        )
        await repository.create(
            user_data, get_password_hash("admin123"), role=UserRole.ADMIN
        )

        # Create regular user
        user_data = UserCreate(
            email="user@example.com", username="user1", password="user12345"
        )
        await repository.create(
            user_data, get_password_hash("user12345"), role=UserRole.USER
        )
        break

    # Login as admin
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "admin123"},
    )
    admin_token = response.json()["access_token"]

    # Access admin endpoint
    response = await client.get(
        "/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 2


@pytest.mark.asyncio
async def test_regular_user_cannot_access_admin_endpoint(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "username": "user1",
            "password": "password123",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    user_token = response.json()["access_token"]

    response = await client.get(
        "/api/v1/admin/users", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_admin_can_see_all_wishes(client, test_db):
    from app.adapters.database import get_db
    from app.adapters.repositories.user_repository import UserRepository
    from app.domain.entities import UserRole
    from app.domain.models import UserCreate
    from app.main import app
    from app.services.auth_service import get_password_hash

    async for db in app.dependency_overrides[get_db]():
        repository = UserRepository(db)

        # Create admin
        user_data = UserCreate(
            email="admin@example.com", username="admin", password="admin123"
        )
        await repository.create(
            user_data, get_password_hash("admin123"), role=UserRole.ADMIN
        )

        # Create regular user
        user_data = UserCreate(
            email="user@example.com", username="user1", password="user12345"
        )
        await repository.create(
            user_data, get_password_hash("user123"), role=UserRole.USER
        )
        break

    # Login as user and create wish
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "user123"},
    )
    user_token = response.json()["access_token"]

    await client.post(
        "/api/v1/wishes/",
        json={"title": "User Wish"},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    # Login as admin
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "admin123"},
    )
    admin_token = response.json()["access_token"]

    # Admin can see all wishes
    response = await client.get(
        "/api/v1/wishes/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    wishes = response.json()["items"]
    assert len(wishes) == 1
    assert wishes[0]["title"] == "User Wish"


@pytest.mark.asyncio
async def test_admin_can_delete_any_wish(client, test_db):
    from app.adapters.database import get_db
    from app.adapters.repositories.user_repository import UserRepository
    from app.domain.entities import UserRole
    from app.domain.models import UserCreate
    from app.main import app
    from app.services.auth_service import get_password_hash

    async for db in app.dependency_overrides[get_db]():
        repository = UserRepository(db)

        # Create admin
        user_data = UserCreate(
            email="admin@example.com", username="admin", password="admin123"
        )
        await repository.create(
            user_data, get_password_hash("admin123"), role=UserRole.ADMIN
        )

        # Create regular user
        user_data = UserCreate(
            email="user@example.com", username="user1", password="user12345"
        )
        await repository.create(
            user_data, get_password_hash("user123"), role=UserRole.USER
        )
        break

    # Login as user and create wish
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "user123"},
    )
    user_token = response.json()["access_token"]

    response = await client.post(
        "/api/v1/wishes/",
        json={"title": "User Wish"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    wish_id = response.json()["id"]

    # Login as admin
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "admin123"},
    )
    admin_token = response.json()["access_token"]

    # Admin can delete user's wish
    response = await client.delete(
        f"/api/v1/wishes/{wish_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204
