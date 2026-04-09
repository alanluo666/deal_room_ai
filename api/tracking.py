import os
import time

import mlflow
from dotenv import load_dotenv

load_dotenv()


class TrackingManager:
    def __init__(self) -> None:
        self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "")
        self.experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "team-project")
        self.enabled = bool(self.tracking_uri)

    def configure(self) -> None:
        if not self.enabled:
            return
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)

    def log_prediction(
        self,
        *,
        task: str,
        model_name: str,
        latency_seconds: float,
        success: bool,
        question_present: bool,
        error_message: str | None = None,
    ) -> None:
        if not self.enabled:
            return

        with mlflow.start_run():
            mlflow.log_param("provider", "openai")
            mlflow.log_param("model", model_name)
            mlflow.log_param("task", task)
            mlflow.log_param("question_present", question_present)
            mlflow.log_metric("latency_seconds", latency_seconds)
            mlflow.log_metric("success", int(success))

            if error_message:
                mlflow.log_param("error_message", error_message[:250])


tracking_manager = TrackingManager()


def timed_call() -> float:
    return time.perf_counter()


def elapsed_seconds(start_time: float) -> float:
    return time.perf_counter() - start_time
