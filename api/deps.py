from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import decode_access_token
from api.config import settings
from api.db import get_db
from api.document_processing import EmbeddingClient, get_embedding_client
from api.models import User
from api.rag import RagService
from api.service import openai_service
from api.vector_store import VectorStore, get_vector_store


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    session_cookie: str | None = Cookie(default=None, alias=settings.JWT_COOKIE_NAME),
) -> User:
    if not session_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(session_cookie)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
        ) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def vector_store_dep() -> VectorStore:
    return get_vector_store()


def embedding_client_dep() -> EmbeddingClient:
    return get_embedding_client()


def rag_service_dep(
    vector_store: VectorStore = Depends(vector_store_dep),
    embedder: EmbeddingClient = Depends(embedding_client_dep),
) -> RagService:
    """Fresh :class:`RagService` per request.

    Tests can override the collaborators via ``vector_store_dep`` and
    ``embedding_client_dep`` without touching this factory. For the real LLM
    we use the module-level :data:`openai_service` singleton; tests replace
    the whole :func:`rag_service_dep` override with a RagService that uses a
    stub LLM, which keeps OpenAI traffic fully mocked.
    """
    return RagService(
        vector_store=vector_store,
        embedder=embedder,
        llm=openai_service,
    )
