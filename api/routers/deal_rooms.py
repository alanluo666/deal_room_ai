from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_user, vector_store_dep
from api.models import DealRoom, Document, User
from api.routers.documents import _cleanup_document_side_effects
from api.schemas import DealRoomCreate, DealRoomRead
from api.vector_store import VectorStore

router = APIRouter(prefix="/deal-rooms", tags=["deal-rooms"])


@router.post("", response_model=DealRoomRead, status_code=status.HTTP_201_CREATED)
async def create_deal_room(
    payload: DealRoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealRoom:
    deal_room = DealRoom(
        owner_id=current_user.id,
        name=payload.name,
        target_company=payload.target_company,
    )
    db.add(deal_room)
    await db.commit()
    await db.refresh(deal_room)
    return deal_room


@router.get("", response_model=list[DealRoomRead])
async def list_deal_rooms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DealRoom]:
    result = await db.execute(
        select(DealRoom)
        .where(DealRoom.owner_id == current_user.id)
        .order_by(DealRoom.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{deal_room_id}", response_model=DealRoomRead)
async def get_deal_room(
    deal_room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealRoom:
    result = await db.execute(
        select(DealRoom).where(
            DealRoom.id == deal_room_id,
            DealRoom.owner_id == current_user.id,
        )
    )
    deal_room = result.scalar_one_or_none()
    if deal_room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal room not found")
    return deal_room


@router.delete("/{deal_room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal_room(
    deal_room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    vector_store: VectorStore = Depends(vector_store_dep),
) -> Response:
    result = await db.execute(
        select(DealRoom).where(
            DealRoom.id == deal_room_id,
            DealRoom.owner_id == current_user.id,
        )
    )
    deal_room = result.scalar_one_or_none()
    if deal_room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal room not found")

    documents_result = await db.execute(
        select(Document).where(Document.deal_room_id == deal_room.id)
    )
    for document in documents_result.scalars().all():
        _cleanup_document_side_effects(document, vector_store)

    await db.delete(deal_room)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
