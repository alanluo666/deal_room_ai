from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from api.config import settings


@dataclass(frozen=True)
class Chunk:
    document_id: int
    deal_room_id: int
    user_id: int
    chunk_index: int
    text: str
    embedding: list[float]


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: int
    deal_room_id: int
    user_id: int
    chunk_index: int
    text: str
    distance: float | None


class VectorStore:
    """Abstract interface used by the documents router and tests."""

    def upsert_chunks(self, chunks: Iterable[Chunk]) -> None:
        raise NotImplementedError

    def delete_document(self, document_id: int) -> None:
        raise NotImplementedError

    def count_for_document(self, document_id: int) -> int:
        raise NotImplementedError

    def query(
        self,
        *,
        embedding: list[float],
        where: dict,
        top_k: int,
    ) -> list[RetrievedChunk]:
        raise NotImplementedError

    def health_check(self) -> bool:
        raise NotImplementedError


class ChromaVectorStore(VectorStore):
    """Thin wrapper around a Chroma HTTP client."""

    def __init__(self, host: str, port: int, collection_name: str) -> None:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        self._client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def upsert_chunks(self, chunks: Iterable[Chunk]) -> None:
        chunks = list(chunks)
        if not chunks:
            return
        ids = [f"doc:{c.document_id}:chunk:{c.chunk_index}" for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "deal_room_id": c.deal_room_id,
                "user_id": c.user_id,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]
        embeddings = [c.embedding for c in chunks]
        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def delete_document(self, document_id: int) -> None:
        self._collection.delete(where={"document_id": document_id})

    def count_for_document(self, document_id: int) -> int:
        result = self._collection.get(where={"document_id": document_id}, include=[])
        return len(result.get("ids", []))

    def query(
        self,
        *,
        embedding: list[float],
        where: dict,
        top_k: int,
    ) -> list[RetrievedChunk]:
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        ids = (result.get("ids") or [[]])[0]
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        dists = (result.get("distances") or [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for i in range(len(ids)):
            meta = metas[i] if i < len(metas) else {}
            if not meta:
                continue
            retrieved.append(
                RetrievedChunk(
                    document_id=int(meta.get("document_id", 0)),
                    deal_room_id=int(meta.get("deal_room_id", 0)),
                    user_id=int(meta.get("user_id", 0)),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    text=docs[i] if i < len(docs) else "",
                    distance=float(dists[i]) if i < len(dists) else None,
                )
            )
        return retrieved

    def health_check(self) -> bool:
        try:
            self._client.heartbeat()
            return True
        except Exception:
            return False


_instance: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _instance
    if _instance is None:
        _instance = ChromaVectorStore(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            collection_name=settings.CHROMA_COLLECTION,
        )
    return _instance
