"""Inference helper — used by both the ingestion pipeline and the deploy
predictor. Loads the model lazily and caches it module-level.
"""

from __future__ import annotations

import os
from functools import lru_cache

import joblib

from classifier.labels import DOC_TYPES

_DEFAULT_PATH = os.getenv("CLASSIFIER_MODEL_PATH", "./classifier_model.joblib")


@lru_cache(maxsize=1)
def _load_model(path: str):
    return joblib.load(path)


def predict_doc_type(text: str, *, model_path: str | None = None) -> str:
    if not text or not text.strip():
        return "other"
    model = _load_model(model_path or _DEFAULT_PATH)
    label = str(model.predict([text])[0])
    return label if label in DOC_TYPES else "other"


def predict_with_scores(
    text: str, *, model_path: str | None = None
) -> dict[str, float]:
    """Returns {label: probability} so callers can apply confidence thresholds."""
    model = _load_model(model_path or _DEFAULT_PATH)
    probs = model.predict_proba([text])[0]
    classes = model.classes_
    return {str(c): float(p) for c, p in zip(classes, probs)}
