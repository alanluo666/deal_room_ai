"""Request-id and latency logging middleware.

This module is intentionally small and dependency-free. It uses the standard
:mod:`logging` module and emits one structured line per request on the
``"api.request"`` logger. No request bodies, query strings, cookies, auth
headers, or user identity are logged. No external telemetry or cloud SDKs are
imported from this module.

The middleware:

* reads ``X-Request-ID`` from the inbound request, or generates a fresh hex id
  when it is missing,
* measures wall-clock latency with :func:`time.perf_counter`,
* echoes the request id on the outbound response via ``X-Request-ID``,
* logs a single ``INFO`` record with ``method``, ``path``, ``status``,
  ``latency_ms``, ``client_ip``, and ``request_id`` fields.

On unhandled exceptions, a single ``ERROR`` record with the same fields (plus
``error``) is emitted and the exception is re-raised so that FastAPI's usual
error handling still runs.
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_LOGGER_NAME = "api.request"

logger = logging.getLogger(REQUEST_LOGGER_NAME)


def _logfmt(fields: dict[str, object]) -> str:
    """Render ``fields`` as a grep-friendly ``key=value`` single line.

    Values are coerced to ``str``. Strings containing whitespace or ``"`` are
    wrapped in double quotes with embedded quotes escaped, so the line is
    still parseable by downstream tooling.
    """

    parts: list[str] = []
    for key, raw in fields.items():
        if raw is None:
            value = ""
        else:
            value = str(raw)
        needs_quote = any(ch.isspace() for ch in value) or '"' in value
        if needs_quote:
            escaped = value.replace('"', '\\"')
            parts.append(f'{key}="{escaped}"')
        else:
            parts.append(f"{key}={value}")
    return " ".join(parts)


def install_request_logging(app: FastAPI) -> None:
    """Register the request-id / latency logging middleware on ``app``.

    Safe to call once during app construction. It does not mutate the app's
    route table, does not touch any other middleware, and never raises from
    within the request path.
    """

    @app.middleware("http")
    async def _request_logging_middleware(
        request: Request, call_next
    ) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming if incoming else uuid.uuid4().hex

        client_ip = request.client.host if request.client else ""
        method = request.method
        path = request.url.path

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                _logfmt(
                    {
                        "method": method,
                        "path": path,
                        "status": 500,
                        "latency_ms": latency_ms,
                        "client_ip": client_ip,
                        "request_id": request_id,
                        "error": type(exc).__name__,
                    }
                )
            )
            raise

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            _logfmt(
                {
                    "method": method,
                    "path": path,
                    "status": response.status_code,
                    "latency_ms": latency_ms,
                    "client_ip": client_ip,
                    "request_id": request_id,
                }
            )
        )
        return response
