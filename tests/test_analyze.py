"""Tests for the ``POST /deal-rooms/{id}/analyze`` task preset endpoint."""
import pytest
from httpx import AsyncClient

from api.rag import NO_ANSWER_TEXT, RagService, _build_task_prompt
from api.tasks import INSTRUCTIONS, RETRIEVAL_QUERIES, Task
from api.vector_store import RetrievedChunk

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
    content: bytes = b"Acme Corp reported $5M in Q1 2026 revenue, up 12% year over year. Ongoing litigation with a former supplier poses a material risk.",
):
    return await client.post(
        f"/deal-rooms/{deal_room_id}/documents",
        files={"file": (filename, content, TXT_MIME)},
    )


@pytest.mark.asyncio
async def test_analyze_requires_auth(client):
    response = await client.post(
        "/deal-rooms/1/analyze",
        json={"task": "summary"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_analyze_summary_happy_path(client, override_rag, fake_vector_store):
    await _register(client, "sum@example.com")
    room_id = await _create_room(client)
    up = await _upload_txt(client, room_id, filename="acme.txt")
    assert up.status_code == 201
    doc_id = up.json()["id"]

    response = await client.post(
        f"/deal-rooms/{room_id}/analyze",
        json={"task": "summary"},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["task"] == "summary"
    assert body["answer"] == "Stubbed answer."
    assert body["model"] == "stub-llm"
    assert isinstance(body["chunks_used"], int)
    assert body["chunks_used"] >= 1
    assert len(body["citations"]) >= 1

    first = body["citations"][0]
    assert first["document_id"] == doc_id
    assert first["filename"] == "acme.txt"

    assert fake_vector_store.last_query is not None


@pytest.mark.asyncio
async def test_analyze_risks_happy_path(client, override_rag):
    await _register(client, "risk@example.com")
    room_id = await _create_room(client)
    up = await _upload_txt(client, room_id, filename="acme.txt")
    assert up.status_code == 201

    response = await client.post(
        f"/deal-rooms/{room_id}/analyze",
        json={"task": "risks"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["task"] == "risks"
    assert body["answer"] == "Stubbed answer."
    assert body["chunks_used"] >= 1


@pytest.mark.asyncio
async def test_analyze_empty_room_returns_idk(client, override_rag):
    await _register(client, "empty-analyze@example.com")
    room_id = await _create_room(client)

    response = await client.post(
        f"/deal-rooms/{room_id}/analyze",
        json={"task": "summary"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == NO_ANSWER_TEXT
    assert body["citations"] == []
    assert body["chunks_used"] == 0


@pytest.mark.asyncio
async def test_analyze_non_owner_returns_404(make_client, override_rag):
    async with make_client() as owner:
        await _register(owner, "owner-a@example.com")
        room_id = await _create_room(owner)
        up = await _upload_txt(owner, room_id)
        assert up.status_code == 201

    async with make_client() as intruder:
        await _register(intruder, "intruder-a@example.com")
        response = await intruder.post(
            f"/deal-rooms/{room_id}/analyze",
            json={"task": "summary"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_task", ["unknown", "sum", "", "SUMMARY"])
async def test_analyze_rejects_invalid_task(client, override_rag, bad_task):
    await _register(client, f"bad-{bad_task or 'blank'}@example.com")
    room_id = await _create_room(client)
    response = await client.post(
        f"/deal-rooms/{room_id}/analyze",
        json={"task": bad_task},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("top_k", [0, -1, 11, 999])
async def test_analyze_rejects_out_of_range_top_k(client, override_rag, top_k):
    await _register(client, f"k{top_k}-analyze@example.com")
    room_id = await _create_room(client)
    response = await client.post(
        f"/deal-rooms/{room_id}/analyze",
        json={"task": "summary", "top_k": top_k},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_503_when_openai_not_configured(
    client, fake_vector_store, fake_embedding_client
):
    from api.deps import rag_service_dep
    from api.main import app
    from tests.conftest import StubLLM

    await _register(client, "missing-analyze@example.com")
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
        f"/deal-rooms/{room_id}/analyze",
        json={"task": "risks"},
    )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_analyze_does_not_mutate_questions_history(client, override_rag):
    """Analyze is stateless in M4 — it must not write Question rows."""
    await _register(client, "stateless@example.com")
    room_id = await _create_room(client)
    await _upload_txt(client, room_id)

    before = await client.get(f"/deal-rooms/{room_id}/questions")
    assert before.status_code == 200
    count_before = len(before.json())

    for task in ("summary", "risks", "summary"):
        response = await client.post(
            f"/deal-rooms/{room_id}/analyze",
            json={"task": task},
        )
        assert response.status_code == 200

    after = await client.get(f"/deal-rooms/{room_id}/questions")
    assert after.status_code == 200
    assert len(after.json()) == count_before


@pytest.mark.asyncio
async def test_analyze_passes_task_specific_instructions_to_llm(
    client, override_rag, stub_llm
):
    await _register(client, "instr@example.com")
    room_id = await _create_room(client)
    await _upload_txt(client, room_id)

    r1 = await client.post(
        f"/deal-rooms/{room_id}/analyze", json={"task": "summary"}
    )
    assert r1.status_code == 200

    r2 = await client.post(
        f"/deal-rooms/{room_id}/analyze", json={"task": "risks"}
    )
    assert r2.status_code == 200

    assert len(stub_llm.instruction_calls) >= 2
    summary_instr, risks_instr = stub_llm.instruction_calls[-2:]
    assert summary_instr is not None
    assert risks_instr is not None
    assert summary_instr == INSTRUCTIONS[Task.SUMMARY]
    assert risks_instr == INSTRUCTIONS[Task.RISKS]
    assert summary_instr != risks_instr


@pytest.mark.asyncio
async def test_analyze_uses_task_retrieval_query_not_user_text(
    client, override_rag, fake_embedding_client
):
    """The embedding must be derived from the task preset, not a user question."""
    await _register(client, "retr@example.com")
    room_id = await _create_room(client)
    await _upload_txt(client, room_id)

    pre_calls = len(fake_embedding_client.calls)
    response = await client.post(
        f"/deal-rooms/{room_id}/analyze", json={"task": "risks"}
    )
    assert response.status_code == 200

    assert len(fake_embedding_client.calls) == pre_calls + 1
    last_embed_input = fake_embedding_client.calls[-1]
    assert last_embed_input == [RETRIEVAL_QUERIES[Task.RISKS]]


def test_build_task_prompt_without_chunks_requests_idk():
    prompt = _build_task_prompt(Task.SUMMARY, [])
    assert "Task: summary" in prompt
    assert NO_ANSWER_TEXT in prompt
    assert "Context: (no documents found)" in prompt


def test_build_task_prompt_with_chunks_renders_sources():
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
    prompt = _build_task_prompt(Task.RISKS, chunks)
    assert "Task: risks" in prompt
    assert "[Source 1" in prompt
    assert "[Source 2" in prompt
    assert "document_id=7" in prompt
    assert NO_ANSWER_TEXT in prompt
