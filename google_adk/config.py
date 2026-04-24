import os
from pathlib import Path

# --- Model ---
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "textembedding-gecko@003")

# --- Vertex AI ---
GCP_PROJECT = os.getenv("GCP_PROJECT", "")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# --- ChromaDB ---
CHROMA_DATA_DIR = os.getenv(
    "CHROMA_DATA_DIR",
    str(Path(__file__).parent.parent / "chroma_data"),
)
CHROMA_COLLECTION = "deal_room_docs"

# --- RAG retrieval ---
DEFAULT_TOP_K = 5

# --- Context / history ---
# Max tokens allowed for verbatim conversation history before summarization kicks in
HISTORY_TOKEN_BUDGET = 3_000
# Number of most-recent turns (user+assistant pairs) to keep verbatim
HISTORY_KEEP_RECENT = 6

# --- ADK app name (used by Runner) ---
ADK_APP_NAME = "deal_room_ai"
