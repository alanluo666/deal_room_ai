import pytest
from httpx import AsyncClient

from api.rag import NO_ANSWER_TEXT, RetrievedChunk, _build_prompt, _trim_to_budget

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
async def test_ask_requires_auth(client):
    response = await client.post(
        "/deal-rooms/1/ask",
        json={"question": "hello?"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ask_happy_path_returns_answer_and_citations(
    client, override_rag, fake_vector_store
):
    await _register(client, "happy@example.com")
    room_id = await _create_room(client)
    up = await _upload_txt(client, room_id, filename="acme.txt")
    assert up.status_code == 201
    doc_id = up.json()["id"]

    response = await client.post(
        f"/deal-rooms/{room_id}/ask",
        json={"question": "What was Q1 revenue?"},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["answer"] == "Stubbed answer."
    assert body["model"] == "stub-llm"
    assert isinstance(body["question_id"], int)
    assert len(body["citations"]) >= 1

    first = body["citations"][0]
    assert first["document_id"] == doc_id
    assert first["filename"] == "acme.txt"
    assert isinstance(first["chunk_index"], int)
    assert len(first["snippet"]) <= 300

    assert fake_vector_store.last_query is not None
    where = fake_vector_store.last_query["where"]
    assert "$and" in where


@pytest.mark.asyncio
async def test_ask_in_empty_room_returns_idk(client, override_rag):
    await _register(client, "empty@example.com")
    room_id = await _create_room(client)

    response = await client.post(
        f"/deal-rooms/{room_id}/ask",
        json={"question": "Anything?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == NO_ANSWER_TEXT
    assert body["citations"] == []

    listing = await client.get(f"/deal-rooms/{room_id}/questions")
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["answer"] == NO_ANSWER_TEXT


@pytest.mark.asyncio
async def test_ask_non_owner_returns_404(make_client, override_rag):
    async with make_client() as client_a:
        await _register(client_a, "owner@example.com")
        room_id = await _create_room(client_a)
        up = await _upload_txt(client_a, room_id)
        assert up.status_code == 201

    async with make_client() as client_b:
        await _register(client_b, "intruder@example.com")
        response = await client_b.post(
            f"/deal-rooms/{room_id}/ask",
            json={"question": "anything?"},
        )
        assert response.status_code == 404

        listing = await client_b.get(f"/deal-rooms/{room_id}/questions")
        assert listing.status_code == 404


@pytest.mark.asyncio
async def test_ask_isolates_per_deal_room(client, override_rag, fake_vector_store):
    await _register(client, "iso@example.com")
    room_a = await _create_room(client, "A")
    room_b = await _create_room(client, "B")

    up_a = await _upload_txt(client, room_a, filename="a.txt")
    up_b = await _upload_txt(client, room_b, filename="b.txt")
    doc_a = up_a.json()["id"]
    doc_b = up_b.json()["id"]

    response = await client.post(
        f"/deal-rooms/{room_a}/ask",
        json={"question": "room a question", "top_k": 5},
    )
    assert response.status_code == 200
    citations = response.json()["citations"]
    assert citations, "expected at least one citation from room A"
    for cit in citations:
        assert cit["document_id"] == doc_a
        assert cit["filename"] == "a.txt"
    assert all(cit["document_id"] != doc_b for cit in citations)


@pytest.mark.asyncio
async def test_ask_503_when_openai_not_configured(
    client, make_client, fake_vector_store, fake_embedding_client
):
    from api.deps import rag_service_dep
    from api.main import app
    from api.rag import RagService
    from tests.conftest import StubLLM

    await _register(client, "missing@example.com")
    room_id = await _create_room(client)
    up = await _upload_txt(client, room_id)
    assert up.status_code == 201

    raising_llm = StubLLM(
        raises=RuntimeError("OPENAI_API_KEY is not set"),
        model="stub-llm",
    )

    def _factory():
        return RagService(
            vector_store=fake_vector_store,
            embedder=fake_embedding_client,
            llm=raising_llm,
        )

    app.dependency_overrides[rag_service_dep] = _factory

    response = await client.post(
        f"/deal-rooms/{room_id}/ask",
        json={"question": "still works?"},
    )
    assert response.status_code == 503

    listing = await client.get(f"/deal-rooms/{room_id}/questions")
    assert listing.status_code == 200
    assert listing.json() == []


@pytest.mark.asyncio
async def test_ask_rejects_empty_question(client, override_rag):
    await _register(client, "val@example.com")
    room_id = await _create_room(client)
    response = await client.post(
        f"/deal-rooms/{room_id}/ask",
        json={"question": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("top_k", [0, -1, 11, 999])
async def test_ask_rejects_out_of_range_top_k(client, override_rag, top_k):
    await _register(client, f"k{top_k}@example.com")
    room_id = await _create_room(client)
    response = await client.post(
        f"/deal-rooms/{room_id}/ask",
        json={"question": "hi", "top_k": top_k},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_questions_list_ordered_and_scoped(client, override_rag):
    await _register(client, "list@example.com")
    room_a = await _create_room(client, "A")
    room_b = await _create_room(client, "B")
    await _upload_txt(client, room_a, filename="a.txt")
    await _upload_txt(client, room_b, filename="b.txt")

    for question in ("first question?", "second question?", "third question?"):
        response = await client.post(
            f"/deal-rooms/{room_a}/ask",
            json={"question": question},
        )
        assert response.status_code == 200

    await client.post(
        f"/deal-rooms/{room_b}/ask",
        json={"question": "in room b"},
    )

    listing = await client.get(f"/deal-rooms/{room_a}/questions")
    assert listing.status_code == 200
    data = listing.json()
    assert [q["question"] for q in data] == [
        "third question?",
        "second question?",
        "first question?",
    ]
    for q in data:
        assert q["deal_room_id"] == room_a


@pytest.mark.asyncio
async def test_delete_deal_room_cascades_questions(
    client, override_rag, test_session_factory
):
    from sqlalchemy import select

    from api.models import Question

    await _register(client, "cascade@example.com")
    room_id = await _create_room(client)
    await _upload_txt(client, room_id)

    ask = await client.post(
        f"/deal-rooms/{room_id}/ask",
        json={"question": "cascade test"},
    )
    assert ask.status_code == 200

    async with test_session_factory() as session:
        pre_rows = (
            await session.execute(
                select(Question).where(Question.deal_room_id == room_id)
            )
        ).scalars().all()
        assert len(pre_rows) == 1

    response = await client.delete(f"/deal-rooms/{room_id}")
    assert response.status_code == 204

    gone = await client.get(f"/deal-rooms/{room_id}/questions")
    assert gone.status_code == 404

    async with test_session_factory() as session:
        post_rows = (
            await session.execute(
                select(Question).where(Question.deal_room_id == room_id)
            )
        ).scalars().all()
        assert post_rows == []


@pytest.mark.asyncio
async def test_ask_persists_citations_json_round_trip(client, override_rag):
    await _register(client, "rt@example.com")
    room_id = await _create_room(client)
    await _upload_txt(client, room_id, filename="acme.txt")

    created = await client.post(
        f"/deal-rooms/{room_id}/ask",
        json={"question": "round trip?"},
    )
    assert created.status_code == 200
    created_body = created.json()

    listing = await client.get(f"/deal-rooms/{room_id}/questions")
    assert listing.status_code == 200
    data = listing.json()
    assert len(data) == 1
    stored = data[0]
    assert stored["answer"] == created_body["answer"]
    assert stored["citations"] == created_body["citations"]


def test_trim_to_budget_truncates_partial_chunk_when_meaningful():
    chunks = [
        RetrievedChunk(
            document_id=1,
            deal_room_id=1,
            user_id=1,
            chunk_index=i,
            text="x" * 400,
            distance=float(i),
        )
        for i in range(10)
    ]
    trimmed = _trim_to_budget(chunks, budget=1000)
    total = sum(len(c.text) for c in trimmed)
    assert total <= 1000
    assert 1 <= len(trimmed) <= 4


def test_trim_to_budget_drops_partial_below_threshold():
    chunks = [
        RetrievedChunk(
            document_id=1,
            deal_room_id=1,
            user_id=1,
            chunk_index=i,
            text="x" * 1000,
            distance=float(i),
        )
        for i in range(2)
    ]
    trimmed = _trim_to_budget(chunks, budget=1100)
    assert len(trimmed) == 1
    assert len(trimmed[0].text) == 1000


def test_build_prompt_when_no_chunks_contains_idk_instruction():
    prompt = _build_prompt("What is the revenue?", [])
    assert NO_ANSWER_TEXT in prompt
    assert "Context: (no documents found)" in prompt


def test_build_prompt_includes_source_markers():
    chunks = [
        RetrievedChunk(
            document_id=7,
            deal_room_id=3,
            user_id=1,
            chunk_index=0,
            text="Revenue was $5M.",
            distance=0.0,
        ),
        RetrievedChunk(
            document_id=7,
            deal_room_id=3,
            user_id=1,
            chunk_index=1,
            text="Margin expanded.",
            distance=1.0,
        ),
    ]
    prompt = _build_prompt("What was revenue?", chunks)
    assert "[Source 1" in prompt
    assert "[Source 2" in prompt
    assert "document_id=7" in prompt
    assert NO_ANSWER_TEXT in prompt
