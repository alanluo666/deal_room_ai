"""Vertex AI custom-prediction container handler.

Vertex AI hits two HTTP routes on the container:
  GET  /health     -> 200 if the model loaded
  POST /predict    -> {"instances": [{"text": "..."}, ...]}
                       returns {"predictions": [{"label": "...",
                                                  "scores": {...}}, ...]}

Run locally:
  CLASSIFIER_MODEL_PATH=./classifier_model.joblib \\
      uvicorn deploy.predictor:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from classifier.predict import predict_doc_type, predict_with_scores

app = FastAPI(title="Deal Room AI — Doc Type Classifier")


class Instance(BaseModel):
    text: str


class PredictRequest(BaseModel):
    instances: list[Instance]


class Prediction(BaseModel):
    label: str
    scores: dict[str, float]


class PredictResponse(BaseModel):
    predictions: list[Prediction]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    out: list[Prediction] = []
    for inst in request.instances:
        out.append(
            Prediction(
                label=predict_doc_type(inst.text),
                scores=predict_with_scores(inst.text),
            )
        )
    return PredictResponse(predictions=out)
