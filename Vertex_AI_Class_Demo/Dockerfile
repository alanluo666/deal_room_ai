# Temporary in-class Vertex AI demo scaffold — minimal image for local FastAPI app.
# Main Deal Room AI Dockerfile (repo root) uses Python 3.12 and port 8000 + `api/` package.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
