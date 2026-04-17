from __future__ import annotations

import io
import os

from api.config import settings
from api.vector_store import Chunk


ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    }
)

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 100


class UnsupportedFileTypeError(Exception):
    pass


class ExtractionError(Exception):
    pass


def is_supported(mime_type: str) -> bool:
    return mime_type in ALLOWED_MIME_TYPES


def extract_text(mime_type: str, data: bytes) -> str:
    if mime_type == "text/plain":
        try:
            return data.decode("utf-8", errors="replace")
        except Exception as exc:  # pragma: no cover - replace=errors never raises
            raise ExtractionError(f"Could not decode text file: {exc}") from exc

    if mime_type == "application/pdf":
        try:
            import pypdf
        except ImportError as exc:  # pragma: no cover
            raise ExtractionError("pypdf is not installed") from exc
        try:
            reader = pypdf.PdfReader(io.BytesIO(data))
            parts = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(parts).strip()
        except Exception as exc:
            raise ExtractionError(f"PDF extraction failed: {exc}") from exc

    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        try:
            from docx import Document as DocxDocument
        except ImportError as exc:  # pragma: no cover
            raise ExtractionError("python-docx is not installed") from exc
        try:
            doc = DocxDocument(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs).strip()
        except Exception as exc:
            raise ExtractionError(f"DOCX extraction failed: {exc}") from exc

    raise UnsupportedFileTypeError(f"Unsupported MIME type: {mime_type}")


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    if not text or not text.strip():
        return []
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError as exc:  # pragma: no cover
        raise ExtractionError("langchain-text-splitters is not installed") from exc
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return [piece for piece in splitter.split_text(text) if piece.strip()]


class EmbeddingClient:
    """Minimal OpenAI embeddings client. Instantiation is cheap; the network
    client is lazily created so unit tests can construct this without
    OPENAI_API_KEY being set."""

    def __init__(self, *, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model or settings.EMBEDDING_MODEL
        self._api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY", "")
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            if not self._api_key:
                raise RuntimeError("OPENAI_API_KEY is not set")
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._ensure_client()
        response = client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


_embedding_singleton: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    global _embedding_singleton
    if _embedding_singleton is None:
        _embedding_singleton = EmbeddingClient()
    return _embedding_singleton


def reset_embedding_client() -> None:
    """Clear the cached singleton. Used only by tests."""
    global _embedding_singleton
    _embedding_singleton = None


def build_chunks(
    *,
    user_id: int,
    deal_room_id: int,
    document_id: int,
    mime_type: str,
    data: bytes,
    embedder: EmbeddingClient,
) -> list[Chunk]:
    text = extract_text(mime_type, data)
    pieces = chunk_text(text)
    if not pieces:
        return []
    embeddings = embedder.embed(pieces)
    if len(embeddings) != len(pieces):
        raise ExtractionError(
            f"Embedding count {len(embeddings)} does not match chunk count {len(pieces)}"
        )
    return [
        Chunk(
            document_id=document_id,
            deal_room_id=deal_room_id,
            user_id=user_id,
            chunk_index=idx,
            text=piece,
            embedding=embeddings[idx],
        )
        for idx, piece in enumerate(pieces)
    ]
