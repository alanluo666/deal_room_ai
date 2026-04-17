from __future__ import annotations

import hashlib
import os
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.db import get_db
from api.deps import embedding_client_dep, get_current_user, vector_store_dep
from api.document_processing import (
    ALLOWED_MIME_TYPES,
    EmbeddingClient,
    build_chunks,
    is_supported,
)
from api.models import Document, DocumentStatus, User
from api.routers._helpers import load_owned_deal_room
from api.schemas import DocumentRead
from api.vector_store import VectorStore

router = APIRouter(prefix="/deal-rooms/{deal_room_id}/documents", tags=["documents"])


_EXTENSION_BY_MIME = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
}


async def _load_owned_document(
    db: AsyncSession, deal_room_id: int, document_id: int, user: User
) -> Document:
    await load_owned_deal_room(db, deal_room_id, user)
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.deal_room_id == deal_room_id,
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


def _storage_path(user_id: int, deal_room_id: int, sha256: str, mime_type: str) -> Path:
    extension = _EXTENSION_BY_MIME.get(mime_type, ".bin")
    base = Path(settings.STORAGE_DIR) / str(user_id) / str(deal_room_id)
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{sha256}{extension}"


@router.post(
    "",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    deal_room_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    vector_store: VectorStore = Depends(vector_store_dep),
    embedder: EmbeddingClient = Depends(embedding_client_dep),
) -> Document:
    await load_owned_deal_room(db, deal_room_id, current_user)

    mime_type = (file.content_type or "").lower()
    if not is_supported(mime_type):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {mime_type or 'unknown'}. Allowed: "
            + ", ".join(sorted(ALLOWED_MIME_TYPES)),
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_UPLOAD_BYTES} byte limit",
        )

    sha256 = hashlib.sha256(data).hexdigest()
    path = _storage_path(current_user.id, deal_room_id, sha256, mime_type)
    path.write_bytes(data)

    document = Document(
        deal_room_id=deal_room_id,
        filename=file.filename or f"upload-{sha256[:8]}",
        mime_type=mime_type,
        size_bytes=len(data),
        sha256=sha256,
        storage_path=str(path),
        status=DocumentStatus.PENDING.value,
        chunk_count=0,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    try:
        document.status = DocumentStatus.PROCESSING.value
        await db.commit()
        await db.refresh(document)

        chunks = build_chunks(
            user_id=current_user.id,
            deal_room_id=deal_room_id,
            document_id=document.id,
            mime_type=mime_type,
            data=data,
            embedder=embedder,
        )
        vector_store.upsert_chunks(chunks)

        document.status = DocumentStatus.READY.value
        document.chunk_count = len(chunks)
        document.error_message = None
    except Exception as exc:
        # Any extraction, chunking, embedding, or vector-store failure is
        # recorded on the document row so the upload request still returns
        # 201 with an observable "failed" status instead of a 500.
        document.status = DocumentStatus.FAILED.value
        document.error_message = str(exc)[:500]
    await db.commit()
    await db.refresh(document)
    return document


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    deal_room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Document]:
    await load_owned_deal_room(db, deal_room_id, current_user)
    result = await db.execute(
        select(Document)
        .where(Document.deal_room_id == deal_room_id)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    deal_room_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    return await _load_owned_document(db, deal_room_id, document_id, current_user)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    deal_room_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    vector_store: VectorStore = Depends(vector_store_dep),
) -> Response:
    document = await _load_owned_document(db, deal_room_id, document_id, current_user)
    _cleanup_document_side_effects(document, vector_store)
    await db.delete(document)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _cleanup_document_side_effects(document: Document, vector_store: VectorStore) -> None:
    """Best-effort removal of a document's on-disk file and its Chroma chunks."""
    try:
        if document.storage_path and os.path.exists(document.storage_path):
            os.remove(document.storage_path)
    except OSError:
        pass
    try:
        vector_store.delete_document(document.id)
    except Exception:
        pass
