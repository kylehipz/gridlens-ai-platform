FROM python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/libs/db/src

RUN groupadd --system app && useradd --system --gid app --home-dir /home/app --create-home app
WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY libs/db/src ./libs/db/src
COPY infra/db/alembic.ini ./infra/db/alembic.ini
COPY infra/db/alembic ./infra/db/alembic

USER app
CMD ["python", "-m", "alembic", "-c", "infra/db/alembic.ini", "upgrade", "head"]
