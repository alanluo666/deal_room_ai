"""Deal Room ADK agent definition.

The agent is an LlmAgent backed by Gemini 2.0 Flash that orchestrates four
tools to perform agentic RAG over the ChromaDB vector store. The L0 system
instruction (identity + hard rules) is built at import time; the L1 session
block is injected by the runner per session.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent

from .config import GEMINI_MODEL
from .context.layers import build_l0_instruction
from .tools import analyze_risks, answer_question, search_documents, summarize_document

agent = LlmAgent(
    model=GEMINI_MODEL,
    name="deal_room_agent",
    description=(
        "Due diligence analyst for Deal Room AI. "
        "Searches SEC 10-K documents, extracts risks, and answers questions "
        "with evidence-backed citations."
    ),
    instruction=build_l0_instruction(),
    tools=[
        search_documents,
        summarize_document,
        analyze_risks,
        answer_question,
    ],
)
