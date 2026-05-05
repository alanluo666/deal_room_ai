"""Guardrail: importing the live API must not transitively load cloud SDKs.

Default mode is offline/free. Cloud SDKs (Vertex AI, Gemini, the Google ADK
agent module, google-cloud-aiplatform, google-genai) are scaffolded only and
must not be loaded as a side effect of starting the FastAPI app or running
the test suite. This test fails loudly if a future import accidentally pulls
one of them into the API process.

The check is performed against ``sys.modules`` after ``api.main`` has been
imported (which happens transitively at collection time via
``tests/conftest.py``).
"""

from __future__ import annotations

import sys

import api.main  # noqa: F401 — assert the import has happened


FORBIDDEN_MODULES = (
    "google_adk",
    "vertexai",
    "google.cloud.aiplatform",
    "google.genai",
)


def test_api_startup_does_not_import_google_adk() -> None:
    assert "google_adk" not in sys.modules


def test_api_startup_does_not_import_vertexai() -> None:
    assert "vertexai" not in sys.modules


def test_api_startup_does_not_import_google_cloud_aiplatform() -> None:
    assert "google.cloud.aiplatform" not in sys.modules


def test_api_startup_does_not_import_google_genai() -> None:
    assert "google.genai" not in sys.modules


def test_forbidden_modules_list_kept_in_sync() -> None:
    """Sanity: the per-module tests above must cover every entry in FORBIDDEN_MODULES."""
    asserted = {
        "google_adk",
        "vertexai",
        "google.cloud.aiplatform",
        "google.genai",
    }
    assert asserted == set(FORBIDDEN_MODULES)
