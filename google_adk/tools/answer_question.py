"""answer_question tool — citation-enforced final answer construction.

This is the last tool the agent calls. It enforces that at least one citation
chunk id is supplied before producing a structured response. This is the
primary guardrail against the agent inventing figures without evidence.
"""

from __future__ import annotations

import json
import logging

from google.adk.tools import ToolContext

from ..context.session_state import update_state
from ..rag.chroma_client import get_chunks_by_ids
from ..schemas import AgentResponse, Citation

logger = logging.getLogger(__name__)


def answer_question(
    question: str,
    citation_chunk_ids: list[str],
    answer: str,
    open_questions: list[str] | None = None,
    tool_context: ToolContext | None = None,
) -> str:
    """Produce a structured, citation-backed answer to a due diligence question.

    The agent MUST provide at least one chunk id from a prior ``search_documents``
    call. If ``citation_chunk_ids`` is empty the tool returns an error, forcing
    the agent to retrieve evidence before answering.

    Args:
        question:           The user's original question (echoed in the response).
        citation_chunk_ids: Chunk ids retrieved by ``search_documents`` that
                            support the answer.  Must not be empty.
        answer:             The prose answer synthesised from the retrieved context.
        open_questions:     Optional list of follow-up questions the agent flagged
                            as unresolved; persisted to session.state.
        tool_context:       Injected by ADK; used to update session.state.

    Returns:
        JSON string matching :class:`AgentResponse`, or ``{"error": "..."}``
        if citation enforcement fails.
    """
    # -- Citation enforcement guardrail -----------------------------------------
    if not citation_chunk_ids:
        return json.dumps({
            "error": (
                "answer_question requires at least one citation_chunk_id. "
                "Call search_documents first to retrieve supporting evidence, "
                "then include the returned chunk_ids here."
            )
        })

    # -- Fetch chunk metadata to build Citation objects -------------------------
    chunks = get_chunks_by_ids(citation_chunk_ids)
    chunk_map = {c["id"]: c for c in chunks}

    citations: list[Citation] = []
    for chunk_id in citation_chunk_ids:
        chunk = chunk_map.get(chunk_id)
        if chunk:
            meta = chunk.get("metadata", {})
            citations.append(
                Citation(
                    chunk_id=chunk_id,
                    doc_id=meta.get("doc_id", "unknown"),
                    section_type=meta.get("section_type", "unknown"),
                    excerpt=chunk.get("document", "")[:300],
                )
            )
        else:
            # Include a minimal citation so the structure is preserved
            citations.append(
                Citation(
                    chunk_id=chunk_id,
                    doc_id="unknown",
                    section_type="unknown",
                    excerpt="",
                )
            )

    # -- Persist open questions to session.state --------------------------------
    if open_questions and tool_context is not None:
        update_state(tool_context, new_questions=open_questions)

    # -- Build structured response ----------------------------------------------
    response = AgentResponse(
        answer=answer,
        citations=citations,
        open_questions=open_questions or [],
    )

    logger.debug(
        "answer_question: question=%r → %d citations, %d open questions",
        question[:60],
        len(citations),
        len(response.open_questions),
    )

    return json.dumps(response.model_dump())
