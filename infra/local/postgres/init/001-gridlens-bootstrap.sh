#!/usr/bin/env bash
set -euo pipefail

: "${POSTGRES_DB:=gridlens_dev}"
: "${GRIDLENS_APP_USER:=gridlens_app}"
: "${GRIDLENS_APP_PASSWORD:=gridlens_app_local}"

case "${GRIDLENS_APP_USER}" in
  ""|*[!A-Za-z0-9_]*)
    echo "GRIDLENS_APP_USER must contain only letters, numbers, and underscores" >&2
    exit 1
    ;;
esac

case "${GRIDLENS_APP_PASSWORD}" in
  ""|*"'"*)
    echo "GRIDLENS_APP_PASSWORD must be non-empty and must not contain single quotes" >&2
    exit 1
    ;;
esac

psql --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${GRIDLENS_APP_USER}') THEN
    CREATE ROLE "${GRIDLENS_APP_USER}" LOGIN PASSWORD '${GRIDLENS_APP_PASSWORD}';
  END IF;
END
\$\$;

CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION "${GRIDLENS_APP_USER}";

GRANT CONNECT ON DATABASE "${POSTGRES_DB}" TO "${GRIDLENS_APP_USER}";
GRANT USAGE, CREATE ON SCHEMA app TO "${GRIDLENS_APP_USER}";
ALTER ROLE "${GRIDLENS_APP_USER}" SET search_path = app, public;
SQL
