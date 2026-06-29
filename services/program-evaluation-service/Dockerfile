FROM python:3.14-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN groupadd --system app && useradd --system --gid app --home-dir /home/app --create-home app
WORKDIR /app
COPY pyproject.toml ./

FROM base AS dev
RUN pip install --no-cache-dir ".[dev]"
COPY services/program-evaluation-service/src ./src
USER app
EXPOSE 8000
CMD ["uvicorn", "gridlens_program_evaluation_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS runtime
RUN pip install --no-cache-dir .
COPY services/program-evaluation-service/src ./src
USER app
EXPOSE 8000
CMD ["uvicorn", "gridlens_program_evaluation_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
