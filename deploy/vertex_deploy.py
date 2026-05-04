"""Upload the prediction container to Artifact Registry, register the model
in Vertex AI Model Registry, and deploy it to an endpoint.

Run from CI after the container has been pushed:
  python -m deploy.vertex_deploy --image-uri us-central1-docker.pkg.dev/$PROJECT/deal-room-ai/classifier:$SHA

Authentication: relies on the ambient GCP credentials
(GOOGLE_APPLICATION_CREDENTIALS in CI, gcloud ADC locally).
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import yaml
from google.cloud import aiplatform

log = logging.getLogger("deploy")


def _expand_env(value):
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.environ.get(value[2:-1], value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def load_config(path: str | Path) -> dict:
    raw = yaml.safe_load(Path(path).read_text())
    return _expand_env(raw)


def deploy(image_uri: str, config_path: str = "deploy/config.yaml") -> str:
    cfg = load_config(config_path)
    aiplatform.init(project=cfg["project_id"], location=cfg["region"])

    model_cfg = cfg["model"]
    serving = model_cfg["serving_container"]
    log.info("Uploading model with image %s", image_uri)
    model = aiplatform.Model.upload(
        display_name=model_cfg["display_name"],
        description=model_cfg.get("description"),
        serving_container_image_uri=image_uri,
        serving_container_predict_route=serving["predict_route"],
        serving_container_health_route=serving["health_route"],
        serving_container_ports=serving["ports"],
    )

    endpoint_name = cfg["endpoint"]["display_name"]
    existing = aiplatform.Endpoint.list(filter=f'display_name="{endpoint_name}"')
    endpoint = existing[0] if existing else aiplatform.Endpoint.create(
        display_name=endpoint_name
    )

    dm = cfg["deployed_model"]
    log.info("Deploying model to endpoint %s", endpoint.resource_name)
    endpoint.deploy(
        model=model,
        machine_type=dm["machine_type"],
        min_replica_count=dm["min_replica_count"],
        max_replica_count=dm["max_replica_count"],
        traffic_percentage=100,
    )
    log.info("Deployed. Endpoint: %s", endpoint.resource_name)
    return endpoint.resource_name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--image-uri",
        required=True,
        help="Full Artifact Registry image URI to deploy.",
    )
    parser.add_argument("--config", default="deploy/config.yaml")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(
        level=args.log_level, format="%(levelname)s %(name)s: %(message)s"
    )
    deploy(args.image_uri, args.config)


if __name__ == "__main__":
    main()
