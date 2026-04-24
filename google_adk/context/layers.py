"""L0–L3 context layer assembly for the Deal Room ADK agent.

Layer summary
-------------
L0  Fixed system prompt: agent identity + hard rules (always in prompt).
L1  Session-specific critical facts pulled from ADK session.state (~100-200 tokens).
L2  RAG chunks returned by tool calls per turn (inserted by the tool response).
L3  Optional second-pass / broader retrieval, triggered by the agent's own reasoning.

L0 and L1 are assembled here into the agent ``instruction`` string. L2 and L3
flow through the tool responses and are therefore handled automatically by ADK.
"""

from __future__ import annotations

from ..schemas import DurableFacts

# ---------------------------------------------------------------------------
# L0: Identity and hard rules
# ---------------------------------------------------------------------------

_L0_INSTRUCTION = """\
You are a due diligence analyst for Deal Room AI.

IDENTITY
- Your role is to help investment teams analyse SEC 10-K filings and related documents.
- You answer questions about risks, financials, legal issues, and business operations.
- You are precise, evidence-driven, and never speculate beyond what the documents say.

HARD RULES (always follow, no exceptions)
1. NEVER state a financial figure, metric, or forward-looking claim without citing the
   exact chunk that contains it. If no retrieved chunk supports the claim, say so.
2. If a question cannot be answered from the retrieved context, respond with:
   "I was unable to find supporting evidence for this in the available documents."
3. Do not fabricate section labels, document names, or company data.
4. When uncertain, surface the uncertainty explicitly rather than guessing.
5. Always prefer calling `search_documents` one or more times before calling
   `answer_question` — the latter enforces that citations are present.

TOOL USAGE PATTERN (agentic RAG)
1. Receive user question.
2. Call `search_documents` with the most relevant query and optional section_type filter.
3. Review returned chunks. If context is insufficient, call `search_documents` again
   with a refined or broader query (L3 retrieval).
4. If a company has multiple risk areas, call `analyze_risks` before `answer_question`.
5. Finish by calling `answer_question` with the assembled evidence.
"""


def build_l0_instruction() -> str:
    """Return the fixed L0 system prompt string."""
    return _L0_INSTRUCTION.strip()


# ---------------------------------------------------------------------------
# L1: Session-specific critical facts from session.state
# ---------------------------------------------------------------------------

def build_l1_block(facts: DurableFacts) -> str:
    """Render L1 context block from durable session facts.

    The block is short by design (~100–200 tokens) and is appended to the
    agent instruction at session start and after each summarization cycle.
    """
    lines: list[str] = ["--- SESSION FACTS (L1) ---"]

    if facts.active_company:
        lines.append(f"Active company under analysis: {facts.active_company}")

    if facts.confirmed_metrics:
        lines.append("Confirmed metrics this session:")
        for key, value in facts.confirmed_metrics.items():
            lines.append(f"  - {key}: {value}")

    if facts.cited_doc_ids:
        lines.append(
            f"Chunks already cited ({len(facts.cited_doc_ids)} total): "
            + ", ".join(facts.cited_doc_ids[:10])
            + (" ..." if len(facts.cited_doc_ids) > 10 else "")
        )

    if facts.open_questions:
        lines.append("Open questions not yet resolved:")
        for q in facts.open_questions:
            lines.append(f"  ? {q}")

    lines.append("--- END SESSION FACTS ---")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Combined assembler
# ---------------------------------------------------------------------------

def assemble_context(state: dict) -> str:
    """Assemble the full agent instruction from L0 + L1 for a given session.

    Called by the runner when constructing or refreshing the agent instruction
    (e.g. after history summarization replaces old turns).
    """
    from ..context.session_state import get_durable_facts  # avoid circular at module level

    facts = get_durable_facts(state)
    l0 = build_l0_instruction()
    l1 = build_l1_block(facts)
    return f"{l0}\n\n{l1}"
