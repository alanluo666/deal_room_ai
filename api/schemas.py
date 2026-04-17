from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from api.tasks import Task


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


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    deal_room_id: int
    filename: str
    mime_type: str
    size_bytes: int
    status: str
    error_message: str | None
    chunk_count: int
    created_at: datetime


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)


class Citation(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    snippet: str


class AskResponse(BaseModel):
    question_id: int
    answer: str
    citations: list[Citation]
    model: str
    chunks_used: int


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    deal_room_id: int
    user_id: int
    question: str
    answer: str
    citations: list[Citation]
    created_at: datetime


class AnalyzeRequest(BaseModel):
    task: Task
    top_k: int = Field(default=8, ge=1, le=10)


class AnalyzeResponse(BaseModel):
    task: str
    answer: str
    citations: list[Citation]
    model: str
    chunks_used: int


# ---------------------------------------------------------------------------
# Chat (Person C slice)
#
# DTOs for the forthcoming ``POST /deal-rooms/{id}/chat`` endpoint. The wrapper
# route is intentionally not wired yet; these types exist so the backend and
# frontend agree on a stable contract before any route or component code
# depends on them. Shapes are chosen to stay compatible with Person A's later
# ADK agent (multi-turn ``messages``, optional ``session_id``, reserved
# ``steps`` for agent step traces) without requiring any ADK dependency now.
# ---------------------------------------------------------------------------


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: ChatRole
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=50)
    top_k: int = Field(default=5, ge=1, le=10)
    session_id: str | None = Field(default=None, max_length=128)


class ChatStep(BaseModel):
    """Reserved for Person A's ADK step traces. Person C does not populate this."""

    name: str
    detail: str | None = None


class ChatResponse(BaseModel):
    message: ChatMessage
    citations: list[Citation]
    model: str
    chunks_used: int
    session_id: str | None = None
    steps: list[ChatStep] = Field(default_factory=list)
