"""Vertex AI text-embedding wrapper.

Uses textembedding-gecko@003 via the google-cloud-aiplatform SDK.
Vertex AI is initialised lazily on first call so that importing this module
does not require credentials at import time.
"""

from __future__ import annotations

import logging

import vertexai
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

from ..config import EMBEDDING_MODEL, GCP_LOCATION, GCP_PROJECT

logger = logging.getLogger(__name__)

_model: TextEmbeddingModel | None = None


def _get_model() -> TextEmbeddingModel:
    global _model
    if _model is None:
        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
        _model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)
        logger.info("Loaded embedding model: %s", EMBEDDING_MODEL)
    return _model


def embed(text: str) -> list[float]:
    """Return the embedding vector for a single text string."""
    model = _get_model()
    inputs = [TextEmbeddingInput(text=text, task_type="RETRIEVAL_QUERY")]
    embeddings = model.get_embeddings(inputs)
    return embeddings[0].values


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Return embedding vectors for a batch of texts (for ingestion use)."""
    model = _get_model()
    inputs = [
        TextEmbeddingInput(text=t, task_type="RETRIEVAL_DOCUMENT") for t in texts
    ]
    embeddings = model.get_embeddings(inputs)
    return [e.values for e in embeddings]
