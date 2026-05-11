"""Trimmed assignment-oriented automation tests.

These tests are designed to work with the existing fixtures in
``tests/conftest.py`` and current API contracts.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from httpx import AsyncClient

from api.service import openai_service


async def _register(client: AsyncClient, email: str, password: str = "password1") -> int:
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_predict_rejects_missing_document_text(client):
    # Why: request validation should reject malformed /predict payloads.
    await _register(client, "predict-missing@example.com")
    response = await client.post("/predict", json={"task": "summary"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_predict_summary_returns_result_with_stubbed_model(client, monkeypatch):
    # Why: verifies the /predict success contract without real OpenAI calls.
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
    # Why: checks that /predict exposes tracking status in response payload.
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


@pytest.mark.asyncio
async def test_predict_request_is_logged_once(client, caplog, monkeypatch):
    # Why: validates request-logging integration on /predict.
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

    matching = [
        r for r in caplog.records if r.name == "api.request" and "path=/predict" in r.message
    ]
    assert len(matching) == 1


def test_repository_has_no_openai_style_secret_literals():
    # Why: lightweight security guardrail for obvious hardcoded key patterns.
    repo_root = Path(__file__).resolve().parents[1]
    api_dir = repo_root / "api"
    key_pattern = re.compile(r"sk-[A-Za-z0-9]{20,}")

    for py_file in api_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        assert key_pattern.search(text) is None, f"Potential secret literal in {py_file}"
