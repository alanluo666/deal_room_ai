from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.db import get_db
from api.routers import auth as auth_router
from api.routers import deal_rooms as deal_rooms_router
from api.schemas import PredictionRequest, PredictionResponse
from api.service import openai_service
from api.tracking import elapsed_seconds, timed_call, tracking_manager

app = FastAPI(title="Deal Room AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(deal_rooms_router.router)


@app.on_event("startup")
def startup_event():
    tracking_manager.configure()


@app.get("/")
def root():
    return {"message": "Deal Room AI API is running"}


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "status": "ok",
        "openai_configured": openai_service.is_ready(),
        "openai_model": openai_service.model,
        "mlflow_tracking_enabled": tracking_manager.enabled,
        "mlflow_tracking_uri": tracking_manager.tracking_uri,
        "mlflow_experiment_name": tracking_manager.experiment_name,
        "db_ok": db_ok,
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
