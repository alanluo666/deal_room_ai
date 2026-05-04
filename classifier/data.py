"""Training-data loading.

Expected layout on disk (CSV):
    text,label
    "...","financials"
    "...","legal"

For a smoke test we also expose a tiny synthetic generator so train.py runs
end-to-end before real labeled data exists.
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

from classifier.labels import DOC_TYPES


@dataclass
class Dataset:
    texts: list[str]
    labels: list[str]


def load_csv(path: str | Path) -> Dataset:
    texts: list[str] = []
    labels: list[str] = []
    with Path(path).open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["text"])
            labels.append(row["label"])
    return Dataset(texts=texts, labels=labels)


def synthetic(n_per_class: int = 40, seed: int = 7) -> Dataset:
    """Tiny templated dataset for pipeline smoke tests — NOT a real model."""
    rng = random.Random(seed)
    snippets = {
        "financials": ["Revenue Q{q} {y}", "EBITDA margin", "Balance sheet", "Cash flow"],
        "legal": ["Indemnification", "Jurisdiction", "Limitation of liability"],
        "mgmt_presentation": ["Go-to-market", "Slide", "Roadmap", "Vision"],
        "contract": ["This Agreement", "the Parties", "shall"],
        "due_diligence_report": ["Due diligence findings", "Risk rating", "Recommendation"],
        "email_correspondence": ["From:", "To:", "Subject:", "Best regards"],
        "other": ["Misc note", "Memo", "Internal"],
    }
    texts: list[str] = []
    labels: list[str] = []
    for label in DOC_TYPES:
        for _ in range(n_per_class):
            phrase = rng.choice(snippets[label])
            filler = " ".join(rng.choice(["alpha", "beta", "gamma"]) for _ in range(20))
            texts.append(f"{phrase} {filler}")
            labels.append(label)
    pairs = list(zip(texts, labels))
    rng.shuffle(pairs)
    texts, labels = zip(*pairs)
    return Dataset(texts=list(texts), labels=list(labels))
