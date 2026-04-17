import os
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:3000")

import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from api.db import Base, get_db
from api.main import app
from api.models import DealRoom, User  # noqa: F401  -- register metadata


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


@pytest_asyncio.fixture
async def make_client(test_session_factory) -> AsyncGenerator[Callable, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

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
