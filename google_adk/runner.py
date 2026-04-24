"""ADK Runner and session service setup.

Usage (from Person C's FastAPI /chat endpoint)::

    from google_adk.runner import run_turn

    response_json = await run_turn(session_id="abc123", user_message="What are Apple's key risks?")

The runner handles multi-turn sessions by maintaining state in
InMemorySessionService.  For production, swap in VertexAiSessionService.
"""

from __future__ import annotations

import json
import logging

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from .agent import agent
from .config import ADK_APP_NAME
from .context.history_summarizer import build_summary_turn, maybe_summarize
from .context.layers import assemble_context
from .context.session_state import get_durable_facts
from .schemas import AgentResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Session service (swap for VertexAiSessionService in production)
# ---------------------------------------------------------------------------

session_service = InMemorySessionService()

runner = Runner(
    agent=agent,
    app_name=ADK_APP_NAME,
    session_service=session_service,
)


# ---------------------------------------------------------------------------
# Public interface for the FastAPI layer
# ---------------------------------------------------------------------------

def run_turn(session_id: str, user_message: str) -> AgentResponse:
    """Process one user turn and return a structured AgentResponse.

    This function:
    1. Gets or creates an ADK session for ``session_id``.
    2. Applies history summarisation if the token budget is exceeded.
    3. Refreshes the agent instruction with the current L1 session facts.
    4. Runs the ADK agent and extracts the final AgentResponse from the output.

    Args:
        session_id:   Stable identifier for the conversation (provided by the
                      frontend / FastAPI layer).
        user_message: The user's latest message.

    Returns:
        :class:`AgentResponse` with the answer and citations.
    """
    from google.genai import types as genai_types  # ADK internal message type

    # -- 1. Get or create session ----------------------------------------------
    session = session_service.get_session(
        app_name=ADK_APP_NAME,
        user_id="default",
        session_id=session_id,
    )
    if session is None:
        session = session_service.create_session(
            app_name=ADK_APP_NAME,
            user_id="default",
            session_id=session_id,
        )

    # -- 2. History summarisation ---------------------------------------------
    # ADK stores turns in session.events; convert to simple dicts for the
    # summariser, then store a summary turn back if needed.
    history: list[dict] = [
        {"role": e.author, "content": _extract_text(e)}
        for e in (session.events or [])
        if _extract_text(e)
    ]
    recent_turns, summary_text = maybe_summarize(history)
    if summary_text:
        # Prepend a synthetic summary turn to the recent turns
        summary_turn = build_summary_turn(summary_text)
        recent_turns = [summary_turn] + recent_turns
        logger.info("session=%s: history summarised (%d chars)", session_id, len(summary_text))

    # -- 3. Refresh L1 instruction block in session.state ----------------------
    state = session.state or {}
    facts = get_durable_facts(state)
    updated_instruction = assemble_context(state)
    # Mutate the agent's instruction for this session turn (ADK allows this
    # because LlmAgent.instruction is re-evaluated per run call when supplied
    # as a callable; here we patch in the session-specific string).
    agent.instruction = updated_instruction

    # -- 4. Run the agent ------------------------------------------------------
    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=user_message)],
    )

    final_response_text: str = ""
    for event in runner.run(
        user_id="default",
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    final_response_text += part.text

    # -- 5. Parse structured response ------------------------------------------
    return _parse_agent_output(final_response_text)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_text(event) -> str:
    """Best-effort extraction of text from an ADK event."""
    try:
        if event.content and event.content.parts:
            return " ".join(p.text for p in event.content.parts if p.text)
    except Exception:
        pass
    return ""


def _parse_agent_output(raw: str) -> AgentResponse:
    """Try to parse the agent's final output as AgentResponse JSON.

    If the output is plain prose (no JSON wrapper), wrap it without citations
    so the caller always receives a typed object.
    """
    raw = raw.strip()
    # The agent should call answer_question which returns JSON; look for it
    start = raw.find("{")
    if start != -1:
        try:
            data = json.loads(raw[start:])
            return AgentResponse(**data)
        except Exception:
            pass

    # Fallback: treat the whole text as a plain answer
    return AgentResponse(answer=raw, citations=[], open_questions=[])
