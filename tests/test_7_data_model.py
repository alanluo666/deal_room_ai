"""Day-11 style data + model tests (4 data, 3 model)."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest
from sklearn.metrics import recall_score
from sklearn.model_selection import train_test_split

from classifier.data import load_csv, synthetic
from classifier.labels import DOC_TYPES
from classifier.model import build_pipeline


def _make_small_csv(tmp_path: Path, rows: list[dict[str, str]]) -> Path:
    csv_path = tmp_path / "dataset.csv"
    lines = ["text,label"]
    for row in rows:
        lines.append(f"{row['text']},{row['label']}")
    csv_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path


def _train_on_synthetic(n_per_class: int = 30, seed: int = 7):
    dataset = synthetic(n_per_class=n_per_class, seed=seed)
    X_train, X_test, y_train, y_test = train_test_split(
        dataset.texts,
        dataset.labels,
        test_size=0.25,
        random_state=123,
        stratify=dataset.labels,
    )
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    return pipeline, X_test, y_test


def test_data_schema_load_csv_enforces_required_columns(tmp_path):
    # Data test: schema (positive and negative case).
    good = _make_small_csv(
        tmp_path,
        [
            {"text": "Revenue grew 10 percent", "label": "financials"},
            {"text": "This Agreement is effective", "label": "contract"},
        ],
    )
    ds = load_csv(good)
    assert ds.texts == ["Revenue grew 10 percent", "This Agreement is effective"]
    assert ds.labels == ["financials", "contract"]

    bad = tmp_path / "missing_label.csv"
    bad.write_text("text\nRevenue only row\n", encoding="utf-8")
    with pytest.raises(KeyError):
        load_csv(bad)


def test_data_distribution_synthetic_is_balanced():
    # Data test: distribution.
    ds = synthetic(n_per_class=20, seed=99)
    counts = Counter(ds.labels)
    assert set(counts.keys()) == set(DOC_TYPES)
    # Synthetic generator should be class-balanced by construction.
    assert all(v == 20 for v in counts.values())


def test_data_integrity_no_empty_texts_or_unknown_labels():
    # Data test: integrity.
    ds = synthetic(n_per_class=15, seed=11)
    assert len(ds.texts) == len(ds.labels)
    assert len(ds.texts) > 0
    for text, label in zip(ds.texts, ds.labels):
        assert isinstance(text, str)
        assert text.strip() != ""
        assert label in DOC_TYPES


def test_data_semantics_synthetic_contains_label_specific_keywords():
    # Data test: semantics.
    ds = synthetic(n_per_class=25, seed=42)
    by_label: dict[str, list[str]] = {label: [] for label in DOC_TYPES}
    for text, label in zip(ds.texts, ds.labels):
        by_label[label].append(text.lower())

    expectations = {
        "financials": ["revenue", "ebitda", "balance sheet", "cash flow"],
        "legal": ["indemnification", "jurisdiction", "limitation of liability"],
        "mgmt_presentation": ["go-to-market", "slide", "roadmap", "vision"],
        "contract": ["agreement", "parties", "shall"],
        "due_diligence_report": ["due diligence findings", "risk rating", "recommendation"],
        "email_correspondence": ["from:", "to:", "subject:", "best regards"],
        "other": ["misc note", "memo", "internal"],
    }
    for label, keywords in expectations.items():
        joined = " ".join(by_label[label])
        assert any(keyword in joined for keyword in keywords), label


def test_model_slice_recall_meets_floor_per_label():
    # Model test: slice quality.
    model, X_test, y_test = _train_on_synthetic(n_per_class=35, seed=17)
    y_pred = model.predict(X_test)

    per_label_recall = recall_score(
        y_test,
        y_pred,
        labels=list(DOC_TYPES),
        average=None,
        zero_division=0,
    )
    # Balanced threshold: avoid flaky strictness but catch major failures.
    assert all(r >= 0.70 for r in per_label_recall), per_label_recall


def test_model_invariance_to_case_spacing_and_punctuation():
    # Model test: invariance under non-semantic perturbations.
    model, _, _ = _train_on_synthetic(n_per_class=35, seed=21)
    base_cases = [
        "Revenue Q2 2026 and cash flow are strong.",
        "This Agreement shall bind the Parties.",
        "Subject: follow up To: team@example.com",
    ]
    perturbations = [
        lambda s: s.upper(),
        lambda s: f"   {s}   ",
        lambda s: s.replace(".", " . ").replace(":", " : "),
    ]
    for text in base_cases:
        base_pred = model.predict([text])[0]
        for transform in perturbations:
            alt_pred = model.predict([transform(text)])[0]
            assert alt_pred == base_pred


def test_model_calibration_probability_sanity_and_confidence_floor():
    # Model test: calibration-oriented sanity checks.
    model, X_test, y_test = _train_on_synthetic(n_per_class=35, seed=33)
    probs = model.predict_proba(X_test)
    classes = model.classes_
    preds = model.predict(X_test)

    # Probability simplex checks.
    for row in probs:
        assert all(p >= 0.0 for p in row)
        assert abs(float(sum(row)) - 1.0) < 1e-6

    # Confidence sanity: correct predictions should not be uniformly low confidence.
    class_to_idx = {label: i for i, label in enumerate(classes)}
    correct_conf = []
    for pred, true_label, row in zip(preds, y_test, probs):
        if pred == true_label:
            correct_conf.append(float(row[class_to_idx[pred]]))
    assert correct_conf, "Expected at least one correct prediction"
    assert sum(correct_conf) / len(correct_conf) >= 0.55


def test_ingestion_boundary_infers_doc_type_and_passes_to_build_chunks(
    tmp_path, monkeypatch
):
    # Boundary check: ingestion should infer doc_type and pass it to build_chunks.
    from ingestion import pipeline as ingestion_pipeline

    sample_file = tmp_path / "doc.txt"
    sample_file.write_text("Revenue and EBITDA details", encoding="utf-8")

    captured: dict[str, object] = {}

    class _FakeStore:
        def __init__(self) -> None:
            self.deleted_document_ids: list[int] = []
            self.upsert_count = 0

        def delete_document(self, document_id: int) -> None:
            self.deleted_document_ids.append(document_id)

        def upsert_chunks(self, chunks) -> None:
            self.upsert_count += len(chunks)

    fake_store = _FakeStore()

    class _FakeEmbedder:
        def embed(self, texts):  # pragma: no cover - not used directly in this test
            return [[0.0] for _ in texts]

    def _fake_build_chunks(**kwargs):
        captured.update(kwargs)
        return [object(), object()]

    monkeypatch.setattr(ingestion_pipeline, "_resolve_mime", lambda _p: "text/plain")
    monkeypatch.setattr(
        ingestion_pipeline, "extract_text", lambda mime_type, data: "Revenue and EBITDA"
    )
    monkeypatch.setattr(
        ingestion_pipeline, "predict_doc_type", lambda text: "financials"
    )
    monkeypatch.setattr(ingestion_pipeline, "EmbeddingClient", _FakeEmbedder)
    monkeypatch.setattr(ingestion_pipeline, "build_chunks", _fake_build_chunks)
    monkeypatch.setattr(ingestion_pipeline, "get_vector_store", lambda: fake_store)

    count = ingestion_pipeline.ingest_file(
        sample_file, deal_room_id=1, user_id=2, document_id=3
    )

    assert count == 2
    assert captured["doc_type"] == "financials"
    assert captured["deal_room_id"] == 1
    assert captured["user_id"] == 2
    assert captured["document_id"] == 3
    assert fake_store.deleted_document_ids == [3]
    assert fake_store.upsert_count == 2


def test_deploy_boundary_predict_returns_label_and_scores_shape(monkeypatch):
    # Boundary check: deploy predictor contract includes label + scores per instance.
    from deploy import predictor as deploy_predictor

    monkeypatch.setattr(
        deploy_predictor, "predict_doc_type", lambda text: "contract"
    )
    monkeypatch.setattr(
        deploy_predictor,
        "predict_with_scores",
        lambda text: {"contract": 0.82, "legal": 0.18},
    )

    request = deploy_predictor.PredictRequest(
        instances=[deploy_predictor.Instance(text="This Agreement shall bind the Parties.")]
    )
    response = deploy_predictor.predict(request)

    assert len(response.predictions) == 1
    first = response.predictions[0]
    assert first.label == "contract"
    assert isinstance(first.scores, dict)
    assert set(first.scores.keys()) == {"contract", "legal"}
    assert abs(sum(first.scores.values()) - 1.0) < 1e-9
