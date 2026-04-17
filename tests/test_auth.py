import pytest


@pytest.mark.asyncio
async def test_register_returns_201_and_sets_cookie(client):
    response = await client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "password1"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert "id" in body
    assert "deal_room_ai_session" in response.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client):
    payload = {"email": "dup@example.com", "password": "password1"}
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_login_happy_path(client):
    await client.post(
        "/auth/register",
        json={"email": "bob@example.com", "password": "password1"},
    )
    client.cookies.clear()
    response = await client.post(
        "/auth/login",
        json={"email": "bob@example.com", "password": "password1"},
    )
    assert response.status_code == 200
    assert "deal_room_ai_session" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401_and_no_cookie(client):
    await client.post(
        "/auth/register",
        json={"email": "carol@example.com", "password": "password1"},
    )
    client.cookies.clear()
    response = await client.post(
        "/auth/login",
        json={"email": "carol@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert "deal_room_ai_session" not in response.cookies


@pytest.mark.asyncio
async def test_me_without_cookie_returns_401(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_cookie_returns_user(client):
    await client.post(
        "/auth/register",
        json={"email": "dave@example.com", "password": "password1"},
    )
    response = await client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "dave@example.com"


@pytest.mark.asyncio
async def test_logout_clears_cookie(client):
    await client.post(
        "/auth/register",
        json={"email": "eve@example.com", "password": "password1"},
    )
    logout = await client.post("/auth/logout")
    assert logout.status_code == 204
    client.cookies.clear()
    me = await client.get("/auth/me")
    assert me.status_code == 401
