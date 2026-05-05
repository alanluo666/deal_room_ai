from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_user, rag_service_dep
from api.errors import OpenAINotConfiguredError
from api.models import Question, User
from api.rag import RagService
from api.routers._helpers import filenames_by_document_id, load_owned_deal_room
from api.schemas import AskRequest, AskResponse, Citation, QuestionRead
from api.tracking import elapsed_seconds, timed_call, tracking_manager

logger = logging.getLogger("api.questions")

router = APIRouter(prefix="/deal-rooms/{deal_room_id}", tags=["questions"])


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    deal_room_id: int,
    payload: AskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag: RagService = Depends(rag_service_dep),
) -> AskResponse:
    await load_owned_deal_room(db, deal_room_id, current_user)
    filenames = await filenames_by_document_id(db, deal_room_id)

    started = timed_call()
    try:
        result = rag.ask(
            question=payload.question,
            user_id=current_user.id,
            deal_room_id=deal_room_id,
            top_k=payload.top_k,
            filenames_by_document_id=filenames,
        )
    except OpenAINotConfiguredError as exc:
        tracking_manager.log_ask(
            model_name=rag.model,
            top_k=payload.top_k,
            chunks_used=0,
            latency_seconds=elapsed_seconds(started),
            success=False,
            error_message="openai_not_configured",
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI is not configured on the server",
        ) from exc
    except Exception as exc:
        logger.exception("ask failed for deal_room_id=%s", deal_room_id)
        tracking_manager.log_ask(
            model_name=rag.model,
            top_k=payload.top_k,
            chunks_used=0,
            latency_seconds=elapsed_seconds(started),
            success=False,
            error_message=type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ask failed. Please try again.",
        ) from exc

    citations_json = [c.model_dump() for c in result.citations]
    question_row = Question(
        deal_room_id=deal_room_id,
        user_id=current_user.id,
        question=payload.question,
        answer=result.answer,
        citations=citations_json,
    )
    db.add(question_row)
    await db.commit()
    await db.refresh(question_row)

    tracking_manager.log_ask(
        model_name=result.model,
        top_k=payload.top_k,
        chunks_used=result.chunks_used,
        latency_seconds=elapsed_seconds(started),
        success=True,
    )

    return AskResponse(
        question_id=question_row.id,
        answer=result.answer,
        citations=result.citations,
        model=result.model,
        chunks_used=result.chunks_used,
    )


@router.get("/questions", response_model=list[QuestionRead])
async def list_questions(
    deal_room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[QuestionRead]:
    await load_owned_deal_room(db, deal_room_id, current_user)
    result = await db.execute(
        select(Question)
        .where(Question.deal_room_id == deal_room_id)
        .order_by(Question.created_at.desc(), Question.id.desc())
    )
    rows = list(result.scalars().all())
    return [
        QuestionRead(
            id=row.id,
            deal_room_id=row.deal_room_id,
            user_id=row.user_id,
            question=row.question,
            answer=row.answer,
            citations=[Citation(**c) for c in (row.citations or [])],
            created_at=row.created_at,
        )
        for row in rows
    ]
