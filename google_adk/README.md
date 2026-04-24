# Google ADK Agent (Person A Scope)

This folder contains the AI agent module for Deal Room AI.
It implements Google ADK-based agent orchestration, agentic RAG retrieval with ChromaDB, session context/state handling, and citation-enforced responses.

## What This Module Provides

- ADK `LlmAgent` wired with domain tools
- Tooling for:
  - semantic document search
  - document summarization
  - risk analysis
  - structured answer generation with citations
- RAG infrastructure:
  - ChromaDB collection access
  - Vertex AI embedding wrapper
  - metadata-filtered retriever
- Context management:
  - L0-L3 context strategy
  - durable `session.state` facts
  - history token-budget summarization
- Runner interface for API integration (`run_turn`)

## Folder Structure

```text
google_adk/
├── agent.py
├── runner.py
├── config.py
├── schemas.py
├── tools/
├── rag/
└── context/
```

## Environment Variables

Set these before running:

- `GCP_PROJECT`
- `GCP_LOCATION` (default: `us-central1`)
- `GEMINI_MODEL` (default: `gemini-2.0-flash`)
- `EMBEDDING_MODEL` (default: `textembedding-gecko@003`)
- `CHROMA_DATA_DIR` (optional custom local path)

## Install Dependencies

From `deal_room_ai/`:

```bash
pip install -r google_adk/requirements.txt
```

## Minimal Usage

```python
from google_adk import run_turn

response = run_turn(
    session_id="demo-session-1",
    user_message="What are the key risk factors for Apple?"
)

print(response.answer)
for c in response.citations:
    print(c.chunk_id, c.doc_id)
```

## Integration Contract (for API layer)

The API layer should:

1. Receive `session_id` and user `message`
2. Call `run_turn(session_id=..., user_message=...)`
3. Return the `AgentResponse` object to the client

## Notes

- This branch intentionally scopes to `google_adk/` only.
- No merge to `main` is performed as part of this step.
