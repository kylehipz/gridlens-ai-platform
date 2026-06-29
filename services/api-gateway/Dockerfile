FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN groupadd --system app && useradd --system --gid app --home-dir /home/app --create-home app
WORKDIR /app
COPY src ./src

FROM base AS dev
RUN pip install --no-cache-dir "debugpy>=1.8,<2"
COPY devtools ./devtools
USER app
EXPOSE 8000 5678
CMD ["python", "-m", "gridlens_api_gateway.main"]

FROM base AS runtime
USER app
EXPOSE 8000
CMD ["python", "-m", "gridlens_api_gateway.main"]
