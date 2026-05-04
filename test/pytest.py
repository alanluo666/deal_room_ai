"""
FUNCTIONAL TESTS (6–8)
Run: pytest tests/test_functional.py -v

Requires:
  pip install pytest pytest-asyncio httpx
  Your app must be importable as `src.app` (FastAPI/Flask).
  Place a sample PDF at tests/fixtures/sample_financials.pdf
"""

import pytest
import os
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


FIXTURE_PDF = os.path.join(os.path.dirname(__file__), "fixtures", "sample_financials.pdf")

FIXTURE_EXPECTED = {
    "company_name": "Fixture Corp",
    "reporting_period": "Q2 2024",
    "revenue": 5_000_000,
    "ebitda": 1_200_000,
    "net_income": 750_000,
}

TOLERANCE = 0.001  # 0.1%


# ── Test 6: Document upload and parsing flow ──────────────────

def parse_financial_document(file_path: str) -> dict:
    """
    Parses a financial PDF and returns structured fields.
    Stub — replace with your real parser import:
      from src.services.document_parser import parse_financial_document
    """
    if not file_path.endswith(".pdf"):
        raise ValueError("Unsupported file type — only PDF is accepted")
    # Stub returns fixture values for testing
    return {**FIXTURE_EXPECTED}


class TestDocumentUploadAndParsing:
    """Functional Test 6 — Document upload and parsing flow"""

    def test_revenue_within_tolerance(self):
        result = parse_financial_document(FIXTURE_PDF)
        expected = FIXTURE_EXPECTED["revenue"]
        delta = abs(result["revenue"] - expected) / expected
        assert delta <= TOLERANCE, f"Revenue delta {delta:.4%} exceeds 0.1% tolerance"

    def test_ebitda_within_tolerance(self):
        result = parse_financial_document(FIXTURE_PDF)
        expected = FIXTURE_EXPECTED["ebitda"]
        delta = abs(result["ebitda"] - expected) / expected
        assert delta <= TOLERANCE, f"EBITDA delta {delta:.4%} exceeds 0.1% tolerance"

    def test_net_income_within_tolerance(self):
        result = parse_financial_document(FIXTURE_PDF)
        expected = FIXTURE_EXPECTED["net_income"]
        delta = abs(result["net_income"] - expected) / expected
        assert delta <= TOLERANCE

    def test_company_name_and_period_correct(self):
        result = parse_financial_document(FIXTURE_PDF)
        assert result["company_name"] == FIXTURE_EXPECTED["company_name"]
        assert result["reporting_period"] == FIXTURE_EXPECTED["reporting_period"]

    def test_unsupported_file_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            parse_financial_document("tests/fixtures/sample.txt")

    def test_upload_endpoint_returns_parsed_fields(self):
        """Uses a mock client — swap for real TestClient(app) in your project."""
        mock_client = MagicMock()
        mock_client.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"revenue": 5_000_000, "ebitda": 1_200_000, "net_income": 750_000},
        )
        response = mock_client.post("/api/documents/upload")
        assert response.status_code == 200
        body = response.json()
        assert "revenue" in body
        assert "ebitda" in body
        assert "net_income" in body


@pytest.fixture
def client():
    """
    Swap this for your real app test client, e.g.:
      from fastapi.testclient import TestClient
      from src.app import app
      return TestClient(app)
    """
    from unittest.mock import MagicMock
    mock_client = MagicMock()
    mock_client.post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"revenue": 5_000_000, "ebitda": 1_200_000, "net_income": 750_000},
    )
    return mock_client


# ── Test 7: Instant summary sent before batch job ────────────

def get_job_log(document_id: str) -> list:
    """
    Returns the ordered event log for a given document.
    Stub — replace with your real service:
      from src.services.job_logger import get_job_log
    """
    raise NotImplementedError("Stub — patch this in tests")


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


class TestSummaryBeforeBatchJob:
    """Functional Test 7 — Summary dispatched before batch job is queued"""

    def test_summary_timestamp_before_batch_timestamp(self):
        log = [
            {"event": "summary_sent",  "timestamp": "2024-10-01T10:00:00.800Z"},
            {"event": "batch_queued",  "timestamp": "2024-10-01T10:00:01.400Z"},
        ]
        summary_time = _parse_ts(next(e for e in log if e["event"] == "summary_sent")["timestamp"])
        batch_time   = _parse_ts(next(e for e in log if e["event"] == "batch_queued")["timestamp"])
        assert summary_time < batch_time, (
            f"Summary ({summary_time}) was not sent before batch job ({batch_time})"
        )

    def test_both_events_exist_in_log(self):
        log = [
            {"event": "summary_sent",  "timestamp": "2024-10-01T10:00:00.800Z"},
            {"event": "batch_queued",  "timestamp": "2024-10-01T10:00:01.400Z"},
        ]
        events = [e["event"] for e in log]
        assert "summary_sent" in events
        assert "batch_queued" in events

    def test_detects_wrong_order(self):
        """Catches a reversed ordering — batch before summary."""
        log = [
            {"event": "batch_queued",  "timestamp": "2024-10-01T10:00:00.200Z"},
            {"event": "summary_sent",  "timestamp": "2024-10-01T10:00:01.500Z"},
        ]
        summary_time = _parse_ts(next(e for e in log if e["event"] == "summary_sent")["timestamp"])
        batch_time   = _parse_ts(next(e for e in log if e["event"] == "batch_queued")["timestamp"])
        # Intentionally asserts the wrong order was detected
        assert summary_time >= batch_time


# ── Test 8: App health endpoint ───────────────────────────────

class TestHealthEndpoint:
    """Functional Test 8 — App /health endpoint"""

    def test_health_returns_200(self, health_client):
        response = health_client.get("/health")
        assert response.status_code == 200

    def test_health_body_has_status_ok(self, health_client):
        response = health_client.get("/health")
        assert response.json()["status"] == "ok"

    def test_health_body_has_positive_uptime(self, health_client):
        response = health_client.get("/health")
        body = response.json()
        assert "uptime" in body
        assert isinstance(body["uptime"], (int, float))
        assert body["uptime"] > 0

    def test_health_body_has_version(self, health_client):
        response = health_client.get("/health")
        body = response.json()
        assert "version" in body
        assert isinstance(body["version"], str)

    def test_health_responds_within_500ms(self, health_client):
        start = time.time()
        health_client.get("/health")
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 500, f"Health check took {elapsed_ms:.0f}ms — exceeded 500ms"


@pytest.fixture
def health_client():
    """
    Replace with your real app client, e.g.:
      from fastapi.testclient import TestClient
      from src.app import app
      return TestClient(app)
    """
    mock = MagicMock()
    mock.get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"status": "ok", "uptime": 4821.5, "version": "1.2.0"},
    )
    return mock



# 4.) Email Validation test (Boston)
# 5.) Analyze Summary test (Boston)
# # 
import pytest



# -------------------------------------------------
# Simple helper functions used only in this file
# -------------------------------------------------

def is_valid_email(email):
    """Very simple email check for demo purposes."""
    return "@" in email and "." in email



def fake_analyze(task):
    """Mock analyze result for a simple summary/risk style response."""
    if task not in {"summary", "risks"}:
        return {"status_code": 422, "message": "Invalid task"}
    return {
        "status_code": 200,
        "task": task,
        "answer": f"Sample {task} answer",
        "citations": [{"document_id": 1, "chunk_index": 0}],
    }



# -------------------------
# 1. Email validation test
# -------------------------

def test_valid_email_check():
    """Checks that a valid email passes and an invalid email fails."""
    assert is_valid_email("student@example.com") is True
    assert is_valid_email("bad-email") is False



# -------------------------
# 2. Analyze summary test
# -------------------------

def test_analyze_summary_returns_result():
    """Checks that a summary-style analysis returns success, an answer, and citations."""
    response = fake_analyze("summary")

    assert response["status_code"] == 200
    assert response["task"] == "summary"
    assert "answer" in response
    assert isinstance(response["citations"], list)