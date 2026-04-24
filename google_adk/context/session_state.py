"""ADK session.state management for durable facts.

ADK exposes ``session.state`` as a plain dict. This module provides typed
helpers for reading and writing the Deal Room facts that must survive history
summarisation (citations, open questions, active company, confirmed metrics).

Tools receive a ``ToolContext`` object from ADK. Its ``.state`` attribute is
the live session state dict — mutations are persisted by the ADK session
service automatically.
"""

from __future__ import annotations

from ..schemas import DurableFacts

# Keys written to session.state
_KEY_METRICS = "confirmed_metrics"
_KEY_CITED = "cited_doc_ids"
_KEY_QUESTIONS = "open_questions"
_KEY_COMPANY = "active_company"

DURABLE_KEYS = [_KEY_METRICS, _KEY_CITED, _KEY_QUESTIONS, _KEY_COMPANY]


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

def update_state(
    tool_context,  # google.adk.tools.tool_context.ToolContext
    new_citations: list[str] | None = None,
    new_questions: list[str] | None = None,
    confirmed_metrics: dict[str, str] | None = None,
    active_company: str | None = None,
) -> None:
    """Merge new information into the live ADK session.state.

    Designed to be called from within tool functions where ``tool_context``
    is the ADK-injected parameter.
    """
    state = tool_context.state

    # Cited chunk ids — accumulate across turns
    if new_citations:
        existing: list[str] = state.get(_KEY_CITED, [])
        merged = list(dict.fromkeys(existing + new_citations))  # deduplicate, preserve order
        state[_KEY_CITED] = merged

    # Open questions — accumulate, deduplication by value
    if new_questions:
        existing_q: list[str] = state.get(_KEY_QUESTIONS, [])
        for q in new_questions:
            if q not in existing_q:
                existing_q.append(q)
        state[_KEY_QUESTIONS] = existing_q

    # Confirmed metrics — merge dict (new values overwrite old for same key)
    if confirmed_metrics:
        existing_m: dict[str, str] = state.get(_KEY_METRICS, {})
        existing_m.update(confirmed_metrics)
        state[_KEY_METRICS] = existing_m

    # Active company — overwrite if provided
    if active_company is not None:
        state[_KEY_COMPANY] = active_company


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

def get_durable_facts(state: dict) -> DurableFacts:
    """Extract durable facts from a raw session.state dict into a typed model."""
    return DurableFacts(
        confirmed_metrics=state.get(_KEY_METRICS, {}),
        cited_doc_ids=state.get(_KEY_CITED, []),
        open_questions=state.get(_KEY_QUESTIONS, []),
        active_company=state.get(_KEY_COMPANY),
    )
