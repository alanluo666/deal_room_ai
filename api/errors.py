"""Typed API exceptions.

Centralising these makes router error-handling explicit and removes the
fragile ``"OPENAI_API_KEY" in str(exc)`` string match that previously lived
in three routers. All exceptions remain subclasses of :class:`RuntimeError`
so that existing ``except RuntimeError`` blocks continue to behave as
before; new code should catch the specific subclass.
"""
from __future__ import annotations


class OpenAINotConfiguredError(RuntimeError):
    """Raised when an OpenAI-backed code path runs but the API key is unset.

    Routers map this to a stable, non-leaky response:
      - ``/chat``    → 200 local-dev stub (matches the existing UX)
      - ``/ask``     → 503 "OpenAI is not configured on the server"
      - ``/analyze`` → 503 "OpenAI is not configured on the server"
    """

    def __init__(self, message: str = "OpenAI API key is not configured") -> None:
        super().__init__(message)
