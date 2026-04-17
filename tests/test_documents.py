import os

import pytest
from httpx import AsyncClient


PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
TXT_MIME = "text/plain"


async def _register(client: AsyncClient, email: str, password: str = "password1") -> int:
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_room(client: AsyncClient, name: str = "Room") -> int:
    response = await client.post("/deal-rooms", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


async def _upload_txt(
    client: AsyncClient,
    deal_room_id: int,
    *,
    filename: str = "notes.txt",
    content: bytes = b"hello world. this is a small test document.",
    mime: str = TXT_MIME,
):
    return await client.post(
        f"/deal-rooms/{deal_room_id}/documents",
        files={"file": (filename, content, mime)},
    )


@pytest.mark.asyncio
async def test_upload_requires_auth(client):
    response = await client.post(
        "/deal-rooms/1/documents",
        files={"file": ("x.txt", b"hi", TXT_MIME)},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_txt_happy_path(client, fake_vector_store, fake_embedding_client):
    await _register(client, "up@example.com")
    room_id = await _create_room(client)

    response = await _upload_txt(client, room_id)
    assert response.status_code == 201
    body = response.json()
    assert body["deal_room_id"] == room_id
    assert body["mime_type"] == TXT_MIME
    assert body["status"] == "ready"
    assert body["chunk_count"] >= 1
    assert body["error_message"] is None
    assert body["size_bytes"] > 0

    assert len(fake_embedding_client.calls) == 1
    assert sum(1 for _ in fake_vector_store.upserts) == body["chunk_count"]
    for chunk in fake_vector_store.upserts:
        assert chunk.deal_room_id == room_id
        assert chunk.document_id == body["id"]


@pytest.mark.asyncio
async def test_list_documents_scoped_to_room(client):
    await _register(client, "list@example.com")
    room_id = await _create_room(client, "A")
    other_room_id = await _create_room(client, "B")

    up = await _upload_txt(client, room_id, filename="a.txt")
    assert up.status_code == 201

    listing = await client.get(f"/deal-rooms/{room_id}/documents")
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    other = await client.get(f"/deal-rooms/{other_room_id}/documents")
    assert other.status_code == 200
    assert other.json() == []


@pytest.mark.asyncio
async def test_get_document(client):
    await _register(client, "g@example.com")
    room_id = await _create_room(client)
    up = await _upload_txt(client, room_id)
    doc_id = up.json()["id"]

    response = await client.get(f"/deal-rooms/{room_id}/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["id"] == doc_id


@pytest.mark.asyncio
async def test_upload_unsupported_mime(client):
    await _register(client, "bad@example.com")
    room_id = await _create_room(client)
    response = await client.post(
        f"/deal-rooms/{room_id}/documents",
        files={"file": ("x.bin", b"\x00\x01\x02", "application/octet-stream")},
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_upload_empty_file(client):
    await _register(client, "empty@example.com")
    room_id = await _create_room(client)
    response = await _upload_txt(client, room_id, content=b"")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_too_large(client, monkeypatch):
    from api.config import settings

    monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 16)

    await _register(client, "big@example.com")
    room_id = await _create_room(client)
    response = await _upload_txt(client, room_id, content=b"x" * 1024)
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_extraction_failure_sets_failed_status(
    client, fake_embedding_client, monkeypatch
):
    def _boom(*args, **kwargs):
        raise RuntimeError("embed exploded")

    monkeypatch.setattr(fake_embedding_client, "embed", _boom)

    await _register(client, "fail@example.com")
    room_id = await _create_room(client)
    response = await _upload_txt(client, room_id)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "failed"
    assert body["error_message"] and "embed exploded" in body["error_message"]
    assert body["chunk_count"] == 0


@pytest.mark.asyncio
async def test_cross_user_cannot_see_documents(make_client):
    async with make_client() as client_a:
        await _register(client_a, "a@example.com")
        room_id = await _create_room(client_a)
        up = await _upload_txt(client_a, room_id)
        doc_id = up.json()["id"]

    async with make_client() as client_b:
        await _register(client_b, "b@example.com")

        forbidden_list = await client_b.get(f"/deal-rooms/{room_id}/documents")
        assert forbidden_list.status_code == 404

        forbidden_get = await client_b.get(
            f"/deal-rooms/{room_id}/documents/{doc_id}"
        )
        assert forbidden_get.status_code == 404

        forbidden_upload = await _upload_txt(client_b, room_id)
        assert forbidden_upload.status_code == 404

        forbidden_delete = await client_b.delete(
            f"/deal-rooms/{room_id}/documents/{doc_id}"
        )
        assert forbidden_delete.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_removes_side_effects(
    client, fake_vector_store
):
    await _register(client, "del@example.com")
    room_id = await _create_room(client)
    up = await _upload_txt(client, room_id)
    doc_id = up.json()["id"]

    listing = await client.get(f"/deal-rooms/{room_id}/documents")
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    assert fake_vector_store.count_for_document(doc_id) > 0

    response = await client.delete(f"/deal-rooms/{room_id}/documents/{doc_id}")
    assert response.status_code == 204

    assert doc_id in fake_vector_store.deleted_document_ids
    assert fake_vector_store.count_for_document(doc_id) == 0

    gone = await client.get(f"/deal-rooms/{room_id}/documents/{doc_id}")
    assert gone.status_code == 404


@pytest.mark.asyncio
async def test_deal_room_delete_cascades_documents(
    client, fake_vector_store
):
    await _register(client, "cascade@example.com")
    room_id = await _create_room(client)

    up1 = await _upload_txt(client, room_id, filename="a.txt")
    up2 = await _upload_txt(client, room_id, filename="b.txt")
    doc_ids = [up1.json()["id"], up2.json()["id"]]

    for doc_id in doc_ids:
        get = await client.get(f"/deal-rooms/{room_id}/documents/{doc_id}")
        assert get.status_code == 200

    response = await client.delete(f"/deal-rooms/{room_id}")
    assert response.status_code == 204

    for doc_id in doc_ids:
        assert doc_id in fake_vector_store.deleted_document_ids

    gone_room = await client.get(f"/deal-rooms/{room_id}")
    assert gone_room.status_code == 404

    gone_list = await client.get(f"/deal-rooms/{room_id}/documents")
    assert gone_list.status_code == 404


@pytest.mark.asyncio
async def test_upload_persists_file_to_disk(client):
    import hashlib

    from api.config import settings

    user_id = await _register(client, "disk@example.com")
    room_id = await _create_room(client)
    payload = b"persist me"
    response = await _upload_txt(client, room_id, content=payload)
    assert response.status_code == 201

    # The shared STORAGE_DIR and a fresh-per-test DB (user_id=1, room_id=1)
    # mean sibling test runs can leave unrelated files under the same parent
    # directory, so we pinpoint the expected file by its sha256.
    expected_sha = hashlib.sha256(payload).hexdigest()
    expected_path = os.path.join(
        settings.STORAGE_DIR, str(user_id), str(room_id), f"{expected_sha}.txt"
    )
    assert os.path.isfile(expected_path)
    with open(expected_path, "rb") as fh:
        assert fh.read() == payload


@pytest.mark.asyncio
async def test_health_includes_storage_and_chroma(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "storage_ok" in body
    assert "chroma_ok" in body
    assert body["chroma_ok"] is True
