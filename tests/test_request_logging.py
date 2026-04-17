"""Tests for the request-id / latency logging middleware.

These tests confirm that the middleware:

* echoes an inbound ``X-Request-ID`` header back on the response,
* generates a fresh ``X-Request-ID`` when the caller did not supply one,
* emits exactly one ``INFO`` record per request on the ``"api.request"``
  logger, with a structured key/value line containing the expected fields.

No request bodies, query strings, cookies, or auth headers are inspected,
because the middleware does not log them.
"""

from __future__ import annotations

import logging


async def test_request_id_header_is_echoed_when_provided(client):
    response = await client.get("/livez", headers={"X-Request-ID": "req-abc-123"})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "req-abc-123"


async def test_request_id_is_generated_when_missing(client):
    response = await client.get("/livez")
    assert response.status_code == 200
    generated = response.headers.get("X-Request-ID")
    assert generated is not None
    assert len(generated) >= 16
    assert generated != ""


async def test_request_is_logged_at_info_level(client, caplog):
    caplog.set_level(logging.INFO, logger="api.request")

    response = await client.get("/livez", headers={"X-Request-ID": "log-test-id"})
    assert response.status_code == 200

    matching = [r for r in caplog.records if r.name == "api.request"]
    assert len(matching) == 1

    record = matching[0]
    assert record.levelno == logging.INFO

    message = record.getMessage()
    assert "method=GET" in message
    assert "path=/livez" in message
    assert "status=200" in message
    assert "latency_ms=" in message
    assert "request_id=log-test-id" in message
