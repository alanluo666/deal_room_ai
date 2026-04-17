import os
import tempfile
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:3000")
os.environ.setdefault("STORAGE_DIR", tempfile.mkdtemp(prefix="dr_test_storage_"))
os.environ.setdefault("CHROMA_HOST", "chroma-test")
os.environ.setdefault("CHROMA_PORT", "8000")
os.environ.setdefault("CHROMA_COLLECTION", "test_chunks")

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from api.db import Base, get_db
from api.deps import embedding_client_dep, rag_service_dep, vector_store_dep
from api.main import app
from api.models import DealRoom, Document, Question, User  # noqa: F401  -- register metadata
from api.rag import RagService
from api.vector_store import Chunk, RetrievedChunk, VectorStore


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, _record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session_factory(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


def _flatten_where(where: dict | None) -> dict:
    """Flatten a chroma-style ``where`` filter into a plain key/value dict.

    Chroma requires ``$and`` for multiple equality conditions; production code
    always uses it, so the fake accepts both shapes.
    """
    if not where:
        return {}
    if "$and" in where:
        merged: dict = {}
        for cond in where["$and"]:
            merged.update(cond)
        return merged
    return dict(where)


class FakeVectorStore(VectorStore):
    def __init__(self) -> None:
        self.upserts: list[Chunk] = []
        self.deleted_document_ids: list[int] = []
        self.last_query: dict | None = None

    def upsert_chunks(self, chunks) -> None:
        self.upserts.extend(chunks)

    def delete_document(self, document_id: int) -> None:
        self.deleted_document_ids.append(document_id)
        self.upserts = [c for c in self.upserts if c.document_id != document_id]

    def count_for_document(self, document_id: int) -> int:
        return sum(1 for c in self.upserts if c.document_id == document_id)

    def query(
        self,
        *,
        embedding: list[float],
        where: dict,
        top_k: int,
    ) -> list[RetrievedChunk]:
        self.last_query = {"embedding": embedding, "where": where, "top_k": top_k}
        flat = _flatten_where(where)

        def matches(chunk: Chunk) -> bool:
            for key, expected in flat.items():
                if getattr(chunk, key, None) != expected:
                    return False
            return True

        candidates = [c for c in self.upserts if matches(c)]
        return [
            RetrievedChunk(
                document_id=c.document_id,
                deal_room_id=c.deal_room_id,
                user_id=c.user_id,
                chunk_index=c.chunk_index,
                text=c.text,
                distance=float(idx),
            )
            for idx, c in enumerate(candidates[:top_k])
        ]

    def health_check(self) -> bool:
        return True


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[float(len(t)), float(i)] for i, t in enumerate(texts)]


class StubLLM:
    """Minimal LLM that satisfies :class:`api.rag.RagLLM`."""

    def __init__(
        self,
        *,
        answer: str = "Stubbed answer.",
        model: str = "stub-llm",
        raises: Exception | None = None,
    ) -> None:
        self.answer = answer
        self.model = model
        self._raises = raises
        self.calls: list[str] = []

    def run_rag(self, *, prompt: str) -> str:
        self.calls.append(prompt)
        if self._raises is not None:
            raise self._raises
        return self.answer


@pytest.fixture
def fake_vector_store() -> FakeVectorStore:
    return FakeVectorStore()


@pytest.fixture
def fake_embedding_client() -> FakeEmbeddingClient:
    return FakeEmbeddingClient()


@pytest.fixture
def stub_llm() -> StubLLM:
    return StubLLM()


@pytest_asyncio.fixture
async def make_client(
    test_session_factory,
    fake_vector_store: FakeVectorStore,
    fake_embedding_client: FakeEmbeddingClient,
) -> AsyncGenerator[Callable, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[vector_store_dep] = lambda: fake_vector_store
    app.dependency_overrides[embedding_client_dep] = lambda: fake_embedding_client

    @asynccontextmanager
    async def _factory() -> AsyncGenerator[AsyncClient, None]:
        transport = ASGITransport(app=app)
        async with LifespanManager(app):
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                yield ac

    yield _factory
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def override_rag(
    make_client,
    fake_vector_store: FakeVectorStore,
    fake_embedding_client: FakeEmbeddingClient,
    stub_llm: StubLLM,
):
    """Swap ``rag_service_dep`` for a RagService that uses the stub LLM."""

    def _factory() -> RagService:
        return RagService(
            vector_store=fake_vector_store,
            embedder=fake_embedding_client,
            llm=stub_llm,
        )

    app.dependency_overrides[rag_service_dep] = _factory
    yield stub_llm


@pytest_asyncio.fixture
async def client(make_client) -> AsyncGenerator[AsyncClient, None]:
    async with make_client() as ac:
        yield ac
