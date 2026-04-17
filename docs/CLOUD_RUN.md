# Cloud Run readiness reference

> **This document does not perform a real deploy.** It is a reference for
> what the current API image expects from Cloud Run and what shape a real
> deploy would take. Every `gcloud` snippet below uses placeholders and is
> provided as a copy-paste template only. Nothing in this repository runs
> `gcloud`, pushes images to Artifact Registry, provisions Cloud SQL, or
> talks to any Google Cloud project.

The goal of this page is to make it trivial to pick up the API image and
deploy it to Cloud Run *later*, without having to reverse-engineer
assumptions about ports, health probes, logging, or migrations.

---

## What Cloud Run expects from a container

Cloud Run has a small set of contract requirements that every image must
satisfy:

- **Listen on `$PORT`.** Cloud Run injects a `PORT` env var (conventionally
  `8080`) and routes external HTTPS traffic only to that port. Hard-coding
  a port makes a revision unhealthy at startup.
- **Stateless filesystem.** Every instance gets a fresh, ephemeral
  filesystem. Only `/tmp` is writable, and it is backed by instance RAM.
- **Multiple concurrent instances.** A single revision can fan out to many
  containers; there is no shared local disk between them.
- **SIGTERM on shutdown.** Cloud Run sends `SIGTERM`, waits up to 10s by
  default, then sends `SIGKILL`. The process should shut down cleanly.

## What this image already provides

As of Step 6 and Step 7 of the Person C work:

- **`$PORT` is honored** by the container entrypoint in `Dockerfile`. It
  falls back to `8000` when `PORT` is unset so local `docker run` and
  `docker compose up` still work as before.
- **`GET /livez`** is a dependency-free liveness probe that always returns
  `200 {"status":"ok"}` when the process can answer HTTP at all.
- **`GET /readyz`** is a readiness probe that checks Postgres
  (`SELECT 1`), Chroma (heartbeat), and `STORAGE_DIR` writability. It
  returns `200` only when all three are healthy and `503` with
  per-dependency booleans when any fail.
- **Structured request logs.** A FastAPI middleware emits one logfmt
  `INFO` record per request on the logger `api.request`, including
  `method`, `path`, `status`, `latency_ms`, `client_ip`, and `request_id`.
  No bodies, query strings, cookies, auth headers, or user identity are
  logged. Because Cloud Run forwards stdout to Cloud Logging
  automatically, no sidecar or SDK is required for these logs to be
  visible in Cloud Logging.
- **`X-Request-ID` header.** The middleware echoes any inbound
  `X-Request-ID` and generates one when missing. The same id appears in
  the corresponding log line, so a client-side error can be correlated
  back to a specific server log without external telemetry.
- **`SIGTERM` handling.** The container entrypoint uses `exec` so uvicorn
  runs as PID 1 and receives Cloud Run's shutdown signal directly.

## Environment variables expected on the service

Every variable the API reads is listed below with its expected shape on
Cloud Run. The authoritative default list lives in `.env.example`; this
table only annotates it with Cloud Run guidance.

| Variable                  | Purpose                                          | Cloud Run recommendation                                                      |
|---------------------------|--------------------------------------------------|-------------------------------------------------------------------------------|
| `JWT_SECRET`              | Signs session cookies                            | **Secret Manager.** Never set as plain env.                                   |
| `JWT_ALGORITHM`           | JWT signing algorithm                            | Leave at default `HS256` unless there is a reason to change.                  |
| `JWT_COOKIE_NAME`         | Session cookie name                              | Leave at default unless the frontend is on a different cookie domain.         |
| `JWT_EXPIRE_DAYS`         | Session lifetime                                 | Tune per product requirement.                                                 |
| `DATABASE_URL`            | Async SQLAlchemy URL for Postgres                | **Secret Manager.** Point at Cloud SQL (see below).                           |
| `FRONTEND_ORIGIN`         | CORS allowlist (single origin)                   | Set to the deployed frontend URL (e.g. a Vercel or Cloud Run domain).         |
| `STORAGE_DIR`             | Local directory for uploaded documents           | `/tmp/storage`. See the storage caveat under "Known readiness gaps".          |
| `MAX_UPLOAD_BYTES`        | Upload cap                                       | Leave at default unless product requirements change.                          |
| `EMBEDDING_MODEL`         | OpenAI embedding model                           | Leave at default `text-embedding-3-small`.                                    |
| `OPENAI_API_KEY`          | OpenAI credential                                | **Secret Manager.** `/ask` and `/analyze` return `503` when unset.            |
| `OPENAI_MODEL`            | Chat completion model                            | Leave at default.                                                             |
| `OPENAI_MAX_OUTPUT_TOKENS`| Cap on LLM output length                         | Leave at default.                                                             |
| `CHROMA_HOST`             | Hostname of the Chroma server                    | Set to the internal address of the Chroma deployment (see below).             |
| `CHROMA_PORT`             | Port of the Chroma server                        | Match `CHROMA_HOST`.                                                          |
| `CHROMA_COLLECTION`       | Name of the Chroma collection                    | Leave at default or namespace per environment (e.g. `deal_room_ai_prod`).     |
| `MLFLOW_TRACKING_URI`     | Optional MLflow tracking server                  | Leave blank unless MLflow is already wired separately.                        |
| `MLFLOW_EXPERIMENT_NAME`  | Optional MLflow experiment                       | Leave blank unless MLflow is already wired separately.                        |

There is no `PORT` row because Cloud Run sets it for you; do not set it
manually in the service config.

## Database (Postgres)

Cloud Run talks to Postgres via one of two shapes. Only the URL form
differs; everything else about the image stays the same.

**Cloud SQL for Postgres via Cloud SQL Auth Proxy (recommended).** Use a
Unix-socket style URL in `DATABASE_URL`:

```
postgresql+asyncpg://USER:PASS@/deal_room_ai?host=/cloudsql/PROJECT:REGION:INSTANCE
```

and attach the Cloud SQL instance to the service with
`--add-cloudsql-instances PROJECT:REGION:INSTANCE`.

**Cloud SQL for Postgres via direct TCP (simpler, fewer IAM steps).**
Use a TCP URL:

```
postgresql+asyncpg://USER:PASS@HOST:5432/deal_room_ai
```

and ensure Cloud Run has network access to `HOST` (Serverless VPC
Access connector or a public IP with authorized networks).

Neither option changes the image. Both go through Alembic migrations the
same way (see below).

## Chroma

Chroma is not a managed Google Cloud service. The two realistic options
for a Cloud Run deploy are:

1. **Run the open-source `chromadb/chroma` image as a second Cloud Run
   service.** Point `CHROMA_HOST` at its internal URL and `CHROMA_PORT`
   at its exposed port. Caveat: Cloud Run instances are ephemeral, so a
   cold-start will wipe the collection unless Chroma is configured with
   a durable backing store. This is **not production-ready** without
   additional work (for example, mounting GCS via Cloud Storage FUSE).
2. **Run Chroma on a small Compute Engine VM** with a persistent disk,
   and set `CHROMA_HOST`/`CHROMA_PORT` to its internal IP. Durable by
   default; trades off serverless scaling for persistence.

Either way, the API image does not change.

## Alembic migrations

The current `docker-compose.yml` runs `alembic upgrade head` as part of
the `api` container's `command:`. That works only because there is a
single `api` container locally. On Cloud Run, a revision typically scales
out to multiple concurrent instances, so running migrations in the main
container's entrypoint causes races and partial-upgrade states.

Recommended pattern for Cloud Run:

- Build the same image.
- Deploy a short-lived **Cloud Run Job** that invokes
  `alembic upgrade head` as its entrypoint.
- Run the job to completion *before* promoting a new revision of the
  main Cloud Run service.

This keeps the `api` service's CMD focused on serving traffic (the
Step-7 Dockerfile CMD does exactly that) and moves schema migrations out
of the request path.

## Liveness and readiness probes

Configure the Cloud Run service to probe the two endpoints we added in
Step 6. Example service-spec fragment (not applied in this repo, just the
shape of the YAML):

```yaml
livenessProbe:
  httpGet:
    path: /livez
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3

startupProbe:
  httpGet:
    path: /readyz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 5
  failureThreshold: 12
```

- **Liveness** points at `/livez` because `/livez` is intentionally
  dependency-free. A failing liveness probe should restart the container
  only when the process itself is stuck, not when Postgres is slow.
- **Startup/readiness** points at `/readyz` because `/readyz` reflects
  "can I actually serve requests?". Cloud Run will only route traffic to
  the revision once this passes.
- Numbers above are starting points; tune for the target environment.

## Logging and observability

The request-logging middleware added in Step 6 writes one line to stdout
per request, in a grep-friendly logfmt format, for example:

```
method=GET path=/readyz status=200 latency_ms=12.4 client_ip=10.8.0.3 request_id=ab12...cd34
```

Cloud Run streams stdout straight to Cloud Logging, so these lines are
searchable under the service's log scope with no extra setup. To
correlate a client-side error with a server log line, have the client
read the `X-Request-ID` response header and include it in its error
report — the same value appears in the server log's `request_id=` field.

No external telemetry, OpenTelemetry exporter, Cloud Trace client,
Cloud Monitoring custom metric, or third-party APM is wired up. The
request log is intentionally the only observability surface for now.

## Known readiness gaps

These are the gaps a real production Cloud Run deploy would need to
close. None of them are fixed by Step 7; they are documented here so
they are not surprises later:

1. **Ephemeral filesystem for uploads.** `STORAGE_DIR` is a local
   directory. Uploaded documents do not persist across Cloud Run
   revisions or instances. A real deploy needs Google Cloud Storage as
   the backing store for raw uploads, with a small adapter layer in the
   API. Until that exists, point `STORAGE_DIR` at `/tmp/storage` and
   treat uploads as disposable.
2. **Chroma persistence.** As noted above, neither Cloud Run option for
   Chroma is durable out of the box. A managed vector database or a
   GCE-hosted Chroma with a persistent disk is the eventual answer.
3. **Secrets.** This repo does not wire Secret Manager. The `gcloud`
   example below shows `--set-secrets` syntax so that the shape is
   obvious, but the secrets themselves are not provisioned here.
4. **CI/CD.** No `cloudbuild.yaml`, no GitHub Actions workflow, no image
   signing, no promotion pipeline exists in this repo yet.
5. **Defense-in-depth.** No rate limiting, WAF, Cloud Armor, or CDN is
   configured. CORS is set to a single `FRONTEND_ORIGIN`; everything
   else is rejected by the server.
6. **Alembic Job automation.** The migration pattern above is documented
   but not wired up as a Cloud Run Job or as an automation step.

## Copy-paste `gcloud` reference (not executed)

The commands below are **not** run by anything in this repository. They
show the shape of a minimal Cloud Run deploy using the current image;
real values (project id, region, Artifact Registry path, secret names,
Cloud SQL instance) are placeholders.

```bash
# Placeholders — fill in with real values before running manually.
export PROJECT_ID=your-gcp-project
export REGION=us-central1
export AR_REPO=deal-room-ai
export SERVICE=deal-room-ai-api
export IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/api:$(git rev-parse --short HEAD)"

# 1. Build the image and push it to Artifact Registry.
gcloud builds submit --tag "$IMAGE"

# 2. Deploy the API service. Wires env vars and secrets; Cloud Run sets
#    PORT for us, so we do not pass it here.
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "STORAGE_DIR=/tmp/storage,CHROMA_HOST=chroma-internal,CHROMA_PORT=8000,EMBEDDING_MODEL=text-embedding-3-small,FRONTEND_ORIGIN=https://your-frontend.example" \
  --set-secrets "JWT_SECRET=jwt-secret:latest,OPENAI_API_KEY=openai-api-key:latest,DATABASE_URL=database-url:latest" \
  --add-cloudsql-instances "$PROJECT_ID:$REGION:your-sql-instance"

# 3. Run Alembic migrations as a one-shot Cloud Run Job against the
#    same image. The job overrides the service's CMD with alembic.
gcloud run jobs create "$SERVICE-migrate" \
  --image "$IMAGE" \
  --region "$REGION" \
  --set-env-vars "STORAGE_DIR=/tmp/storage" \
  --set-secrets "DATABASE_URL=database-url:latest" \
  --command "alembic" \
  --args "upgrade,head"

gcloud run jobs execute "$SERVICE-migrate" --region "$REGION" --wait
```

Again: these are not executed from this repository. The purpose of this
document is purely to show a reader what "deploy this image to Cloud
Run" would look like in practice, without introducing any real cloud
integration.
