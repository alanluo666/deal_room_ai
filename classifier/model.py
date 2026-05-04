"""Classifier definition.

Architecture: TF-IDF (1-2 grams) + multinomial Logistic Regression in a single
sklearn Pipeline. This is intentionally lightweight — the document TYPE problem
is mostly lexical (financials vs. legal vs. mgmt deck), so a TF-IDF baseline
typically gets 85%+ macro-F1 and runs on CPU in milliseconds.

If we hit a quality ceiling, the upgrade path is to swap _build_pipeline for a
sentence-transformers encoder + LR head without changing the training loop.
"""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.95,
                    strip_accents="unicode",
                    lowercase=True,
                ),
            ),
            (
                "lr",
                LogisticRegression(
                    max_iter=1000,
                    n_jobs=-1,
                    class_weight="balanced",
                ),
            ),
        ]
    )
