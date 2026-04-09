# Temporary in-class Vertex AI demo scaffold — sample online prediction (replace endpoint name).
"""
Send one dummy prediction to a deployed Vertex AI Endpoint.

The main Deal Room AI product API (`../api/main.py`, OpenAI + MLflow) is separate;
use this script only after deploying a model with `deploy_model.py`.
"""

from google.cloud import aiplatform

import config

# After deployment: paste your real Vertex AI Endpoint resource name here (full string).
# Paste the full resource name from the console or deploy_model output after deployment.
ENDPOINT_RESOURCE_NAME = (
    "projects/your-project-id/locations/us-central1/endpoints/your-endpoint-id"
)


def main() -> None:
    aiplatform.init(project=config.PROJECT_ID, location=config.REGION)

    endpoint = aiplatform.Endpoint(ENDPOINT_RESOURCE_NAME)
    # Dummy sklearn-style instance; adjust keys/shape to match your deployed model.
    instances = [{"dense_input": [1.0, 2.0, 3.0, 4.0]}]
    response = endpoint.predict(instances=instances)
    print(response)


if __name__ == "__main__":
    main()
