FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY runner.py ./
COPY pipelines/ ./pipelines/

RUN pip install --no-cache-dir uv && \
    uv sync --no-dev

RUN mkdir -p /app/logs /app/history /app/.last_run

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

ENTRYPOINT ["python", "runner.py"]
