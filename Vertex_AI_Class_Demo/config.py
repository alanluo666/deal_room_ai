# Temporary in-class Vertex AI demo scaffold — placeholder config only (not production).
"""
Shared placeholder settings for the class demo.

This repo’s main application (`../api/`) uses FastAPI + OpenAI + MLflow and runs on
port 8000 (see repo root README). These settings are only for the isolated Vertex AI
exercise and do not affect the production-style API code.
"""

PROJECT_ID = "your-project-id"
REGION = "us-central1"
BUCKET_NAME = "your-bucket-name"
PIPELINE_ROOT = f"gs://{BUCKET_NAME}/pipeline-root"
MODEL_ARTIFACT_URI = f"gs://{BUCKET_NAME}/models/demo-model"
MODEL_DISPLAY_NAME = "deal-room-ai-vertex-class-demo-model"
ENDPOINT_DISPLAY_NAME = "deal-room-ai-vertex-class-demo-endpoint"
PIPELINE_DISPLAY_NAME = "deal-room-ai-vertex-class-demo-run"
PIPELINE_TEMPLATE_PATH = "demo_pipeline.yaml"
