## Deal Room AI

Document Review Workspace for Smaller Deal Teams — a collaborative SaaS platform for search funds, independent sponsors, boutique M&A advisors, and small corp dev teams. The platform focuses on the document-heavy part of due diligence by bringing filings, contracts, and management transcripts into one workspace, powered by AI-driven analysis.

M1 of the product slice ships multi-user accounts (JWT in an HTTP-only cookie), persistent deal rooms in Postgres, and a Next.js 15 workspace shell. Document upload, retrieval, and AI summarization land in later milestones.

## Prerequisites

- Python 3.12+ (only needed if you run the API outside Docker)
- Node.js 20+ and npm (for the frontend)
- Docker and Docker Compose (recommended for local development)
- OpenAI API key (required only for the legacy `POST /predict` endpoint)

## Local Development Quickstart

### 1. Environment variables

```bash
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

Generate a secret for JWT signing and paste it into `.env` as `JWT_SECRET`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

`.env.example` ships with `MLFLOW_TRACKING_URI=` and `MLFLOW_EXPERIMENT_NAME=` intentionally blank. Leave them blank for local development — MLflow is fully disabled in that state and the API will not attempt any remote connections.

### 2. Start the backend (API + Postgres)

```bash
docker compose up -d
```

The first run will build the API image, start Postgres, apply Alembic migrations, and expose the API at `http://localhost:8000`. Confirm it is healthy:

```bash
curl -s localhost:8000/health | python -m json.tool
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The workspace is available at `http://localhost:3000`.

### 4. Run the backend tests

```bash
docker compose exec api pytest
```

All auth and deal-room tests run against an in-process SQLite database with LLM and embedding calls fully mocked — no network calls leave the process.

## Running the API Outside Docker

You still need Postgres reachable at the URL in `DATABASE_URL`. The easiest option is to run only the Postgres service from Compose:

```bash
docker compose up -d postgres
pip install -r requirements.txt
alembic upgrade head
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

All new endpoints accept and set an HTTP-only session cookie named `deal_room_ai_session`. The frontend sends the cookie automatically with `credentials: "include"`. If you hit these endpoints with `curl`, use `-c cookies.txt` and `-b cookies.txt` to persist the session between calls.

### Auth

| Method | Path             | Description                                                  |
|--------|------------------|--------------------------------------------------------------|
| POST   | `/auth/register` | Create a user, set session cookie, return the user           |
| POST   | `/auth/login`    | Verify credentials, set session cookie, return the user      |
| POST   | `/auth/logout`   | Clear the session cookie                                     |
| GET    | `/auth/me`       | Return the current user; requires a valid session cookie     |

```bash
curl -s -c cookies.txt -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "a-strong-password"}'

curl -s -b cookies.txt http://localhost:8000/auth/me
```

### Deal rooms

All deal-room endpoints require a session cookie and are automatically scoped to the owning user. Cross-user access returns `404`.

| Method | Path                     | Description                             |
|--------|--------------------------|-----------------------------------------|
| GET    | `/deal-rooms`            | List deal rooms owned by the caller     |
| POST   | `/deal-rooms`            | Create a deal room                      |
| GET    | `/deal-rooms/{id}`       | Fetch one deal room                     |
| DELETE | `/deal-rooms/{id}`       | Hard delete a deal room (cascades when children land in M2) |

```bash
curl -s -b cookies.txt -X POST http://localhost:8000/deal-rooms \
  -H "Content-Type: application/json" \
  -d '{"name": "Project Acme", "target_company": "Acme Corp"}'

curl -s -b cookies.txt http://localhost:8000/deal-rooms
```

### Platform

#### `GET /` — Root

```bash
curl http://localhost:8000/
```

```json
{ "message": "Deal Room AI API is running" }
```

#### `GET /health`

```bash
curl -s http://localhost:8000/health | python -m json.tool
```

```json
{
  "status": "ok",
  "openai_configured": true,
  "openai_model": "gpt-5-mini",
  "mlflow_tracking_enabled": false,
  "mlflow_tracking_uri": "",
  "mlflow_experiment_name": "",
  "db_ok": true
}
```

The five `openai_*` and `mlflow_*` fields are the same as before; `db_ok` is new in M1 and reports the result of a trivial `SELECT 1` against Postgres.

#### `POST /predict` — Legacy demo endpoint

> This single-shot demo endpoint is kept working for backward compatibility but is considered deprecated after the M1 slice. Future AI functionality will live behind deal-room-scoped endpoints that run retrieval over uploaded documents rather than free-form text pasted into the body.

```bash
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"task": "summary", "document_text": "Acme Corp reported $5M revenue in Q1 2026..."}'
```

## MLflow Tracking (opt-in only)

MLflow is fully disabled by default. Leaving `MLFLOW_TRACKING_URI` blank (as in `.env.example`) means:

- No connections are attempted to any tracking server.
- No runs, params, metrics, or artifacts are logged anywhere.
- `/health` reports `"mlflow_tracking_enabled": false`.

To opt in later, set `MLFLOW_TRACKING_URI` to your own tracking server URL and optionally set `MLFLOW_EXPERIMENT_NAME`. There is no default remote URI in the code, the Docker Compose file, the backend settings, or this README — configuration is always explicit.

## Project Structure

```
deal_room_ai/
├── api/
│   ├── __init__.py
│   ├── auth.py             # bcrypt hashing + JWT cookie helpers
│   ├── config.py           # pydantic-settings Settings (DB, JWT, CORS)
│   ├── db.py               # SQLAlchemy async engine + session + Base
│   ├── deps.py             # get_current_user, get_db dependencies
│   ├── main.py             # FastAPI app, routers, CORS, /health, /predict
│   ├── models/             # User, DealRoom ORM models
│   ├── routers/            # auth + deal-rooms HTTP routers
│   ├── schemas.py          # Pydantic request/response models
│   ├── service.py          # Legacy OpenAI service for /predict
│   └── tracking.py         # MLflow tracking manager (off unless opted in)
├── alembic/                # Alembic environment + initial migration
├── alembic.ini
├── frontend/               # Next.js 15 + TypeScript + Tailwind workspace
│   ├── app/
│   │   ├── (auth)/login    # /login page
│   │   ├── (auth)/register # /register page
│   │   └── deal-rooms      # /deal-rooms workspace
│   ├── components/
│   ├── lib/                # api.ts, auth.ts, types.ts
│   └── middleware.ts       # Route protection for /deal-rooms/*
├── tests/                  # pytest suite for auth + deal-room scoping
├── docker-compose.yml      # api + postgres services (no MLflow service)
├── Dockerfile
├── MLFlow_Server_SetUp.ipynb
├── pyproject.toml
├── requirements.txt
└── .env.example
```

## Milestone status

- **M1 (this slice):** multi-user auth, per-user deal rooms, Next.js shell, pytest suite.
- **M2 (planned):** document upload per deal room, text extraction, chunking, embedding into ChromaDB, MLflow opt-in for embedding runs.
- **M3 (planned):** retrieval-augmented summaries, risks, and Q&A scoped to each deal room.
- **M4 (planned):** task tracker and management dashboard.
