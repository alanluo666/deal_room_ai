# Temporary in-class Vertex AI demo scaffold — local FastAPI stub (not connected to Vertex).
"""
Minimal FastAPI app for the class demo only.

The real Deal Room AI API lives at `../api/main.py` (OpenAI + MLflow, `/predict` for
document tasks). Run that with `uvicorn api.main:app --host 0.0.0.0 --port 8000` from
the `deal_room_ai` repo root. This file is a separate stub on port 8080 for Docker.
"""

from fastapi import Body, FastAPI

app = FastAPI(title="Deal Room AI — Vertex class demo (stub API)")


@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "deal-room-ai-vertex-class-demo-api",
        "note": "Stub only. Main app: uvicorn api.main:app --port 8000 from deal_room_ai root.",
    }


@app.post("/predict")
def predict_placeholder(payload: dict = Body(default_factory=dict)):
    return {
        "echo": payload,
        "note": (
            "Placeholder only — not wired to Vertex AI or the main Deal Room AI OpenAI "
            "service. Use predict.py for Vertex endpoints; use ../api for document AI."
        ),
    }
