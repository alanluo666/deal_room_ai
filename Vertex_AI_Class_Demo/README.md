# Vertex AI class demo (Deal Room AI repo)

This folder is a **temporary, minimal in-class exercise** for Google Cloud Vertex AI (KFP pipeline, model upload/deploy, online prediction, plus a tiny FastAPI stub). It is **not** production code and does not implement real Deal Room AI business logic.

## How this relates to the rest of the repo

| Location | Purpose |
|----------|---------|
| **`../api/`** | Main **Deal Room AI** FastAPI app: OpenAI-backed `/predict` for document summary / risks / QA, optional MLflow logging (`../README.md`). Runs on **port 8000** by default. |
| **`../Dockerfile`** | Builds the main API image (`uvicorn api.main:app`, port 8000). |
| **`../requirements.txt`** | Dependencies for the main app (FastAPI, OpenAI, MLflow, etc.). |
| **`./` (this folder)** | Isolated Vertex AI demo scripts and a **stub** FastAPI app on **port 8080** for Docker only. Uses **`./requirements.txt`** (Vertex + KFP stack). |

Do not confuse the stub `app.py` here with `../api/main.py`.

## Install (separate venv recommended)

From the **Deal Room AI** repository root (`deal_room_ai/`):

```bash
cd Vertex_AI_Class_Demo
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Edit `config.py` with your `PROJECT_ID`, `BUCKET_NAME`, and other placeholders before running cloud scripts. Use Application Default Credentials or a service account with Vertex AI access.

## Run the pipeline (compile + submit)

```bash
python pipeline.py
```

Writes `demo_pipeline.yaml` (gitignored) and runs a `PipelineJob` (requires valid GCP config and permissions).

## Deploy model + endpoint

```bash
python deploy_model.py
```

`MODEL_ARTIFACT_URI` must contain a model compatible with the chosen serving container (see `deploy_model.py` comments).

## Predict on a deployed endpoint

Set `ENDPOINT_RESOURCE_NAME` in `predict.py`, then:

```bash
python predict.py
```

## Docker (stub API only)

```bash
docker build -t deal-room-ai-vertex-class-demo .
docker run --rm -p 8080:8080 deal-room-ai-vertex-class-demo
```

- Stub health: `GET http://localhost:8080/`
- Stub echo: `POST http://localhost:8080/predict`

For the real document API, run from repo root: `uvicorn api.main:app --host 0.0.0.0 --port 8000` (see `../README.md`).
