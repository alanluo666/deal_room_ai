"""Tests for the liveness and readiness probes.

These tests verify the contract that ``/livez`` is trivial and always 200,
and that ``/readyz`` returns 200 only when every dependency it checks (DB,
Chroma, storage) reports healthy.

They rely exclusively on the existing in-memory fixtures (sqlite + fake
vector store + tempdir storage) from :mod:`tests.conftest`. No real network,
Docker, or cloud resources are touched.
"""

from __future__ import annotations


async def test_livez_returns_200_without_auth(client):
    response = await client.get("/livez")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readyz_happy_path_returns_200(client):
    response = await client.get("/readyz")
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "status": "ok",
        "db_ok": True,
        "chroma_ok": True,
        "storage_ok": True,
    }


async def test_readyz_returns_503_when_chroma_unhealthy(
    make_client, fake_vector_store, monkeypatch
):
    monkeypatch.setattr(fake_vector_store, "health_check", lambda: False)

    async with make_client() as ac:
        response = await ac.get("/readyz")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["chroma_ok"] is False
    assert body["db_ok"] is True
    assert body["storage_ok"] is True
