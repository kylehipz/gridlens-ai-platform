FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN groupadd --system app && useradd --system --gid app --home-dir /home/app --create-home app
WORKDIR /app
COPY pyproject.toml ./

FROM base AS dev
RUN pip install --no-cache-dir ".[dev]"
COPY workers/local-runtime-worker/src ./src
USER app
CMD ["python", "-m", "gridlens_local_runtime_worker.main"]

FROM base AS runtime
RUN pip install --no-cache-dir .
COPY workers/local-runtime-worker/src ./src
USER app
CMD ["python", "-m", "gridlens_local_runtime_worker.main"]
