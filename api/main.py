import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.db import get_db
from api.deps import vector_store_dep
from api.middleware import install_request_logging
from api.routers import analyze as analyze_router
from api.routers import auth as auth_router
from api.routers import chat as chat_router
from api.routers import deal_rooms as deal_rooms_router
from api.routers import documents as documents_router
from api.routers import questions as questions_router
from api.schemas import PredictionRequest, PredictionResponse
from api.service import openai_service
from api.tracking import elapsed_seconds, timed_call, tracking_manager
from api.vector_store import VectorStore

app = FastAPI(title="Deal Room AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

install_request_logging(app)

app.include_router(auth_router.router)
app.include_router(deal_rooms_router.router)
app.include_router(documents_router.router)
app.include_router(questions_router.router)
app.include_router(analyze_router.router)
app.include_router(chat_router.router)


@app.on_event("startup")
def startup_event():
    # Fail fast if the signing key is missing. Without this guard the app
    # would silently sign session cookies with the empty string, which is
    # trivially forgeable. Tests and docker-compose both set JWT_SECRET
    # explicitly via env, so this only triggers on real misconfiguration.
    if not settings.JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET is not set. Configure it in .env before starting the API."
        )
    tracking_manager.configure()


@app.get("/")
def root():
    return {"message": "Deal Room AI API is running"}


@app.get("/livez")
def livez():
    """Liveness probe.

    Intentionally trivial: if the process can answer this endpoint at all, it
    is considered live. Does not touch the database, Chroma, storage, or any
    external service.
    """
    return {"status": "ok"}


@app.get("/readyz")
async def readyz(
    db: AsyncSession = Depends(get_db),
    vector_store: VectorStore = Depends(vector_store_dep),
):
    """Readiness probe.

    Returns 200 only when the API can actually serve traffic, which requires
    the database, the vector store, and the local storage directory to all be
    usable. Returns 503 with per-dependency booleans when any check fails.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    try:
        chroma_ok = vector_store.health_check()
    except Exception:
        chroma_ok = False

    storage_ok = os.path.isdir(settings.STORAGE_DIR) and os.access(
        settings.STORAGE_DIR, os.W_OK
    )

    payload = {
        "status": "ok" if (db_ok and chroma_ok and storage_ok) else "not_ready",
        "db_ok": db_ok,
        "chroma_ok": chroma_ok,
        "storage_ok": storage_ok,
    }
    status_code = 200 if payload["status"] == "ok" else 503
    return JSONResponse(status_code=status_code, content=payload)


@app.get("/health")
async def health(
    db: AsyncSession = Depends(get_db),
    vector_store: VectorStore = Depends(vector_store_dep),
):
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    storage_ok = os.path.isdir(settings.STORAGE_DIR) and os.access(
        settings.STORAGE_DIR, os.W_OK
    )

    try:
        chroma_ok = vector_store.health_check()
    except Exception:
        chroma_ok = False

    return {
        "status": "ok",
        "openai_configured": openai_service.is_ready(),
        "openai_model": openai_service.model,
        "mlflow_tracking_enabled": tracking_manager.enabled,
        "mlflow_tracking_uri": tracking_manager.tracking_uri,
        "mlflow_experiment_name": tracking_manager.experiment_name,
        "db_ok": db_ok,
        "storage_ok": storage_ok,
        "chroma_ok": chroma_ok,
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    start_time = timed_call()

    try:
        result = openai_service.run_prediction(request)
        tracking_manager.log_prediction(
            task=request.task,
            model_name=openai_service.model,
            latency_seconds=elapsed_seconds(start_time),
            success=True,
            question_present=bool(request.question),
        )
        return PredictionResponse(
            result=result,
            model=openai_service.model,
            mlflow_tracking_enabled=tracking_manager.enabled,
        )
    except Exception as exc:
        tracking_manager.log_prediction(
            task=request.task,
            model_name=openai_service.model,
            latency_seconds=elapsed_seconds(start_time),
            success=False,
            question_present=bool(request.question),
            error_message=str(exc),
        )
        raise HTTPException(status_code=500, detail=str(exc))
