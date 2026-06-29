FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN groupadd --system app && useradd --system --gid app --home-dir /home/app --create-home app
WORKDIR /app
COPY src ./src
USER app

FROM base AS dev
EXPOSE 8000 5678
CMD ["python", "-m", "gridlens_api_gateway.main"]

FROM base AS runtime
EXPOSE 8000
CMD ["python", "-m", "gridlens_api_gateway.main"]
