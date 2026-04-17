"""Task preset endpoints (``POST /deal-rooms/{id}/analyze``).

This router wraps the existing grounded RAG pipeline with task-specific
retrieval queries and instructions. Results are intentionally stateless
for M4: we do not persist ``AnalyzeResponse`` rows. Clients re-request
as needed.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_user, rag_service_dep
from api.models import User
from api.rag import RagService
from api.routers._helpers import filenames_by_document_id, load_owned_deal_room
from api.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter(prefix="/deal-rooms/{deal_room_id}", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_deal_room(
    deal_room_id: int,
    payload: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag: RagService = Depends(rag_service_dep),
) -> AnalyzeResponse:
    await load_owned_deal_room(db, deal_room_id, current_user)
    filenames = await filenames_by_document_id(db, deal_room_id)

    try:
        result = rag.run_task(
            task=payload.task,
            user_id=current_user.id,
            deal_room_id=deal_room_id,
            top_k=payload.top_k,
            filenames_by_document_id=filenames,
        )
    except RuntimeError as exc:
        message = str(exc)
        if "OPENAI_API_KEY" in message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI is not configured on the server",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        ) from exc

    return AnalyzeResponse(
        task=payload.task.value,
        answer=result.answer,
        citations=result.citations,
        model=result.model,
        chunks_used=result.chunks_used,
    )
