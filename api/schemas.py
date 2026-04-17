from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class DealRoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    target_company: str | None = Field(default=None, max_length=255)


class DealRoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    target_company: str | None
    created_at: datetime
