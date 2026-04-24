"""Chat-history token budget and LLM summarisation.

When cumulative conversation history exceeds HISTORY_TOKEN_BUDGET tokens, this
module compresses the oldest turns into a running summary via a single Gemini
Flash call, keeping only the HISTORY_KEEP_RECENT most-recent turns verbatim.

Turn format
-----------
Each turn is a dict with keys ``role`` (``"user"`` or ``"assistant"``) and
``content`` (str). The runner passes the turn list before each Gemini call.
"""

from __future__ import annotations

import logging

import tiktoken

from ..config import GEMINI_MODEL, GCP_LOCATION, GCP_PROJECT, HISTORY_KEEP_RECENT, HISTORY_TOKEN_BUDGET

logger = logging.getLogger(__name__)

# tiktoken encoding for approximate token counting (cl100k is close enough for
# Gemini token estimation; exact parity is not required here)
_enc = tiktoken.get_encoding("cl100k_base")


# ---------------------------------------------------------------------------
# Token counting
# ---------------------------------------------------------------------------

def _count_tokens(turns: list[dict]) -> int:
    """Return approximate token count for a list of turn dicts."""
    total = 0
    for turn in turns:
        total += len(_enc.encode(turn.get("content", "")))
    return total


# ---------------------------------------------------------------------------
# Summarisation call
# ---------------------------------------------------------------------------

_SUMMARISE_PROMPT = """\
You are a conversation summariser for a due diligence AI assistant.

Below is a series of conversation turns between a user and an AI analyst
working on SEC 10-K document analysis. Produce a concise factual summary
(maximum 200 words) that captures:
- The company or companies under analysis
- Key questions asked and answers given
- Important facts, metrics, or risks confirmed
- Any outstanding open questions

Do NOT include speculation. Use bullet points. Start with "Summary so far:".

CONVERSATION:
{conversation}
"""


def _call_gemini_summarise(turns: list[dict]) -> str:
    """Send old turns to Gemini Flash and return a summary string."""
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
        model = GenerativeModel(GEMINI_MODEL)

        conversation_text = "\n".join(
            f"{t['role'].upper()}: {t['content']}" for t in turns
        )
        prompt = _SUMMARISE_PROMPT.format(conversation=conversation_text)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as exc:
        logger.warning("History summarisation failed (%s); using truncated history.", exc)
        return "(Summary unavailable — see truncated history above.)"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def maybe_summarize(
    turns: list[dict],
) -> tuple[list[dict], str]:
    """Conditionally summarise old turns to stay within the token budget.

    Args:
        turns: Full conversation history as a list of ``{role, content}`` dicts.

    Returns:
        A tuple ``(recent_turns, summary_text)`` where:
        - ``recent_turns`` are the HISTORY_KEEP_RECENT most-recent turns kept verbatim.
        - ``summary_text`` is a prose summary of the older turns (empty string if no
          summarisation was needed).

    The caller is responsible for prepending the summary as a pseudo-system
    message before passing ``recent_turns`` to the ADK runner.
    """
    if _count_tokens(turns) <= HISTORY_TOKEN_BUDGET:
        return turns, ""

    if len(turns) <= HISTORY_KEEP_RECENT:
        # Not enough history to split — keep everything verbatim
        return turns, ""

    recent = turns[-HISTORY_KEEP_RECENT:]
    old = turns[:-HISTORY_KEEP_RECENT]

    logger.info(
        "History token budget exceeded — summarising %d old turns, keeping %d recent.",
        len(old),
        len(recent),
    )

    summary = _call_gemini_summarise(old)
    return recent, summary


def build_summary_turn(summary_text: str) -> dict:
    """Wrap a summary string as a synthetic ``system`` turn for the history list."""
    return {
        "role": "system",
        "content": f"[Previous conversation summary]\n{summary_text}",
    }
