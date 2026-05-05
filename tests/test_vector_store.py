"""Unit tests for ChromaVectorStore.upsert_chunks metadata wiring.

Specifically verifies that the optional ``doc_type`` on :class:`Chunk` is:
  - written into Chroma metadata when set
  - omitted from Chroma metadata when ``None`` (backward compatibility)

The real :class:`chromadb.HttpClient` is never constructed; we instantiate
``ChromaVectorStore`` via ``__new__`` and inject a capturing stub collection.
This keeps the test offline and free of any chromadb import-time requirements.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from api.vector_store import Chunk, ChromaVectorStore


@dataclass
class _CapturingCollection:
    last_upsert: dict[str, Any] | None = None
    deleted: list[dict[str, Any]] = field(default_factory=list)

    def upsert(self, *, ids, documents, metadatas, embeddings) -> None:
        self.last_upsert = {
            "ids": list(ids),
            "documents": list(documents),
            "metadatas": [dict(m) for m in metadatas],
            "embeddings": [list(e) for e in embeddings],
        }


def _make_store() -> tuple[ChromaVectorStore, _CapturingCollection]:
    store = ChromaVectorStore.__new__(ChromaVectorStore)
    collection = _CapturingCollection()
    store._collection = collection  # noqa: SLF001 — test-only injection
    return store, collection


def test_upsert_chunks_includes_doc_type_in_metadata_when_set() -> None:
    store, collection = _make_store()
    chunk = Chunk(
        document_id=1,
        deal_room_id=2,
        user_id=3,
        chunk_index=0,
        text="quarterly revenue grew 12%",
        embedding=[0.1, 0.2, 0.3],
        doc_type="financials",
    )

    store.upsert_chunks([chunk])

    assert collection.last_upsert is not None
    metas = collection.last_upsert["metadatas"]
    assert len(metas) == 1
    assert metas[0]["doc_type"] == "financials"
    assert metas[0]["document_id"] == 1
    assert metas[0]["deal_room_id"] == 2
    assert metas[0]["user_id"] == 3
    assert metas[0]["chunk_index"] == 0


def test_upsert_chunks_omits_doc_type_in_metadata_when_none() -> None:
    store, collection = _make_store()
    chunk = Chunk(
        document_id=10,
        deal_room_id=20,
        user_id=30,
        chunk_index=0,
        text="hello world",
        embedding=[0.0],
    )

    store.upsert_chunks([chunk])

    assert collection.last_upsert is not None
    metas = collection.last_upsert["metadatas"]
    assert len(metas) == 1
    assert "doc_type" not in metas[0]
    assert metas[0] == {
        "document_id": 10,
        "deal_room_id": 20,
        "user_id": 30,
        "chunk_index": 0,
    }


def test_upsert_chunks_mixed_chunks_only_adds_doc_type_where_set() -> None:
    store, collection = _make_store()
    chunks = [
        Chunk(
            document_id=1,
            deal_room_id=1,
            user_id=1,
            chunk_index=0,
            text="a",
            embedding=[0.0],
            doc_type="legal",
        ),
        Chunk(
            document_id=1,
            deal_room_id=1,
            user_id=1,
            chunk_index=1,
            text="b",
            embedding=[0.0],
        ),
    ]

    store.upsert_chunks(chunks)

    assert collection.last_upsert is not None
    metas = collection.last_upsert["metadatas"]
    assert metas[0]["doc_type"] == "legal"
    assert "doc_type" not in metas[1]
