import pytest


async def _register_and_login(client, email: str, username: str, password: str) -> str:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    assert register_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert response.json()["username"] == "testuser"


@pytest.mark.asyncio
async def test_login_user(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_create_wish(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    token = response.json()["access_token"]

    response = await client.post(
        "/api/v1/wishes/",
        json={
            "title": "New Laptop",
            "link": "https://example.com/laptop",
            "price_estimate": 1500.00,
            "notes": "High-performance laptop for development",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["title"] == "New Laptop"


@pytest.mark.asyncio
async def test_get_wishes(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    token = response.json()["access_token"]

    await client.post(
        "/api/v1/wishes/",
        json={"title": "Test Wish"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await client.get("/api/v1/wishes/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


@pytest.mark.asyncio
async def test_unauthorized_access(client):
    response = await client.get("/api/v1/wishes/")
    # HTTPBearer can return 401 or 403 depending on version/config
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_owner_only_access(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user1@example.com",
            "username": "user1",
            "password": "password123",
        },
    )

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user2@example.com",
            "username": "user2",
            "password": "password123",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "user1@example.com", "password": "password123"},
    )
    token1 = response.json()["access_token"]

    response = await client.post(
        "/api/v1/wishes/",
        json={"title": "User1 Wish"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    wish_id = response.json()["id"]

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "user2@example.com", "password": "password123"},
    )
    token2 = response.json()["access_token"]

    response = await client.get(
        f"/api/v1/wishes/{wish_id}", headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_wish_creation_rejects_html_payload(client):
    token = await _register_and_login(
        client, email="security1@example.com", username="security1", password="password123"
    )

    response = await client.post(
        "/api/v1/wishes/",
        json={"title": "<script>alert(1)</script>", "notes": "legit", "link": "https://safe.com"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["type"] == "https://api.wishlist.com/errors/validation-error"
    assert any("title" in err["field"].lower() for err in body["validation_errors"])


@pytest.mark.asyncio
async def test_wish_creation_rejects_insecure_link(client):
    token = await _register_and_login(
        client, email="security2@example.com", username="security2", password="password123"
    )

    response = await client.post(
        "/api/v1/wishes/",
        json={"title": "Gift", "link": "ftp://example.com/file", "notes": "bad protocol"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["type"] == "https://api.wishlist.com/errors/validation-error"
    assert any("link" in err["field"].lower() for err in body["validation_errors"])
