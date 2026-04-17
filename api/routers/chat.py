"""``POST /deal-rooms/{deal_room_id}/chat`` — Person C thin wrapper.

Design notes
------------
* Same auth + ownership rules as ``/ask``. Cross-user or missing-room
  requests get 404 for parity with the rest of the deal-room surface.
* The route accepts the full ``messages`` history and an optional
  ``session_id`` so the React client can evolve into a multi-turn chat
  without a schema bump. Today the backend only consumes the last user
  turn and passes it through :meth:`api.rag.RagService.ask`. Person A's
  ADK agent lands behind the same route later, either by implementing
  :class:`api.rag.RagLLM` or by replacing ``rag_service_dep`` — neither
  change requires a frontend edit.
* ``/chat`` **does not** persist turns to the ``questions`` table. That
  table belongs to ``/ask`` and we do not want to double-log a single
  conversation. Chat history lives in the React client for now; the
  agent session store is Person A's concern later.
* Local-dev safety: when ``OPENAI_API_KEY`` is not configured we return a
  clearly labelled 200 stub response instead of 503. This keeps the
  ChatPanel usable in a fresh clone without any secrets, which matches
  the Person C guardrail that new backend paths must stay local-only by
  default. ``/ask`` keeps its existing 503 behaviour; the divergence is
  deliberate and documented.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_user, rag_service_dep
from api.models import User
from api.rag import RagService
from api.routers._helpers import filenames_by_document_id, load_owned_deal_room
from api.schemas import ChatMessage, ChatRequest, ChatResponse, ChatRole
from api.service import openai_service
from api.tracking import elapsed_seconds, timed_call, tracking_manager

router = APIRouter(prefix="/deal-rooms/{deal_room_id}", tags=["chat"])

LOCAL_DEV_STUB_MODEL = "local-dev-stub"
LOCAL_DEV_STUB_MESSAGE = (
    "OpenAI is not configured on this server, so /chat is running in "
    "local-dev stub mode. Set OPENAI_API_KEY and restart the API to get "
    "grounded answers from the uploaded documents."
)


def _last_user_message(messages: list[ChatMessage]) -> ChatMessage | None:
    # Pydantic guarantees messages has at least one entry (min_length=1).
    # We require the final turn to be a user message: rejecting trailing
    # assistant/system turns keeps the contract predictable for both the
    # React client today and the ADK agent that lands behind this route
    # later.
    last = messages[-1]
    if last.role != ChatRole.USER:
        return None
    return last


def _stub_response(session_id: str | None) -> ChatResponse:
    return ChatResponse(
        message=ChatMessage(role=ChatRole.ASSISTANT, content=LOCAL_DEV_STUB_MESSAGE),
        citations=[],
        model=LOCAL_DEV_STUB_MODEL,
        chunks_used=0,
        session_id=session_id,
        steps=[],
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    deal_room_id: int,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag: RagService = Depends(rag_service_dep),
) -> ChatResponse:
    await load_owned_deal_room(db, deal_room_id, current_user)

    last_user = _last_user_message(payload.messages)
    if last_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="messages must end with a user turn",
        )

    if not openai_service.is_ready():
        return _stub_response(payload.session_id)

    filenames = await filenames_by_document_id(db, deal_room_id)

    started = timed_call()
    try:
        result = rag.ask(
            question=last_user.content,
            user_id=current_user.id,
            deal_room_id=deal_room_id,
            top_k=payload.top_k,
            filenames_by_document_id=filenames,
        )
    except RuntimeError as exc:
        message = str(exc)
        tracking_manager.log_ask(
            model_name=rag.model,
            top_k=payload.top_k,
            chunks_used=0,
            latency_seconds=elapsed_seconds(started),
            success=False,
            error_message=message,
        )
        # Defensive: a config race between the startup is_ready() check and
        # the actual call should still degrade gracefully rather than 503.
        if "OPENAI_API_KEY" in message:
            return _stub_response(payload.session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        ) from exc

    tracking_manager.log_ask(
        model_name=result.model,
        top_k=payload.top_k,
        chunks_used=result.chunks_used,
        latency_seconds=elapsed_seconds(started),
        success=True,
    )

    return ChatResponse(
        message=ChatMessage(role=ChatRole.ASSISTANT, content=result.answer),
        citations=result.citations,
        model=result.model,
        chunks_used=result.chunks_used,
        session_id=payload.session_id,
        steps=[],
    )
