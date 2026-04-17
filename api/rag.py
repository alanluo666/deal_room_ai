"""Retrieval-augmented question answering for a deal room.

The :class:`RagService` takes a question (or analysis task) plus retrieval
and LLM collaborators and produces an answer with citations. It does no
I/O of its own beyond what its collaborators do, which keeps it
unit-testable without the network.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from api.document_processing import EmbeddingClient
from api.schemas import Citation
from api.tasks import INSTRUCTIONS, RETRIEVAL_QUERIES, Task
from api.vector_store import RetrievedChunk, VectorStore

MAX_CONTEXT_CHARS = 8000
SNIPPET_CHARS = 300
NO_ANSWER_TEXT = "I don't know based on the uploaded documents."


class RagLLM(Protocol):
    """Minimal LLM surface the RAG service depends on."""

    model: str

    def run_rag(self, *, prompt: str, instructions: str | None = None) -> str: ...


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


def _format_sources(chunks: list[RetrievedChunk]) -> str:
    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[Source {i} | document_id={chunk.document_id} | chunk={chunk.chunk_index}]\n{chunk.text}"
        )
    return "\n\n".join(parts)


def _build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return (
            f"Question: {question}\n\n"
            "Context: (no documents found)\n\n"
            f'If the context is empty or does not support an answer, reply exactly: "{NO_ANSWER_TEXT}".'
        )
    return (
        f"Question: {question}\n\n"
        f"Context:\n{_format_sources(chunks)}\n\n"
        "Answer strictly from the context above. If the context does not "
        f'contain the answer, reply exactly: "{NO_ANSWER_TEXT}".'
    )


def _build_task_prompt(task: Task, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return (
            f"Task: {task.value}\n\n"
            "Context: (no documents found)\n\n"
            "Follow the task instructions using only the context above. If "
            "the context is empty or does not support a confident response, "
            f'reply exactly: "{NO_ANSWER_TEXT}".'
        )
    return (
        f"Task: {task.value}\n\n"
        f"Context:\n{_format_sources(chunks)}\n\n"
        "Follow the task instructions using only the context above. If the "
        "context does not support a confident response, reply exactly: "
        f'"{NO_ANSWER_TEXT}".'
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
    """Orchestrates retrieval + LLM for a single deal-room question or task."""

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
        retrieved = self._retrieve(
            query_text=question,
            user_id=user_id,
            deal_room_id=deal_room_id,
            top_k=top_k,
        )
        if not retrieved:
            return self._empty_result()

        trimmed = _trim_to_budget(retrieved, MAX_CONTEXT_CHARS)
        prompt = _build_prompt(question, trimmed)
        answer = self._llm.run_rag(prompt=prompt)
        return self._finalize(answer, trimmed, filenames_by_document_id)

    def run_task(
        self,
        *,
        task: Task,
        user_id: int,
        deal_room_id: int,
        top_k: int,
        filenames_by_document_id: dict[int, str],
    ) -> RagResult:
        retrieval_query = RETRIEVAL_QUERIES[task]
        instructions = INSTRUCTIONS[task]

        retrieved = self._retrieve(
            query_text=retrieval_query,
            user_id=user_id,
            deal_room_id=deal_room_id,
            top_k=top_k,
        )
        if not retrieved:
            return self._empty_result()

        trimmed = _trim_to_budget(retrieved, MAX_CONTEXT_CHARS)
        prompt = _build_task_prompt(task, trimmed)
        answer = self._llm.run_rag(prompt=prompt, instructions=instructions)
        return self._finalize(answer, trimmed, filenames_by_document_id)

    def _retrieve(
        self,
        *,
        query_text: str,
        user_id: int,
        deal_room_id: int,
        top_k: int,
    ) -> list[RetrievedChunk]:
        embeddings = self._embedder.embed([query_text])
        if not embeddings:
            raise RuntimeError("Embedding for query returned empty result")
        query_embedding = embeddings[0]
        where = {
            "$and": [
                {"deal_room_id": deal_room_id},
                {"user_id": user_id},
            ]
        }
        return self._vector_store.query(
            embedding=query_embedding,
            where=where,
            top_k=top_k,
        )

    def _empty_result(self) -> RagResult:
        return RagResult(
            answer=NO_ANSWER_TEXT,
            citations=[],
            model=self._llm.model,
            chunks_used=0,
        )

    def _finalize(
        self,
        answer: str,
        trimmed: list[RetrievedChunk],
        filenames_by_document_id: dict[int, str],
    ) -> RagResult:
        citations = _build_citations(trimmed, filenames_by_document_id)
        return RagResult(
            answer=(answer or "").strip() or NO_ANSWER_TEXT,
            citations=citations,
            model=self._llm.model,
            chunks_used=len(trimmed),
        )
