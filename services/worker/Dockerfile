# CascadeGuard worker (skeleton) — pipeline orchestrator.
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
COPY cascadeguard_worker ./cascadeguard_worker
RUN pip install --no-cache-dir .

CMD ["python", "-m", "cascadeguard_worker.pipeline"]
