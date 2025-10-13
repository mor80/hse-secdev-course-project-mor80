import pytest


@pytest.mark.asyncio
async def test_not_found_wish(client):
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

    r = await client.get("/api/v1/wishes/999", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404
    body = r.json()
    assert body["code"] == "NOT_FOUND"
    assert "not found" in body["message"].lower()


@pytest.mark.asyncio
async def test_validation_error_invalid_email(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalid-email",
            "username": "testuser",
            "password": "testpassword123",
        },
    )
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_validation_error_short_password(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "username": "testuser", "password": "short"},
    )
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "VALIDATION_ERROR"
