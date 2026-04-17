"""Analysis task presets that sit on top of the grounded RAG flow.

These presets drive :meth:`api.rag.RagService.run_task` for the
``POST /deal-rooms/{id}/analyze`` endpoint. Keeping them in a dedicated
module makes it easy to add more presets later (e.g. ``qa_bank``) without
widening the RAG service contract.
"""
from __future__ import annotations

from enum import Enum


class Task(str, Enum):
    SUMMARY = "summary"
    RISKS = "risks"


RETRIEVAL_QUERIES: dict[Task, str] = {
    Task.SUMMARY: (
        "overview of the company, business model, financials, operations, "
        "products, markets, customers, and key metrics"
    ),
    Task.RISKS: (
        "risks, concerns, liabilities, litigation, threats, adverse events, "
        "exposures, contingencies, and going-concern issues"
    ),
}


INSTRUCTIONS: dict[Task, str] = {
    Task.SUMMARY: (
        "You are a due diligence analyst. Produce a concise executive "
        "summary of the target using ONLY the provided context. Structure "
        "the answer as: 2-3 sentences on the business, 2-3 sentences on key "
        "financials or metrics, and 2-3 sentences on notable items or open "
        "questions. If the context is thin or does not cover a section, say "
        "so explicitly for that section. Do not invent facts, numbers, or "
        "citations."
    ),
    Task.RISKS: (
        "You are a due diligence analyst. Extract concrete risks from the "
        "provided context ONLY. Output a bulleted list. Each bullet is a "
        "short risk label followed by a one-sentence justification drawn "
        "from the context. If no risks are evident, say so explicitly "
        "instead of inventing items. Do not invent facts, risks, or "
        "citations."
    ),
}
