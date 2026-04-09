# Temporary in-class Vertex AI demo scaffold — minimal KFP pipeline (placeholder logic only).
"""Compile and run a tiny Vertex AI Pipeline demo."""

from kfp import dsl
from kfp.compiler import Compiler
from google.cloud import aiplatform

import config


@dsl.component
def prepare_data() -> str:
    print("[demo] prepare_data: placeholder step")
    return "gs://placeholder-bucket/prepared-data"


@dsl.component
def train_model(data: str, model_uri: str) -> str:
    print(f"[demo] train_model: data={data!r}, model_uri={model_uri!r}")
    return model_uri


@dsl.component
def evaluate_model(model_uri: str) -> float:
    print(f"[demo] evaluate_model: model_uri={model_uri!r}")
    return 0.0


@dsl.pipeline(name="deal-room-ai-vertex-class-demo-pipeline")
def deal_room_ai_vertex_class_demo_pipeline(model_uri: str = config.MODEL_ARTIFACT_URI):
    prep = prepare_data()
    train = train_model(data=prep.output, model_uri=model_uri)
    evaluate_model(model_uri=train.output)


def compile_pipeline() -> None:
    Compiler().compile(
        pipeline_func=deal_room_ai_vertex_class_demo_pipeline,
        package_path=config.PIPELINE_TEMPLATE_PATH,
    )
    print(f"Compiled pipeline template -> {config.PIPELINE_TEMPLATE_PATH}")


def run_pipeline() -> None:
    aiplatform.init(project=config.PROJECT_ID, location=config.REGION)
    job = aiplatform.PipelineJob(
        display_name=config.PIPELINE_DISPLAY_NAME,
        template_path=config.PIPELINE_TEMPLATE_PATH,
        pipeline_root=config.PIPELINE_ROOT,
        parameter_values={"model_uri": config.MODEL_ARTIFACT_URI},
    )
    job.run(sync=True)
    print("PipelineJob submitted/run finished (sync).")


if __name__ == "__main__":
    compile_pipeline()
    run_pipeline()
