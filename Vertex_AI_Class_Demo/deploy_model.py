# Temporary in-class Vertex AI demo scaffold — uploads artifact and deploys to an endpoint (demo only).
"""
Minimal Vertex AI Model + Endpoint deploy demo.

Sits alongside the Deal Room AI FastAPI service (`../api/`), which uses OpenAI + MLflow
for document analysis — this script does not call that code; it only demonstrates
Vertex model upload and deployment.

The artifact at MODEL_ARTIFACT_URI must contain a model file compatible with the chosen
serving container (e.g. sklearn pickle + sklearn prebuilt image). Otherwise deployment
or serving may fail — this script is for structure only.
"""

from google.cloud import aiplatform

import config

# Prebuilt sklearn CPU serving image (example). Match versions to your saved model.
SERVING_CONTAINER_IMAGE_URI = (
    "us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-3:latest"
)


def main() -> None:
    aiplatform.init(project=config.PROJECT_ID, location=config.REGION)

    model = aiplatform.Model.upload(
        display_name=config.MODEL_DISPLAY_NAME,
        artifact_uri=config.MODEL_ARTIFACT_URI,
        serving_container_image_uri=SERVING_CONTAINER_IMAGE_URI,
    )
    print(f"Model resource name: {model.resource_name}")

    endpoint = aiplatform.Endpoint.create(display_name=config.ENDPOINT_DISPLAY_NAME)
    print(f"Endpoint resource name: {endpoint.resource_name}")

    model.deploy(
        endpoint=endpoint,
        machine_type="n1-standard-2",
        min_replica_count=1,
        max_replica_count=2,
    )
    print("Deploy call issued.")
    print(f"Deployed model on endpoint: {endpoint.resource_name}")


if __name__ == "__main__":
    main()
