"""Additional automation tests intended to be moved under ``tests/``.

This file is intentionally written to be compatible with the existing
fixtures from ``tests/conftest.py`` (``client``, ``override_rag``).
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import pytest
from httpx import AsyncClient

from api.main import app
from api.service import openai_service

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
    content: bytes = b"Acme Corp reported $5M revenue in Q1 2026.",
):
    return await client.post(
        f"/deal-rooms/{deal_room_id}/documents",
        files={"file": (filename, content, TXT_MIME)},
    )


@pytest.mark.asyncio
async def test_health_endpoint_returns_200_with_status_ok(client):
    # Why: baseline availability check for the API service.
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_predict_rejects_missing_document_text(client):
    # Why: validates request schema enforcement for required payload fields.
    await _register(client, "predict-missing@example.com")
    response = await client.post("/predict", json={"task": "summary"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_predict_summary_returns_result_with_stubbed_model(client, monkeypatch):
    # Why: verifies the end-to-end /predict success contract without real OpenAI.
    await _register(client, "predict-ok@example.com")
    monkeypatch.setattr(openai_service, "client", object())
    monkeypatch.setattr(openai_service, "model", "stub-model")
    monkeypatch.setattr(openai_service, "run_prediction", lambda _request: "Synthetic summary")
    response = await client.post(
        "/predict",
        json={
            "task": "summary",
            "document_text": "Acme Corp reported $5M revenue in Q1 2026, up 20% YoY.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["result"] == "Synthetic summary"
    assert body["model"] == "stub-model"


@pytest.mark.asyncio
async def test_predict_call_sets_mlflow_tracking_flag_in_response(client, monkeypatch):
    # Why: checks the response shape used to expose tracking-state to callers.
    await _register(client, "predict-track@example.com")
    monkeypatch.setattr(openai_service, "client", object())
    monkeypatch.setattr(openai_service, "model", "stub-model")
    monkeypatch.setattr(openai_service, "run_prediction", lambda _request: "ok")
    monkeypatch.setattr("api.main.tracking_manager.enabled", True)
    response = await client.post(
        "/predict",
        json={"task": "risks", "document_text": "Top customers account for 70% of revenue."},
    )
    assert response.status_code == 200
    assert response.json()["mlflow_tracking_enabled"] is True


def test_repository_has_no_openai_style_secret_literals():
    # Why: lightweight security check to catch accidentally committed API-like keys.
    repo_root = Path(__file__).resolve().parents[1]
    api_dir = repo_root / "api"
    key_pattern = re.compile(r"sk-[A-Za-z0-9]{20,}")
    for py_file in api_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        assert key_pattern.search(text) is None, f"Potential secret literal in {py_file}"


@pytest.mark.asyncio
async def test_document_upload_and_parsing_flow_returns_ready_document(
    client, fake_vector_store, fake_embedding_client
):
    # Why: covers upload->extract->chunk->embed->store path using current API contracts.
    await _register(client, "upload-flow@example.com")
    room_id = await _create_room(client)
    response = await _upload_txt(client, room_id)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ready"
    assert body["chunk_count"] >= 1
    assert body["error_message"] is None
    assert len(fake_embedding_client.calls) == 1
    assert fake_vector_store.count_for_document(body["id"]) >= 1


@pytest.mark.asyncio
async def test_document_upload_rejects_unsupported_file_type(client):
    # Why: ensures invalid MIME types are rejected before parsing logic runs.
    await _register(client, "upload-mime@example.com")
    room_id = await _create_room(client)
    response = await client.post(
        f"/deal-rooms/{room_id}/documents",
        files={"file": ("blob.bin", b"\x00\x01", "application/octet-stream")},
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_analyze_summary_returns_result(client, override_rag):
    # Why: validates task-preset behavior for summary responses and citations.
    await _register(client, "analyze-summary@example.com")
    room_id = await _create_room(client)
    up = await _upload_txt(client, room_id)
    assert up.status_code == 201
    response = await client.post(
        f"/deal-rooms/{room_id}/analyze",
        json={"task": "summary"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["task"] == "summary"
    assert body["answer"]
    assert isinstance(body["citations"], list)


@pytest.mark.asyncio
async def test_predict_response_time_under_ten_seconds_with_stubbed_model(client, monkeypatch):
    # Why: adds a basic latency guardrail for the synchronous /predict path.
    await _register(client, "predict-latency@example.com")
    monkeypatch.setattr(openai_service, "client", object())
    monkeypatch.setattr(openai_service, "model", "stub-model")
    monkeypatch.setattr(openai_service, "run_prediction", lambda _request: "fast result")
    start = time.time()
    response = await client.post(
        "/predict",
        json={"task": "summary", "document_text": "Short test document."},
    )
    elapsed = time.time() - start
    assert response.status_code == 200
    assert elapsed < 10


@pytest.mark.asyncio
async def test_summary_event_is_logged_before_predict_batch_completion(client, caplog, monkeypatch):
    # Why: operational ordering check adapted to request-logging middleware behavior.
    await _register(client, "request-order@example.com")
    monkeypatch.setattr(openai_service, "client", object())
    monkeypatch.setattr(openai_service, "model", "stub-model")
    monkeypatch.setattr(openai_service, "run_prediction", lambda _request: "ordered result")
    caplog.set_level("INFO", logger="api.request")
    response = await client.post(
        "/predict",
        json={"task": "summary", "document_text": "ordering check"},
    )
    assert response.status_code == 200
    matching = [r for r in caplog.records if r.name == "api.request" and "path=/predict" in r.message]
    assert len(matching) == 1


def test_app_exposes_expected_routes_for_health_and_predict():
    # Why: cheap integration smoke test that routing table includes expected endpoints.
    route_paths = {route.path for route in app.routes}
    assert "/health" in route_paths
    assert "/predict" in route_paths