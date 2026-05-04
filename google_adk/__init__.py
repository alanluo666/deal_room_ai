"""Deal Room AI — Google ADK agent package.

Public API
----------
.. code-block:: python

    from google_adk import run_turn, agent, runner, AgentResponse

    # Single turn (used by FastAPI /chat endpoint)
    response = run_turn(session_id="abc123", user_message="What are Apple's key risks?")
    print(response.answer)
    for citation in response.citations:
        print(citation.chunk_id, citation.excerpt)
"""

from .agent import agent
from .runner import run_turn, runner, session_service
from .schemas import AgentResponse, Citation, DurableFacts, RiskItem

__all__ = [
    "agent",
    "runner",
    "run_turn",
    "session_service",
    "AgentResponse",
    "Citation",
    "DurableFacts",
    "RiskItem",
]
