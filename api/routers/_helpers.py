"""Shared router helpers.

Small, route-oriented utilities that more than one router needs. Keeping
them here avoids cross-router imports (e.g. ``analyze.py`` reaching into
``questions.py``) and removes the duplicate ``_load_owned_deal_room``
copies that lived in both ``documents.py`` and ``questions.py``.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import DealRoom, Document, User


async def load_owned_deal_room(
    db: AsyncSession, deal_room_id: int, user: User
) -> DealRoom:
    """Return the deal room if it exists and is owned by ``user``.

    Raises :class:`HTTPException` 404 for both "does not exist" and
    "not owned by caller" so cross-user probes cannot be distinguished
    from missing ids.
    """
    result = await db.execute(
        select(DealRoom).where(
            DealRoom.id == deal_room_id,
            DealRoom.owner_id == user.id,
        )
    )
    deal_room = result.scalar_one_or_none()
    if deal_room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deal room not found"
        )
    return deal_room


async def filenames_by_document_id(
    db: AsyncSession, deal_room_id: int
) -> dict[int, str]:
    """Map ``document_id -> filename`` for every document in a deal room.

    Used by routers that need to hydrate citations with their original
    upload filenames without loading the full ``Document`` rows.
    """
    result = await db.execute(
        select(Document.id, Document.filename).where(
            Document.deal_room_id == deal_room_id
        )
    )
    return {row.id: row.filename for row in result.all()}
