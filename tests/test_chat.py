"""Tests for ``POST /deal-rooms/{id}/chat`` (Person C slice).

Scope is deliberately small and matches the patterns in
``tests/test_questions.py`` and ``tests/test_analyze.py``:

* 401 without auth
* 404 for non-owner access
* 400 when the last message is not a user turn
* 200 local-dev stub response when ``OPENAI_API_KEY`` is unset
* 200 happy path using the same mocked/stubbed collaborators

No network, no real OpenAI, no MLflow, no Chroma server. ``openai_service``
is monkeypatched in-process when we want to flip ``is_ready()``; everything
else rides on the existing fixtures in ``tests/conftest.py``.
"""
import pytest
from httpx import AsyncClient

from api.routers.chat import LOCAL_DEV_STUB_MODEL

TXT_MIME = "text/plain"


async def _register(client: AsyncClient, email: str, password: str = "password1") -> int:
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_room(client: AsyncClient, name: str = "Room") -> int:
    response = await client.post("/deal-rooms", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


async def _upload_txt(
    client: AsyncClient,
    deal_room_id: int,
    *,
    filename: str = "notes.txt",
    content: bytes = b"Acme Corp reported $5M in Q1 2026 revenue, up 12% year over year.",
):
    return await client.post(
        f"/deal-rooms/{deal_room_id}/documents",
        files={"file": (filename, content, TXT_MIME)},
    )


@pytest.mark.asyncio
async def test_chat_requires_auth(client):
    response = await client.post(
        "/deal-rooms/1/chat",
        json={"messages": [{"role": "user", "content": "hello?"}]},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_non_owner_returns_404(make_client, override_rag, monkeypatch):
    # Force openai_service.is_ready() to True so the handler reaches the
    # ownership check instead of short-circuiting on the local-dev stub.
    from api.service import openai_service

    monkeypatch.setattr(openai_service, "client", object())

    async with make_client() as owner:
        await _register(owner, "owner-chat@example.com")
        room_id = await _create_room(owner)
        up = await _upload_txt(owner, room_id)
        assert up.status_code == 201

    async with make_client() as intruder:
        await _register(intruder, "intruder-chat@example.com")
        response = await intruder.post(
            f"/deal-rooms/{room_id}/chat",
            json={"messages": [{"role": "user", "content": "hello?"}]},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_chat_rejects_when_last_message_is_not_user(
    client, override_rag, monkeypatch
):
    from api.service import openai_service

    monkeypatch.setattr(openai_service, "client", object())

    await _register(client, "lastrole@example.com")
    room_id = await _create_room(client)

    response = await client.post(
        f"/deal-rooms/{room_id}/chat",
        json={
            "messages": [
                {"role": "user", "content": "first"},
                {"role": "assistant", "content": "assistant talks last"},
            ],
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_chat_returns_local_dev_stub_when_openai_not_configured(
    client, monkeypatch
):
    from api.service import openai_service

    monkeypatch.setattr(openai_service, "client", None)
    assert openai_service.is_ready() is False

    await _register(client, "nokey-chat@example.com")
    room_id = await _create_room(client)

    response = await client.post(
        f"/deal-rooms/{room_id}/chat",
        json={
            "messages": [{"role": "user", "content": "anything?"}],
            "session_id": "dev-1",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == LOCAL_DEV_STUB_MODEL
    assert body["message"]["role"] == "assistant"
    assert body["message"]["content"]
    assert body["citations"] == []
    assert body["chunks_used"] == 0
    assert body["session_id"] == "dev-1"
    assert body["steps"] == []


@pytest.mark.asyncio
async def test_chat_happy_path_returns_grounded_answer_and_citations(
    client, override_rag, fake_vector_store, monkeypatch
):
    from api.service import openai_service

    monkeypatch.setattr(openai_service, "client", object())

    await _register(client, "happy-chat@example.com")
    room_id = await _create_room(client)
    up = await _upload_txt(client, room_id, filename="acme.txt")
    assert up.status_code == 201
    doc_id = up.json()["id"]

    response = await client.post(
        f"/deal-rooms/{room_id}/chat",
        json={
            "messages": [{"role": "user", "content": "What was Q1 revenue?"}],
            "session_id": "happy-1",
        },
    )
    assert response.status_code == 200
    body = response.json()

    assert body["message"]["role"] == "assistant"
    assert body["message"]["content"] == "Stubbed answer."
    assert body["model"] == "stub-llm"
    assert isinstance(body["chunks_used"], int)
    assert body["chunks_used"] >= 1
    assert len(body["citations"]) >= 1

    first = body["citations"][0]
    assert first["document_id"] == doc_id
    assert first["filename"] == "acme.txt"
    assert isinstance(first["chunk_index"], int)
    assert len(first["snippet"]) <= 300

    assert body["session_id"] == "happy-1"
    assert body["steps"] == []

    # /chat must not persist turns to the questions table; that is /ask's
    # contract. This assertion will fail loudly if Person A's later swap-in
    # accidentally starts writing Question rows from inside the agent.
    history = await client.get(f"/deal-rooms/{room_id}/questions")
    assert history.status_code == 200
    assert history.json() == []

    # Confirm we actually hit the retrieval path (not the stub).
    assert fake_vector_store.last_query is not None
