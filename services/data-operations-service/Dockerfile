FROM python:3.14-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app/libs/auth/src:/app/libs/contracts/src:/app/libs/db/src:/app/libs/observability/src

RUN groupadd --system app && useradd --system --gid app --home-dir /home/app --create-home app
WORKDIR /app
COPY pyproject.toml ./

FROM base AS dev
RUN pip install --no-cache-dir ".[dev]"
COPY services/data-operations-service/src ./src
COPY libs/auth/src ./libs/auth/src
COPY libs/contracts/src ./libs/contracts/src
COPY libs/db/src ./libs/db/src
COPY libs/observability/src ./libs/observability/src
USER app
EXPOSE 8000
CMD ["uvicorn", "gridlens_data_operations_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS runtime
RUN pip install --no-cache-dir .
COPY services/data-operations-service/src ./src
COPY libs/auth/src ./libs/auth/src
COPY libs/contracts/src ./libs/contracts/src
COPY libs/db/src ./libs/db/src
COPY libs/observability/src ./libs/observability/src
USER app
EXPOSE 8000
CMD ["uvicorn", "gridlens_data_operations_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
