"""RAG retrieval: embed a query, search ChromaDB, return ranked ChunkResults.

The retriever supports optional metadata filtering so the agent can search
within a specific section type (e.g. risk_factor) or for a specific company.
"""

from __future__ import annotations

import logging

from ..config import DEFAULT_TOP_K
from ..schemas import ChunkResult
from .chroma_client import get_collection
from .embedder import embed

logger = logging.getLogger(__name__)


def retrieve(
    query: str,
    section_type: str | None = None,
    company: str | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> list[ChunkResult]:
    """Embed *query* and return the top-k most relevant chunks from ChromaDB.

    Args:
        query:        Natural-language search query.
        section_type: Optional filter — only return chunks with this section label
                      (e.g. ``"risk_factor"``, ``"financial_statement"``).
        company:      Optional filter — restrict results to a specific company/ticker.
        top_k:        Maximum number of results to return.

    Returns:
        List of :class:`ChunkResult` objects ordered by descending relevance.
    """
    query_embedding = embed(query)
    collection = get_collection()

    # Build ChromaDB `where` filter
    where: dict | None = None
    conditions: list[dict] = []
    if section_type:
        conditions.append({"section_type": {"$eq": section_type}})
    if company:
        conditions.append({"company": {"$eq": company}})

    if len(conditions) == 1:
        where = conditions[0]
    elif len(conditions) > 1:
        where = {"$and": conditions}

    query_kwargs: dict = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        query_kwargs["where"] = where

    results = collection.query(**query_kwargs)

    chunks: list[ChunkResult] = []
    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for chunk_id, doc_text, meta, distance in zip(ids, documents, metadatas, distances):
        # ChromaDB cosine distance: 0 = identical, 2 = opposite.
        # Convert to similarity score in [0, 1].
        score = 1.0 - (distance / 2.0)
        chunks.append(
            ChunkResult(
                chunk_id=chunk_id,
                doc_id=meta.get("doc_id", "unknown"),
                section_type=meta.get("section_type", "unknown"),
                company=meta.get("company", "unknown"),
                text=doc_text,
                score=score,
            )
        )

    logger.debug(
        "retrieve: query=%r section_type=%s company=%s → %d results",
        query[:60],
        section_type,
        company,
        len(chunks),
    )
    return chunks
