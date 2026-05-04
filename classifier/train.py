"""Train the document-type classifier and log to MLflow.

Reuses MLFLOW_TRACKING_URI / MLFLOW_EXPERIMENT_NAME from .env so this lives in
the same MLflow workspace as the API service metrics.

Usage:
  python -m classifier.train --data ./data/labels.csv
  python -m classifier.train --synthetic   # smoke test before labels exist
"""

from __future__ import annotations

import argparse
import logging
import os
import tempfile
from pathlib import Path

import joblib
import mlflow
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split

from classifier.data import Dataset, load_csv, synthetic
from classifier.evaluate import evaluate
from classifier.model import build_pipeline

load_dotenv()
log = logging.getLogger("classifier.train")


def _configure_mlflow() -> bool:
    uri = os.getenv("MLFLOW_TRACKING_URI", "")
    if not uri:
        return False
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "team-project"))
    return True


def train(
    dataset: Dataset,
    *,
    test_size: float = 0.2,
    random_state: int = 42,
    output_path: str | None = None,
) -> str:
    """Train, evaluate, log to MLflow. Returns the saved model path."""
    tracking_enabled = _configure_mlflow()

    X_train, X_test, y_train, y_test = train_test_split(
        dataset.texts,
        dataset.labels,
        test_size=test_size,
        random_state=random_state,
        stratify=dataset.labels,
    )

    pipeline = build_pipeline()

    run_ctx = (
        mlflow.start_run(run_name="doc_type_classifier")
        if tracking_enabled
        else _NullCtx()
    )
    with run_ctx:
        pipeline.fit(X_train, y_train)
        report = evaluate(y_test, pipeline.predict(X_test).tolist())

        log.info("accuracy=%.4f macro_f1=%.4f", report.accuracy, report.macro_f1)
        log.info("\n%s", report.text_report)

        out = Path(output_path or tempfile.mkstemp(suffix=".joblib")[1])
        joblib.dump(pipeline, out)

        if tracking_enabled:
            mlflow.log_param("model_type", "tfidf+logreg")
            mlflow.log_param("ngram_range", "1-2")
            mlflow.log_param("n_train", len(X_train))
            mlflow.log_param("n_test", len(X_test))
            mlflow.log_metric("accuracy", report.accuracy)
            mlflow.log_metric("macro_f1", report.macro_f1)
            mlflow.log_metric("macro_precision", report.macro_precision)
            mlflow.log_metric("macro_recall", report.macro_recall)
            mlflow.log_artifact(str(out), artifact_path="model")
            mlflow.sklearn.log_model(pipeline, artifact_path="sklearn_model")

        return str(out)


class _NullCtx:
    def __enter__(self):
        return None

    def __exit__(self, *args):
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--data", help="CSV with columns text,label")
    src.add_argument(
        "--synthetic",
        action="store_true",
        help="Use templated synthetic data — pipeline smoke test only.",
    )
    parser.add_argument("--out", default="./classifier_model.joblib")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(
        level=args.log_level, format="%(levelname)s %(name)s: %(message)s"
    )

    ds = synthetic() if args.synthetic else load_csv(args.data)
    saved = train(ds, output_path=args.out)
    log.info("Model saved to %s", saved)


if __name__ == "__main__":
    main()
