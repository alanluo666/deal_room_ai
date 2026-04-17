"""Retrieval-augmented question answering for a deal room.

The :class:`RagService` takes a question plus retrieval/LLM collaborators
and produces an answer with citations. It does no I/O of its own beyond
what its collaborators do, which keeps it unit-testable without the
network.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from api.document_processing import EmbeddingClient
from api.schemas import Citation
from api.vector_store import RetrievedChunk, VectorStore

MAX_CONTEXT_CHARS = 8000
SNIPPET_CHARS = 300
NO_ANSWER_TEXT = "I don't know based on the uploaded documents."


class RagLLM(Protocol):
    """Minimal LLM surface the RAG service depends on."""

    model: str

    def run_rag(self, *, prompt: str) -> str: ...


@dataclass(frozen=True)
class RagResult:
    answer: str
    citations: list[Citation]
    model: str
    chunks_used: int


def _trim_to_budget(
    chunks: list[RetrievedChunk], budget: int
) -> list[RetrievedChunk]:
    """Keep chunks in retrieval order until ``budget`` characters are used."""
    out: list[RetrievedChunk] = []
    running = 0
    for chunk in chunks:
        text_len = len(chunk.text)
        if running + text_len > budget:
            remaining = budget - running
            if remaining > 200:
                out.append(
                    RetrievedChunk(
                        document_id=chunk.document_id,
                        deal_room_id=chunk.deal_room_id,
                        user_id=chunk.user_id,
                        chunk_index=chunk.chunk_index,
                        text=chunk.text[:remaining],
                        distance=chunk.distance,
                    )
                )
            break
        out.append(chunk)
        running += text_len
    return out


def _build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return (
            f"Question: {question}\n\n"
            "Context: (no documents found)\n\n"
            f'If the context is empty or does not support an answer, reply exactly: "{NO_ANSWER_TEXT}".'
        )
    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[Source {i} | document_id={chunk.document_id} | chunk={chunk.chunk_index}]\n{chunk.text}"
        )
    context = "\n\n".join(parts)
    return (
        f"Question: {question}\n\n"
        f"Context:\n{context}\n\n"
        "Answer strictly from the context above. If the context does not "
        f'contain the answer, reply exactly: "{NO_ANSWER_TEXT}".'
    )


def _build_citations(
    chunks: list[RetrievedChunk],
    filenames_by_document_id: dict[int, str],
    snippet_chars: int = SNIPPET_CHARS,
) -> list[Citation]:
    seen: set[tuple[int, int]] = set()
    out: list[Citation] = []
    for chunk in chunks:
        key = (chunk.document_id, chunk.chunk_index)
        if key in seen:
            continue
        seen.add(key)
        snippet = " ".join(chunk.text.split())
        if len(snippet) > snippet_chars:
            snippet = snippet[:snippet_chars].rstrip() + "..."
        out.append(
            Citation(
                document_id=chunk.document_id,
                filename=filenames_by_document_id.get(
                    chunk.document_id, f"document-{chunk.document_id}"
                ),
                chunk_index=chunk.chunk_index,
                snippet=snippet,
            )
        )
    return out


class RagService:
    """Orchestrates retrieval + LLM for a single deal-room question."""

    def __init__(
        self,
        *,
        vector_store: VectorStore,
        embedder: EmbeddingClient,
        llm: RagLLM,
    ) -> None:
        self._vector_store = vector_store
        self._embedder = embedder
        self._llm = llm

    @property
    def model(self) -> str:
        return self._llm.model

    def ask(
        self,
        *,
        question: str,
        user_id: int,
        deal_room_id: int,
        top_k: int,
        filenames_by_document_id: dict[int, str],
    ) -> RagResult:
        embeddings = self._embedder.embed([question])
        if not embeddings:
            raise RuntimeError("Embedding for question returned empty result")
        query_embedding = embeddings[0]

        where = {
            "$and": [
                {"deal_room_id": deal_room_id},
                {"user_id": user_id},
            ]
        }
        retrieved = self._vector_store.query(
            embedding=query_embedding,
            where=where,
            top_k=top_k,
        )

        if not retrieved:
            return RagResult(
                answer=NO_ANSWER_TEXT,
                citations=[],
                model=self._llm.model,
                chunks_used=0,
            )

        trimmed = _trim_to_budget(retrieved, MAX_CONTEXT_CHARS)
        prompt = _build_prompt(question, trimmed)
        answer = self._llm.run_rag(prompt=prompt)
        citations = _build_citations(trimmed, filenames_by_document_id)

        return RagResult(
            answer=(answer or "").strip() or NO_ANSWER_TEXT,
            citations=citations,
            model=self._llm.model,
            chunks_used=len(trimmed),
        )
