"""Eval utilities — kept separate so train.py and CI both call the same code."""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)


@dataclass
class EvalReport:
    accuracy: float
    macro_f1: float
    macro_precision: float
    macro_recall: float
    text_report: str


def evaluate(y_true: list[str], y_pred: list[str]) -> EvalReport:
    return EvalReport(
        accuracy=accuracy_score(y_true, y_pred),
        macro_f1=f1_score(y_true, y_pred, average="macro", zero_division=0),
        macro_precision=precision_score(
            y_true, y_pred, average="macro", zero_division=0
        ),
        macro_recall=recall_score(y_true, y_pred, average="macro", zero_division=0),
        text_report=classification_report(y_true, y_pred, zero_division=0),
    )
