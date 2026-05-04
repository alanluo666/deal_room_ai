"""analyze_risks tool — extract and categorise risks from a company's filing.

The agent calls this tool when the user asks about risks or when the agent
determines it needs a structured risk breakdown before answering. It
automatically retrieves risk_factor chunks if none are supplied.
"""

from __future__ import annotations

import json
import logging
from typing import Literal

import vertexai
from vertexai.generative_models import GenerativeModel

from ..config import GEMINI_MODEL, GCP_LOCATION, GCP_PROJECT
from ..rag.retriever import retrieve
from ..schemas import Citation, RiskItem

logger = logging.getLogger(__name__)

_RISK_EXTRACTION_PROMPT = """\
You are a senior due diligence analyst. Given the following document excerpts
from a company's SEC 10-K filing, extract and categorise the key risks.

For EACH risk item produce exactly this JSON object (no extra keys):
{{
  "category": "<one of: regulatory, financial, operational, market, legal, reputational, other>",
  "description": "<one concise sentence describing the risk>",
  "severity": "<one of: low, medium, high>",
  "chunk_id": "<the chunk_id of the excerpt that contains this risk>"
}}

Return a JSON array of these objects. Do not include risks not supported by
the provided excerpts. Do not add commentary outside the JSON array.

DOCUMENT EXCERPTS:
{excerpts}

JSON ARRAY:"""


def analyze_risks(
    company: str,
    context_chunks: list[dict] | None = None,
    top_k: int = 8,
) -> str:
    """Identify and categorise risk factors for a company.

    Args:
        company:        Company name or ticker to analyse.
        context_chunks: Optional list of pre-retrieved chunk dicts (each with
                        ``chunk_id``, ``text``, ``section_type``). When omitted
                        the tool retrieves risk_factor chunks automatically.
        top_k:          How many risk_factor chunks to retrieve when
                        ``context_chunks`` is not supplied.

    Returns:
        JSON string ``{"risks": [...], "company": "..."}`` where each risk
        item matches the :class:`RiskItem` schema, or ``{"error": "..."}``
        on failure.
    """
    # -- 1. Obtain chunks -------------------------------------------------------
    if context_chunks:
        chunks = context_chunks
    else:
        retrieved = retrieve(
            query=f"{company} risk factors regulatory financial operational",
            section_type="risk_factor",
            company=company,
            top_k=top_k,
        )
        chunks = [
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "section_type": c.section_type,
                "text": c.text,
            }
            for c in retrieved
        ]

    if not chunks:
        return json.dumps({
            "error": f"No risk_factor chunks found for company '{company}'."
        })

    # -- 2. Build prompt --------------------------------------------------------
    excerpt_parts = []
    for chunk in chunks:
        excerpt_parts.append(
            f"chunk_id: {chunk.get('chunk_id', 'unknown')}\n"
            f"section_type: {chunk.get('section_type', 'unknown')}\n"
            f"{chunk.get('text', '')}"
        )
    excerpts_text = "\n\n---\n\n".join(excerpt_parts)
    prompt = _RISK_EXTRACTION_PROMPT.format(excerpts=excerpts_text)

    # -- 3. Call Gemini ---------------------------------------------------------
    try:
        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
        model = GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        raw_json = response.text.strip()

        # Strip markdown fences if present
        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.startswith("json"):
                raw_json = raw_json[4:]

        raw_items: list[dict] = json.loads(raw_json)
    except Exception as exc:
        logger.error("analyze_risks: Gemini or JSON parse failed: %s", exc)
        return json.dumps({"error": f"Risk extraction failed: {exc}"})

    # -- 4. Validate and enrich with Citation -----------------------------------
    chunk_map = {c.get("chunk_id"): c for c in chunks}
    risk_items: list[dict] = []

    for item in raw_items:
        chunk_id = item.get("chunk_id", "")
        source_chunk = chunk_map.get(chunk_id, {})
        citation = Citation(
            chunk_id=chunk_id,
            doc_id=source_chunk.get("doc_id", "unknown"),
            section_type=source_chunk.get("section_type", "risk_factor"),
            excerpt=source_chunk.get("text", "")[:300],
        )
        risk = RiskItem(
            category=item.get("category", "other"),
            description=item.get("description", ""),
            severity=item.get("severity", "medium"),  # type: ignore[arg-type]
            citation=citation,
        )
        risk_items.append(risk.model_dump())

    logger.debug("analyze_risks: %s → %d risk items", company, len(risk_items))

    return json.dumps({"risks": risk_items, "company": company})
