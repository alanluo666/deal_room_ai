from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """A reference to a specific chunk retrieved from ChromaDB."""

    chunk_id: str = Field(description="ChromaDB document id for the chunk")
    doc_id: str = Field(description="Source filing / document identifier")
    section_type: str = Field(
        description="Classifier-assigned section label, e.g. risk_factor"
    )
    excerpt: str = Field(description="Short verbatim excerpt from the chunk")


class ChunkResult(BaseModel):
    """Internal type returned by the retriever before converting to Citation."""

    chunk_id: str
    doc_id: str
    section_type: str
    company: str
    text: str
    score: float = Field(description="Cosine similarity score (higher = more relevant)")

    def to_citation(self) -> Citation:
        return Citation(
            chunk_id=self.chunk_id,
            doc_id=self.doc_id,
            section_type=self.section_type,
            excerpt=self.text[:300],
        )


class RiskItem(BaseModel):
    """A single identified risk from a due diligence document."""

    category: str = Field(
        description="Risk category, e.g. regulatory, financial, operational"
    )
    description: str = Field(description="Concise description of the risk")
    severity: Literal["low", "medium", "high"]
    citation: Citation


class AgentResponse(BaseModel):
    """Structured output returned to the FastAPI /chat endpoint."""

    answer: str = Field(description="Prose answer to the user's question")
    citations: list[Citation] = Field(
        default_factory=list,
        description="Evidence chunks that support the answer",
    )
    open_questions: list[str] = Field(
        default_factory=list,
        description="Follow-up questions the agent flagged as unresolved",
    )


class DurableFacts(BaseModel):
    """Facts persisted in ADK session.state to survive history summarization."""

    confirmed_metrics: dict[str, str] = Field(
        default_factory=dict,
        description="Key financial / operational metrics confirmed this session",
    )
    cited_doc_ids: list[str] = Field(
        default_factory=list,
        description="All chunk ids cited so far in this session",
    )
    open_questions: list[str] = Field(
        default_factory=list,
        description="Unresolved questions carried across turns",
    )
    active_company: str | None = Field(
        default=None,
        description="Company / ticker currently under analysis",
    )
