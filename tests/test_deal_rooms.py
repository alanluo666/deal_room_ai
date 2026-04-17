import pytest
from httpx import AsyncClient


async def _register(client: AsyncClient, email: str, password: str = "password1") -> int:
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_and_list_deal_rooms(client):
    await _register(client, "owner@example.com")
    create = await client.post(
        "/deal-rooms",
        json={"name": "Acme", "target_company": "Acme Corp"},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["name"] == "Acme"
    assert body["target_company"] == "Acme Corp"
    assert body["owner_id"] > 0

    listing = await client.get("/deal-rooms")
    assert listing.status_code == 200
    rooms = listing.json()
    assert len(rooms) == 1
    assert rooms[0]["id"] == body["id"]


@pytest.mark.asyncio
async def test_create_requires_auth(client):
    response = await client.post("/deal-rooms", json={"name": "Acme"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_other_user_cannot_see_or_delete(make_client):
    async with make_client() as client_a:
        await _register(client_a, "userA@example.com")
        create = await client_a.post("/deal-rooms", json={"name": "Alpha"})
        room_id = create.json()["id"]

    async with make_client() as client_b:
        await _register(client_b, "userB@example.com")

        cross_get = await client_b.get(f"/deal-rooms/{room_id}")
        assert cross_get.status_code == 404

        cross_list = await client_b.get("/deal-rooms")
        assert cross_list.status_code == 200
        assert cross_list.json() == []

        cross_delete = await client_b.delete(f"/deal-rooms/{room_id}")
        assert cross_delete.status_code == 404


@pytest.mark.asyncio
async def test_delete_own_deal_room(client):
    await _register(client, "del@example.com")
    create = await client.post("/deal-rooms", json={"name": "ToDelete"})
    room_id = create.json()["id"]

    delete = await client.delete(f"/deal-rooms/{room_id}")
    assert delete.status_code == 204

    get = await client.get(f"/deal-rooms/{room_id}")
    assert get.status_code == 404


@pytest.mark.asyncio
async def test_health_includes_db_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db_ok"] is True
    for required in (
        "openai_configured",
        "openai_model",
        "mlflow_tracking_enabled",
        "mlflow_tracking_uri",
        "mlflow_experiment_name",
    ):
        assert required in body
    assert body["mlflow_tracking_enabled"] is False
    assert body["mlflow_tracking_uri"] == ""
