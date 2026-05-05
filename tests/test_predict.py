"""Tests for ``POST /predict`` (legacy, now auth-gated and sanitised).

Coverage:
  * 401 when called without a session cookie
  * 503 + stable message when OpenAI is not configured server-side
    (the offline-by-default state under ENABLE_LLM_CALLS=false)
  * 500 + sanitised body when an arbitrary internal exception fires;
    raw exception text and a sentinel internal token must NOT appear
    in the response or its detail

No network, no real OpenAI, no real MLflow. ``openai_service`` is
monkeypatched in-process when we want to force the failure path.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_predict_unauthenticated_returns_401(client):
    response = await client.post(
        "/predict", json={"task": "summary", "document_text": "Hello"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_predict_authenticated_with_openai_disabled_returns_503(client):
    await client.post(
        "/auth/register",
        json={"email": "predict-503@example.com", "password": "password1"},
    )
    response = await client.post(
        "/predict", json={"task": "summary", "document_text": "Hello"}
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "OpenAI is not configured on the server"


@pytest.mark.asyncio
async def test_predict_authenticated_generic_500_is_sanitised(client, monkeypatch):
    from api.service import openai_service

    sentinel = "FAKE-INTERNAL-TOKEN-SHOULD-NOT-LEAK"

    # Force is_ready() True so the OpenAINotConfiguredError branch is skipped
    # and the generic-exception branch is exercised instead.
    monkeypatch.setattr(openai_service, "client", object())

    def _raise(_request):
        raise RuntimeError(sentinel)

    monkeypatch.setattr(openai_service, "run_prediction", _raise)

    await client.post(
        "/auth/register",
        json={"email": "predict-500@example.com", "password": "password1"},
    )
    response = await client.post(
        "/predict", json={"task": "summary", "document_text": "Hello"}
    )
    assert response.status_code == 500
    assert sentinel not in response.text
    assert response.json()["detail"] == "Prediction failed. Please try again."
