FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ api/

EXPOSE 8000

# Honor $PORT so the image can boot on Cloud Run (which injects PORT=8080).
# Falls back to 8000 when $PORT is unset, which keeps `docker run` and
# docker-compose (which overrides `command:` anyway) behaving as before.
# Uses `exec` so uvicorn becomes PID 1 and receives SIGTERM cleanly.
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
