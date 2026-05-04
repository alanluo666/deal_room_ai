"""summarize_document tool — compress retrieved chunks into a concise summary.

The agent uses this when it has retrieved multiple relevant chunks and needs
to distil them before formulating a final answer, or when a user asks for a
section-level summary rather than a specific factual question.
"""

from __future__ import annotations

import json
import logging

import vertexai
from vertexai.generative_models import GenerativeModel

from ..config import GEMINI_MODEL, GCP_LOCATION, GCP_PROJECT
from ..rag.chroma_client import get_chunks_by_ids

logger = logging.getLogger(__name__)

_SUMMARISE_CHUNKS_PROMPT = """\
You are a due diligence analyst. Summarise the following document excerpts
into a concise, factual paragraph (150–300 words). Preserve all important
figures, dates, and named entities exactly as they appear in the source text.
Do not add information that is not present in the excerpts.

DOCUMENT EXCERPTS:
{chunks_text}

SUMMARY:"""


def summarize_document(
    chunk_ids: list[str],
    focus: str | None = None,
) -> str:
    """Summarise the content of specific document chunks.

    Args:
        chunk_ids: List of ChromaDB chunk ids to summarise (1–20 ids).
        focus:     Optional instruction to focus the summary on a particular
                   aspect, e.g. ``"liquidity risk"`` or ``"revenue trends"``.

    Returns:
        JSON string with ``{"summary": "...", "chunk_ids_used": [...]}``
        or ``{"error": "..."}`` on failure.
    """
    if not chunk_ids:
        return json.dumps({"error": "chunk_ids must not be empty."})

    chunk_ids = chunk_ids[:20]  # guard against excessively large requests

    chunks = get_chunks_by_ids(chunk_ids)
    if not chunks:
        return json.dumps({
            "error": f"None of the requested chunk ids were found: {chunk_ids}"
        })

    # Assemble text block
    chunk_texts = []
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        label = f"[{meta.get('section_type', 'unknown')} | {meta.get('doc_id', 'unknown')}]"
        chunk_texts.append(f"{label}\n{chunk['document']}")

    chunks_text = "\n\n---\n\n".join(chunk_texts)

    prompt = _SUMMARISE_CHUNKS_PROMPT.format(chunks_text=chunks_text)
    if focus:
        prompt += f"\n\nFocus especially on: {focus}"

    try:
        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
        model = GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        summary = response.text.strip()
    except Exception as exc:
        logger.error("summarize_document: Gemini call failed: %s", exc)
        return json.dumps({"error": f"Summarisation failed: {exc}"})

    logger.debug(
        "summarize_document: %d chunks → summary (%d chars)", len(chunks), len(summary)
    )

    return json.dumps({
        "summary": summary,
        "chunk_ids_used": [c["id"] for c in chunks],
    })
