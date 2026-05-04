"""search_documents tool — L2 (and L3) RAG retrieval from ChromaDB.

The agent calls this tool one or more times, refining the query or changing
the section_type filter, which is what makes this *agentic* RAG rather than
a single fixed retrieval pass.

After each call the tool writes the retrieved chunk ids into session.state so
they are preserved as durable citation references even after history
summarisation.
"""

from __future__ import annotations

import json
import logging

from google.adk.tools import ToolContext

from ..config import DEFAULT_TOP_K
from ..context.session_state import update_state
from ..rag.retriever import retrieve
from ..schemas import ChunkResult

logger = logging.getLogger(__name__)

# Section type labels understood by the classifier / ChromaDB metadata
VALID_SECTION_TYPES = {
    "risk_factor",
    "financial_statement",
    "management_discussion",
    "legal_clause",
    "business_overview",
}


def search_documents(
    query: str,
    section_type: str | None = None,
    company: str | None = None,
    top_k: int = DEFAULT_TOP_K,
    tool_context: ToolContext | None = None,
) -> str:
    """Search deal documents using semantic similarity.

    Args:
        query:        Natural-language search query describing what to find.
        section_type: Optional filter to restrict results to a classifier label,
                      e.g. ``"risk_factor"``, ``"financial_statement"``.
        company:      Optional company name or ticker to restrict the search.
        top_k:        Number of results to return (default 5, max 10).
        tool_context: Injected by ADK; used to update session.state.

    Returns:
        JSON string with a list of chunk results including text and metadata.
    """
    # Validate section_type if provided
    if section_type and section_type not in VALID_SECTION_TYPES:
        return json.dumps({
            "error": (
                f"Unknown section_type '{section_type}'. "
                f"Valid values: {sorted(VALID_SECTION_TYPES)}"
            )
        })

    top_k = min(max(1, top_k), 10)

    chunks: list[ChunkResult] = retrieve(
        query=query,
        section_type=section_type,
        company=company,
        top_k=top_k,
    )

    if not chunks:
        return json.dumps({"results": [], "message": "No matching chunks found."})

    # Persist citation ids to session.state for durable fact tracking
    if tool_context is not None:
        chunk_ids = [c.chunk_id for c in chunks]
        update_state(tool_context, new_citations=chunk_ids)

        # Also update active_company if we can infer it
        companies = list({c.company for c in chunks if c.company != "unknown"})
        if len(companies) == 1:
            update_state(tool_context, active_company=companies[0])

    results = [
        {
            "chunk_id": c.chunk_id,
            "doc_id": c.doc_id,
            "section_type": c.section_type,
            "company": c.company,
            "score": round(c.score, 4),
            "text": c.text,
        }
        for c in chunks
    ]

    logger.debug(
        "search_documents: query=%r → %d results (section=%s company=%s)",
        query[:60],
        len(results),
        section_type,
        company,
    )

    return json.dumps({"results": results})
