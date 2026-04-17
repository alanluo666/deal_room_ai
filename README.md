<<<<<<< HEAD
# deal_room_ai
Document Review Workspace for Smaller Deal Teams — a collaborative SaaS platform for search funds, independent sponsors, boutique M&amp;A advisors, and small corp dev teams. The idea is to focus on the document-heavy part of diligence by bringing filings, contracts, and management transcripts into one workspace.
=======
# Deal Room AI

Document Review Workspace for Smaller Deal Teams — a collaborative SaaS platform for search funds, independent sponsors, boutique M&A advisors, and small corp dev teams. The platform focuses on the document-heavy part of due diligence by bringing filings, contracts, and management transcripts into one workspace, powered by AI-driven analysis.

## Prerequisites

- Python 3.12+
- Docker (for containerized deployment)
- An OpenAI API key (required for the `/predict` endpoint)
- Access to the team MLflow server (optional, for experiment tracking)

## Environment Setup

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Fill in your values in `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5-mini
OPENAI_MAX_OUTPUT_TOKENS=400
MLFLOW_TRACKING_URI=http://<EXTERNAL_IP>:5000
MLFLOW_EXPERIMENT_NAME=team-project
```

> **Note:** Never commit your `.env` file to Git. It is already in `.gitignore`.

## Running Locally (without Docker)

```bash
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## Running with Docker

### Build the image

```bash
docker build -t deal-room-ai .
```

### Run the container

```bash
docker run --rm -p 8000:8000 --env-file .env deal-room-ai
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### `GET /` — Root

Returns a welcome message confirming the API is running.

```bash
curl http://localhost:8000/
```

Response:

```json
{
  "message": "Deal Room AI API is running"
}
```

### `GET /health` — Health Check

Returns service status including model configuration and MLflow tracking state.

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "ok",
  "openai_configured": true,
  "openai_model": "gpt-5-mini",
  "mlflow_tracking_enabled": true,
  "mlflow_tracking_uri": "http://<EXTERNAL_IP>:5000",
  "mlflow_experiment_name": "team-project"
}
```

### `POST /predict` — Model Prediction

Accepts document text and returns AI-generated analysis. Supports three task types: `summary` (default), `risks`, and `qa`.

#### Example: Summarize a document

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "task": "summary",
    "document_text": "Acme Corp reported $5M revenue in Q1 2026, up 20% year-over-year. Operating margins improved to 15% from 12%. The company expanded into two new markets and signed three enterprise contracts."
  }'
```

Response:

```json
{
  "result": "<AI-generated summary of the document>",
  "model": "gpt-5-mini",
  "mlflow_tracking_enabled": true
}
```

#### Example: Identify risks

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "task": "risks",
    "document_text": "The company has a single customer representing 60% of revenue. Key management personnel have no non-compete agreements."
  }'
```

#### Example: Ask a question about a document

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "task": "qa",
    "document_text": "Acme Corp was founded in 2019 and is headquartered in Austin, TX. The company has 45 employees.",
    "question": "Where is the company headquartered?"
  }'
```

#### Request Body Schema

| Field           | Type   | Required | Description                                                   |
|-----------------|--------|----------|---------------------------------------------------------------|
| `task`          | string | No       | Task type: `summary` (default), `risks`, or `qa`             |
| `document_text` | string | Yes      | The document text to analyze (must be non-empty)              |
| `question`      | string | No       | Question to answer (used when `task` is `qa`)                 |

#### Response Body Schema

| Field                    | Type    | Description                              |
|--------------------------|---------|------------------------------------------|
| `result`                 | string  | The AI-generated analysis                |
| `model`                  | string  | The model used for inference             |
| `mlflow_tracking_enabled`| boolean | Whether the prediction was logged to MLflow |

## MLflow Tracking

Every call to `/predict` is automatically logged to the team MLflow server with:

- **Parameters:** provider, model, task type, whether a question was included
- **Metrics:** latency (seconds), success (1 or 0)

View the MLflow UI at: `http://<EXTERNAL_IP>:5000`

## Project Structure

```
deal_room_ai/
├── api/
│   ├── __init__.py
│   ├── main.py          # FastAPI app and endpoint definitions
│   ├── schemas.py        # Pydantic request/response models
│   ├── service.py        # OpenAI service for LLM inference
│   └── tracking.py       # MLflow tracking manager
├── .env.example           # Environment variable template
├── .gitignore
├── Dockerfile             # Container definition
├── MLFlow_Server_SetUp.ipynb  # Notebook to verify MLflow connectivity
├── README.md
└── requirements.txt
```
>>>>>>> ded75868216a9e970b401cdf59816648482fbd7c
