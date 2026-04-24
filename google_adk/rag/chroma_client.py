"""ChromaDB persistent client and collection accessor.

The client is created once at import time (singleton pattern) so that all
tools and the ingestion pipeline share the same connection.
"""

from __future__ import annotations

import chromadb
from chromadb.config import Settings

from ..config import CHROMA_COLLECTION, CHROMA_DATA_DIR

# ---------------------------------------------------------------------------
# Singleton client
# ---------------------------------------------------------------------------

_client: chromadb.PersistentClient | None = None


def get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=CHROMA_DATA_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


# ---------------------------------------------------------------------------
# Collection accessor
# ---------------------------------------------------------------------------

def get_collection() -> chromadb.Collection:
    """Return (or lazily create) the deal_room_docs collection.

    Metadata schema stored per document:
        doc_id        – source filing identifier (e.g. "AAPL_10K_2023")
        section_type  – classifier label (e.g. "risk_factor")
        company       – ticker or company name (e.g. "AAPL")
        chunk_index   – integer position within the source document
    """
    client = get_client()
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Convenience: fetch chunks by ids
# ---------------------------------------------------------------------------

def get_chunks_by_ids(chunk_ids: list[str]) -> list[dict]:
    """Return a list of {id, document, metadata} dicts for the given ids."""
    collection = get_collection()
    results = collection.get(ids=chunk_ids, include=["documents", "metadatas"])
    output = []
    for i, chunk_id in enumerate(results["ids"]):
        output.append(
            {
                "id": chunk_id,
                "document": results["documents"][i],
                "metadata": results["metadatas"][i],
            }
        )
    return output
