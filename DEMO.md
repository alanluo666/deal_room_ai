# Deal Room AI — 10-minute local demo

A walkthrough that takes a fresh clone to a working, end-to-end demo on
your laptop in about ten minutes. Everything stays local: Postgres and
Chroma run in Docker, the Next.js frontend runs on your host, and no
OpenAI credits are required unless you explicitly opt in.

## 0. Prerequisites

- Docker Desktop 4.30+ (or Docker Engine 24+ with Compose v2)
- Node.js 20+ and `npm`
- ~2 GB of free disk space for images and local volumes

## 1. Clone and configure

```bash
git clone <your-fork-url>
cd deal_room_ai

cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

Generate a signing secret and write it into `.env`:

```bash
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))" >> .env
```

Leave `OPENAI_API_KEY=` blank for a stub-LLM demo.
Leave `MLFLOW_TRACKING_URI=` blank — MLflow is fully off by default and
no remote connections are attempted.

## 2. Start the backend

```bash
docker compose up -d
```

The first run builds the API image and pulls Postgres and Chroma. Wait
for all services to become healthy:

```bash
docker compose ps
curl -s http://localhost:8000/health | python3 -m json.tool
```

You should see `"status": "ok"`, `"db_ok": true`, `"storage_ok": true`,
and `"chroma_ok": true`. `"openai_configured"` will be `false` if you
left the key blank, which is expected.

## 3. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000>.

## 4. Walk the product

1. **Register.** Go to <http://localhost:3000/register>. Use any email
   and a password of 8+ characters. You are logged in automatically.
2. **Create a deal room** from the landing page (e.g. "Acme Diligence",
   target company "Acme Corp").
3. **Open the deal room** and upload the three sample files from
   `docs/samples/`:
   - `acme_q1_brief.txt`
   - `acme_risk_factors.docx`
   - `acme_prospectus.pdf`

   Each upload returns `status: "ready"` with a non-zero chunk count.
4. **Ask a question**, for example *"What was Acme's Q1 revenue and how
   did it change year over year?"* The answer renders with citations
   pointing back to the source chunks and a small line showing the
   model name and how many chunks grounded the answer.
5. **Generate a summary** with the "Generate summary" button. A
   structured, cited answer appears immediately below the buttons.
6. **Identify risks** with the "Identify risks" button. You get a
   bulleted risk list drawn from the uploaded files, again with
   citations.
7. Scroll the **history panel** to expand earlier questions. Ask
   answers persist per deal room; analyze results are stateless (re-run
   anytime).
8. **Delete the deal room** from the header. Inline confirmation keeps
   you from destroying data by accident. On confirm you are returned to
   the deal room list and the room is gone from the DB, the filesystem,
   and the Chroma collection.

## 5. Shut everything down

```bash
# Ctrl+C the frontend dev server, then:
docker compose down
```

Your local data (Postgres, Chroma, uploaded files) persists in Docker
volumes and the bind-mounted `./storage` directory. Add `-v` to
`docker compose down` if you want to wipe everything between runs.

## 6. Running with a real OpenAI key (optional)

Stub-LLM answers are deterministic strings, enough to exercise the
ingest/retrieval/citation loop end-to-end without burning credits. To
swap in the real thing:

1. Put your key into `.env`: `OPENAI_API_KEY=sk-...`
2. Restart the API: `docker compose restart api`
3. Ask and analyze calls now route to OpenAI. The code paths are
   unchanged; only the LLM collaborator switches.

MLflow tracking is still off in this mode. To opt in separately, see
the MLflow section of `README.md`.

## Troubleshooting

- **`chroma_ok: false`**: Chroma sometimes needs a few extra seconds on
  first start. Re-run the `curl` after 10–15s, or `docker compose logs
  -f chromadb`.
- **Upload fails with a 4xx error**: the file type or size is outside
  the allowed set. Allowed MIME types are PDF, DOCX, and plain text;
  the cap is `MAX_UPLOAD_BYTES` in `.env` (10 MB default).
- **`/ask` returns 503**: `OPENAI_API_KEY` is required for real
  answers. For the stub-LLM demo path, see the project's local sanity
  tooling rather than the public API.
- **Port 5432 is already in use**: another Postgres instance is bound
  to the host port. Stop it, or remove the `5432:5432` mapping from
  `docker-compose.yml` and access Postgres only through the API
  container.
