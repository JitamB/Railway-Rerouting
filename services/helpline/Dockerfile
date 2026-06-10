# CascadeGuard helpline service (skeleton).
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
COPY cascadeguard_helpline ./cascadeguard_helpline
RUN pip install --no-cache-dir .

EXPOSE 8100
CMD ["python", "-m", "cascadeguard_helpline.agent"]
