from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    task: str = Field(
        default="summary",
        description="The due diligence task to run, such as summary, risks, or qa.",
    )
    document_text: str = Field(
        ...,
        min_length=1,
        description="The text content to analyze.",
    )
    question: str | None = Field(
        default=None,
        description="Optional question to answer from the document.",
    )


class PredictionResponse(BaseModel):
    result: str
    model: str
    mlflow_tracking_enabled: bool
