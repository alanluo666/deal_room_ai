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
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from api.db import Base, get_db
from api.deps import embedding_client_dep, vector_store_dep
from api.main import app
from api.models import DealRoom, Document, User  # noqa: F401  -- register metadata
from api.vector_store import Chunk, VectorStore


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session_factory(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


class FakeVectorStore(VectorStore):
    def __init__(self) -> None:
        self.upserts: list[Chunk] = []
        self.deleted_document_ids: list[int] = []

    def upsert_chunks(self, chunks) -> None:
        self.upserts.extend(chunks)

    def delete_document(self, document_id: int) -> None:
        self.deleted_document_ids.append(document_id)
        self.upserts = [c for c in self.upserts if c.document_id != document_id]

    def count_for_document(self, document_id: int) -> int:
        return sum(1 for c in self.upserts if c.document_id == document_id)

    def health_check(self) -> bool:
        return True


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[float(len(t)), float(i)] for i, t in enumerate(texts)]


@pytest.fixture
def fake_vector_store() -> FakeVectorStore:
    return FakeVectorStore()


@pytest.fixture
def fake_embedding_client() -> FakeEmbeddingClient:
    return FakeEmbeddingClient()


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
async def client(make_client) -> AsyncGenerator[AsyncClient, None]:
    async with make_client() as ac:
        yield ac
