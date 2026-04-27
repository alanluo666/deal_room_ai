# ML Pipeline & Infra (Chris)

This file documents the ML-pipeline portion of Deal Room AI: document-type
classifier, offline batch ingestion, Vertex AI deployment, and CI/CD. Kept
as a separate doc so it doesn't collide with the unresolved merge conflicts
in `README.md`. Fold into `README.md` once those are resolved.

## Folder map

```
classifier/        # TF-IDF + LogReg doc-type classifier (training + inference)
deploy/            # Vertex AI custom-container deployment for the classifier
ingestion/         # Offline batch ingestion orchestrator (reuses Boston's modules)
.github/workflows/ # ML pipeline CI + deploy-on-merge
requirements-ml.txt
deploy/requirements-vertex.txt
```

## How my work connects to the rest of the system

```
                +-------------------+
upload UI ----> | api/main.py       |  <-- Boston: synchronous ingestion path
                | document_processing|     (PDF/DOCX/TXT -> chunks -> embeddings -> Chroma)
                | vector_store       |
                +---------+----------+
                          |
                  writes to ChromaDB
                          |
batch CLI ----> ingestion/pipeline.py  <-- ME: offline batch path
                  reuses Boston's modules,
                  adds doc_type via classifier
                          |
                  writes to ChromaDB (same collection)
                          |
                          v
                +-------------------+
                | ChromaDB          |  <-- shared store
                +---------+---------+
                          |
                  query at runtime
                          |
                +---------v---------+
                | api/rag.py        |  <-- Boston: retrieval
                | -> GPT-5.x        |  <-- OpenAI: answer generation
                | (Alan's RAG agent |      reads same Chroma collection)
                +-------------------+
```

## ChromaDB schema (single source of truth: `api/vector_store.py`)

Boston's `ChromaVectorStore.upsert_chunks` writes:

| Field | Type | Source |
|---|---|---|
| `id` | str | `f"doc:{document_id}:chunk:{chunk_index}"` (deterministic) |
| `document_id` | int | document row in Postgres |
| `deal_room_id` | int | deal-room row in Postgres |
| `user_id` | int | uploader |
| `chunk_index` | int | position in document |

**My addition (needs Boston's sign-off):** `doc_type: str` (one of
`classifier.labels.DOC_TYPES`). Until Boston extends his `Chunk` dataclass
to carry it, the offline pipeline writes `doc_type` via a follow-up upsert
in `ingestion/pipeline.py::_attach_doc_type`. After Boston extends the
schema, that workaround can be deleted.

## Component details

### `classifier/`
TF-IDF (1-2 grams) + multinomial Logistic Regression in a sklearn Pipeline.
- `model.py` — pipeline definition
- `train.py` — train + log to MLflow (uses MLFLOW_TRACKING_URI from `.env`)
- `evaluate.py` — accuracy / macro-F1 / precision / recall
- `predict.py` — module-cached inference helper
- `labels.py` — public label vocabulary (the API contract Boston references)
- `data.py` — CSV loader + synthetic generator for smoke tests

Train (smoke):
```bash
python -m classifier.train --synthetic --out ./classifier_model.joblib
```
Train (real):
```bash
python -m classifier.train --data ./data/labels.csv --out ./classifier_model.joblib
```

### `deploy/`
Custom-container deploy of the trained classifier to Vertex AI.
- `predictor.py` — FastAPI predictor with `/predict` + `/health` (Vertex contract)
- `Dockerfile.classifier` — slim image, baked-in joblib model
- `vertex_deploy.py` — uploads to Model Registry + creates/updates endpoint
- `config.yaml` — region/repo/machine config (env-var expandable)

Local test of the predictor:
```bash
docker build -f deploy/Dockerfile.classifier -t deal-room-classifier .
docker run --rm -p 8080:8080 deal-room-classifier
curl -s localhost:8080/predict -H 'Content-Type: application/json' \
  -d '{"instances":[{"text":"Revenue Q3 2025 grew 18% YoY ..."}]}'
```

> Note: `Vertex_AI_Class_Demo/` (on the `Vertex_AI` branch) is Alan's class
> exercise with a placeholder model — keep or discard once `deploy/` is in
> place.

### `ingestion/pipeline.py`
Thin orchestrator for **offline batch** ingestion (bulk historical loads,
re-embedding runs, doc_type backfills). Reuses Boston's
`api.document_processing` + `api.vector_store` so chunking/embedding/storage
logic lives in exactly one place.

```bash
python -m ingestion.pipeline \
  --source ./data/raw \
  --deal-room-id 1 --user-id 1 --document-id 100
```

### CI/CD (`.github/workflows/`)
- `ml-ci.yml` — on PRs touching `classifier/`, `ingestion/`, or `deploy/`:
  ruff lint, smoke-train on synthetic data, pytest.
- `deploy-classifier.yml` — on merge to `main` touching the same paths:
  train → build container → push to Artifact Registry → deploy to Vertex
  endpoint. Auths via Workload Identity Federation.

Required GitHub secrets/vars:
- `vars.GCP_PROJECT_ID`
- `secrets.GCP_WIF_PROVIDER`
- `secrets.GCP_DEPLOY_SA`
- `secrets.OPENAI_API_KEY`
- `secrets.MLFLOW_TRACKING_URI`

## Open alignment items

**With Boston (RAG / API):**
- Add `doc_type: str` to `Chunk` and thread through `ChromaVectorStore.upsert_chunks` so the offline pipeline can stop using the `_attach_doc_type` workaround.
- Embedding model: his `api/config.py` ships `text-embedding-3-small`; the assignment spec calls for `text-embedding-3-large`. Pick one — they're not interchangeable (1536 vs. 3072 native dims) and switching means re-embedding everything.
- Where the classifier runs in the online flow: invoke `classifier.predict.predict_doc_type` inside `document_processing.build_chunks` so doc_type is set on synchronous uploads too.

**With Alan (RAG agent / Vertex demo):**
- `Vertex_AI_Class_Demo/` — keep as demo or delete now that `deploy/` is the production path?
- ChromaDB collection name: he reads from whatever `api.config.settings.CHROMA_COLLECTION` is set to (default `deal_room_ai_chunks`).

## Known repo state issues to fix separately

`README.md`, `requirements.txt`, `.env.example`, and `.gitignore` on `main`
contain unresolved git merge conflict markers (`<<<<<<<` / `>>>>>>>`).
Resolve those before the next merge to keep things stable; this scaffold
does not touch them.
