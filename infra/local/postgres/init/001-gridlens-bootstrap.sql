\set ON_ERROR_STOP on

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gridlens_migrator') THEN
    CREATE ROLE gridlens_migrator LOGIN PASSWORD 'gridlens_migrator_local';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gridlens_app') THEN
    CREATE ROLE gridlens_app LOGIN PASSWORD 'gridlens_app_local';
  END IF;
END
$$;

CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION gridlens_migrator;

DO $$
BEGIN
  EXECUTE format('GRANT CONNECT ON DATABASE %I TO gridlens_migrator', current_database());
  EXECUTE format('GRANT CONNECT ON DATABASE %I TO gridlens_app', current_database());
END
$$;

GRANT USAGE, CREATE ON SCHEMA app TO gridlens_migrator;
GRANT USAGE ON SCHEMA app TO gridlens_app;

ALTER ROLE gridlens_migrator SET search_path = app, public;
ALTER ROLE gridlens_app SET search_path = app, public;

ALTER DEFAULT PRIVILEGES FOR ROLE gridlens_migrator IN SCHEMA app
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO gridlens_app;

ALTER DEFAULT PRIVILEGES FOR ROLE gridlens_migrator IN SCHEMA app
  GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO gridlens_app;
