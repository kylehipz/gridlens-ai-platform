# Local Development

This document defines the intended local development setup for GridLens. The
goal is to make day-to-day development reproducible while still exercising the
managed AWS services that materially affect product behavior.

## Development Posture

Local development should use Docker Compose for application runtime and local
stateful dependencies, while using AWS directly for managed cloud services that
are difficult to emulate accurately.

The local stack should run:

- Kong as the browser-facing API gateway for `/api/v1` traffic.
- API services.
- Background workers.
- PostgreSQL.
- Developer-facing support services needed by the app.

The local stack should use real AWS development resources for:

- Cognito.
- S3.
- SQS.
- Bedrock.

This keeps local service orchestration fast and repeatable without hiding
important behavior from authentication, object storage, queueing, and AI
provider integrations.

## AWS Credentials

Local containers should access AWS through the developer's existing AWS CLI
configuration. Do not hard-code AWS access keys in Compose files, `.env` files,
source code, tests, or documentation examples.

Use AWS SSO profiles for local development. A developer should authenticate on
the host before starting the stack:

```sh
aws sso login --profile gridlens-dev
```

Containers should receive:

- `AWS_PROFILE`, set to the local development profile name.
- `AWS_REGION`, set to the development AWS region.
- `AWS_SDK_LOAD_CONFIG=1`, so SDKs load profile configuration from
  `~/.aws/config`.

Mount the host AWS configuration into containers as read-only:

```yaml
services:
  api:
    environment:
      AWS_PROFILE: gridlens-dev
      AWS_REGION: ap-southeast-1
      AWS_SDK_LOAD_CONFIG: "1"
      HOME: /home/app
    volumes:
      - ${HOME}/.aws:/home/app/.aws:ro
```

Containers should run as a non-root application user where practical, and the
mounted path should match that user's home directory. If a container runs as
root, AWS SDKs will usually look under `/root/.aws`, which should be avoided for
normal development images.

AWS SSO credentials expire by design. When containers begin receiving
credential or token-expiration errors, refresh the host session with
`aws sso login --profile gridlens-dev` and restart affected containers if the
SDK does not recover automatically.

The SSO cache and AWS configuration are still sensitive local files. They must
not be copied into images, committed to the repository, printed in logs, or
included in test artifacts.

## AWS Resource Isolation

Local development should use a dedicated AWS development account where
possible. If shared accounts are used, local resources must be clearly scoped
with development prefixes, tags, and least-privilege IAM permissions.

Recommended local resource conventions:

- Use names such as `gridlens-dev-*` for buckets, queues, Cognito resources,
  and related infrastructure.
- Tag resources with `Project=GridLens` and `Environment=dev`.
- Use separate S3 prefixes or buckets for local development data.
- Use separate SQS queues and dead-letter queues for local development.
- Grant Bedrock model access only to the models needed by the development
  workflow.

Use synthetic data only. Do not upload real customer data, regulated data, or
production exports into development AWS resources.

## Dockerfile Stages

Each deployable service should use a multi-stage Dockerfile. At minimum, service
Dockerfiles should distinguish production/runtime images from development
images.

The development stage should:

- Install runtime dependencies.
- Install development dependencies such as test, lint, type-check, hot-reload,
  and debugger packages.
- Preserve source paths expected by bind mounts.
- Expose the service HTTP port and a debugger port.
- Use commands suitable for interactive local development through the
  Compose development overlay.

The production/runtime stage should:

- Install only runtime dependencies.
- Avoid development tools and debugger packages.
- Avoid mounting or baking local credentials.
- Use the same application entry point semantics expected in deployed
  environments.

Use a consistent stage name such as `dev` for development images so Compose
overlays can target services predictably:

```dockerfile
FROM base AS dev
# install dev dependencies and debugger tooling here

FROM base AS runtime
# install only runtime dependencies here
```

## Compose Files

The root `docker-compose.yml` should define the baseline local topology:

- Services.
- Kong in DB-less mode with a tracked declarative configuration.
- Workers.
- PostgreSQL.
- Shared networks.
- Persistent local volumes.
- Required environment variables with non-secret defaults.

Development-only behavior should live in `docker-compose.dev.yml`. The dev
overlay should override commands and image targets for local workflows without
changing the baseline topology.

The dev overlay should be used for:

- Building each service from the Dockerfile `dev` stage.
- Bind-mounting source code for hot reload.
- Running API services with hot-reload commands.
- Running workers with development logging and restart-friendly commands.
- Publishing debugger ports.
- Enabling development-only environment flags.

Expected usage:

```sh
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
make dev
```

Prefer the Makefile target for day-to-day work. `make down` stops containers and
preserves named volumes. `make reset-local-state` is the explicit destructive
reset path and removes local named volumes so PostgreSQL init scripts rerun on
the next startup.

## Kong Gateway

Kong owns the local browser-facing `/api/v1` ingress path. It runs in DB-less
mode from the tracked declarative file at `infra/local/kong/kong.yml`; no Kong
database container is required.

The local Compose service sets:

- `KONG_DATABASE=off`
- `KONG_DECLARATIVE_CONFIG=/kong/declarative/kong.yml`

Kong publishes the proxy on `127.0.0.1:${API_HOST_PORT:-8000}`. The admin API
is configured for loopback inside the container and is not published as a host
port by the Compose file. Gateway auth plugins, tenant enforcement, request
transformation, and rate limiting are deferred until policy workstreams add
them explicitly.

The active scaffold route is:

```text
GET /api/v1/health -> identity-tenant-service:8000/health
```

Use this target to run only the gateway path and its upstream API service:

```sh
make dev-gateway
curl http://127.0.0.1:${API_HOST_PORT:-8000}/api/v1/health
```

The expected response body is public-safe scaffold JSON:

```json
{"status":"ok","service":"identity-tenant-service"}
```

## First Run

From a fresh checkout:

```sh
make setup
make test
make dev
```

`make setup` creates the repo-local `.venv` and installs development
dependencies from `pyproject.toml`. Makefile Python targets use
`.venv/bin/python` by default.

## Frontend App

The Vite React TypeScript app lives under `frontend/`.

Run the browser app directly on the host:

```sh
make run-frontend
```

Run the frontend unit and component tests:

```sh
make test-frontend
```

The development sign-in stores only local scaffold session state in the browser.
It is not a security boundary; backend services remain responsible for
authentication, authorization, and tenant isolation.

Shared library checks are also available directly:

```sh
make test-contracts
make test-libs
```

These targets use fake adapters for S3-compatible storage, AI providers,
JWKS/Cognito validation, event queue messages, and tenant-aware repositories.
They must not require Docker, AWS credentials, active SSO, network access, or a
live PostgreSQL instance.

Copy `.env.example` to `.env` only when you need to override the public-safe
defaults. The Compose files already provide non-secret defaults for the
scaffold runtime.

`make dev` starts:

- PostgreSQL 16 with PGVector.
- Kong DB-less API gateway.
- All scaffolded FastAPI services.
- Implemented service-owned worker placeholders for data operations, assistant,
  program evaluation, and insights reporting.

The browser-facing API health endpoint is available through Kong at:

```sh
curl http://127.0.0.1:${API_HOST_PORT:-8000}/api/v1/health
```

Set `API_HOST_PORT` in `.env` to publish the API on a different host port.
The Kong proxy still listens on port `8000` inside the container, and each
upstream FastAPI service listens on port `8000` inside the Compose network.
Compose healthchecks and service routing use those internal ports.

For running just the identity tenant FastAPI process on the host without Kong:

```sh
make run-identity-tenant
curl http://127.0.0.1:8000/health
```

Stop the stack without deleting local database state:

```sh
make down
```

Remove local database state and force PostgreSQL init scripts to rerun on next
startup:

```sh
make reset-local-state
```

## PostgreSQL and PGVector

The local database uses a named Docker volume so data persists across
`make down`. On the first startup with an empty volume, scripts under
`infra/local/postgres/init/` create:

- the `gridlens_dev` local database;
- the `gridlens_app` local app role;
- the `app` schema;
- the `vector` PostgreSQL extension.

Verify PGVector:

```sh
docker compose -f docker-compose.yml exec -T postgres psql \
  -U gridlens \
  -d gridlens_dev \
  -c "select extname from pg_extension where extname = 'vector';"
```

The result should include exactly one `vector` row. With the stack running,
`make test-local-db` also verifies PostgreSQL connectivity, the `app` schema,
and the app role's ability to create and drop a smoke-test table.

PostgreSQL entrypoint scripts only run when the data volume is empty. If you
change init scripts or role defaults, run `make reset-local-state` before
starting the stack again.

## Managed AWS Development Resources

The local runtime is configured for managed development resources rather than
local AWS emulators. `.env.example` includes development-only placeholders for:

- Cognito user pool and client IDs.
- S3 artifact bucket.
- SQS job queue URL.
- Bedrock text and embedding model IDs.

Before running product code that calls AWS, authenticate on the host:

```sh
aws sso login --profile gridlens-dev
```

The scaffold FastAPI services and service workers do not call Cognito, S3, SQS, or
Bedrock during startup or default tests. AWS behavior in this foundation runtime
is limited to configuration and the read-only `~/.aws` mount contract.

## Debugging Ports

Each local service should expose a debugger port in the development overlay.
Debugger ports are for local development only and must not be exposed in
production images, production Compose examples, or deployed infrastructure.

Use predictable port assignments so developers can attach IDEs consistently.
For example:

| Component | HTTP port | Debug port |
|---|---:|---:|
| Kong proxy | 8000 | n/a |
| Identity tenant service | 8010 | 5680 |
| Data operations service | 8020 | 5681 |
| Assistant service | 8030 | 5682 |
| Program evaluation service | 8040 | 5683 |
| Insights reporting service | 8050 | 5684 |
| Governance service | 8060 | 5685 |
| Alerts anomalies service | 8070 | 5686 |
| Worker processes | n/a | Service-specific |

The local runtime publishes Kong on host port `8000` by default. Use
`API_HOST_PORT` to change the gateway host port without changing the container
listener. Service-specific debugger ports are deferred until debugger tooling is
added, but every service should have a documented debugger port and avoid
collisions with other local services when that happens.

## Local Observability

The Compose stack includes local-only observability backends:

- Grafana: `http://127.0.0.1:${GRAFANA_PORT:-3000}`
- Prometheus: `http://127.0.0.1:${PROMETHEUS_PORT:-9090}`
- Loki: `http://127.0.0.1:${LOKI_PORT:-3100}`
- Tempo: `http://127.0.0.1:${TEMPO_PORT:-3200}`
- OTLP collector HTTP endpoint: `http://127.0.0.1:${OTEL_HTTP_PORT:-4318}`

Application containers use the shared observability environment by default:

```text
OBSERVABILITY_MODE=local
LOG_EXPORTER=loki
METRICS_EXPORTER=prometheus
TRACES_EXPORTER=tempo
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
```

The collector configuration lives under `infra/local/observability/` and routes
OTLP metrics to Prometheus, logs to Loki, and traces to Tempo. Grafana
provisions Prometheus, Loki, and Tempo data sources automatically and loads the
minimal `GridLens Local Service Health` dashboard from the same directory.

For manual observability checks, local API services expose dev-only smoke
routes:

```sh
curl -H 'X-Request-ID: manual-req-1' \
  http://127.0.0.1:${API_HOST_PORT:-8000}/__observability/smoke
curl -H 'X-Request-ID: manual-req-2' \
  http://127.0.0.1:${API_HOST_PORT:-8000}/__observability/fail
```

`/__observability/smoke` emits a structured log, OTLP metrics, and a trace span
to the collector. `/__observability/fail` returns the standard safe error
envelope with the same request ID that appears in logs and traces. In Grafana,
use Prometheus for the smoke request metric exported by the collector, Loki for
`observability_smoke`, and Tempo for the returned `trace_id`.

Local telemetry must remain public-safe. Logs, metric labels, and span
attributes should use request, correlation, trace, service, route, tenant, and
job identifiers only after applying the shared redaction helpers. Do not emit
account numbers, meter IDs, prompt text, source rows, credentials, signed URLs,
or high-cardinality customer payloads as telemetry fields.

## Environment Variables

`.env.example` is the public-safe environment contract for local development.
It includes local PostgreSQL connection values, scaffold service ports, AWS SSO
profile settings, and development-only placeholders for managed Cognito, S3,
SQS, and Bedrock resources.

The default local runtime does not require MinIO, LocalStack, ElasticMQ, or
other AWS emulators. Endpoint override variables may be added later for explicit
testing needs, but they are not canonical local development defaults.

## Tests

Default tests run without network access and without AWS credentials:

```sh
make test
```

Integration tests that exercise Cognito, S3, SQS, or Bedrock should be marked as
live AWS tests and should require an explicit opt-in environment variable or
Makefile target. Live tests must use synthetic data and development resources
only.

Tests should not assume a developer has an active SSO session unless the test
target is explicitly documented as requiring AWS.

## Troubleshooting

### Expired AWS SSO Session

If later product code receives AWS credential or token-expiration errors,
refresh the host session:

```sh
aws sso login --profile gridlens-dev
```

Then restart affected containers if the SDK does not recover automatically:

```sh
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart identity-tenant-service data-operations-worker
```

### Stale Database Volume

If PGVector, roles, or schemas do not match the documented bootstrap state, the
database volume probably predates the current init scripts. Run:

```sh
make reset-local-state
make dev
```

### Missing AWS Config Directory

Compose mounts `${HOME}/.aws` into app containers as read-only. If the directory
does not exist, create it through normal AWS CLI setup on the host. Do not commit
that directory or copy it into images.

## Security Rules

- Do not commit secrets, static AWS access keys, SSO cache files, or generated
  credentials.
- Do not bake `$HOME/.aws` into Docker images.
- Mount AWS configuration read-only.
- Use least-privilege development IAM roles.
- Keep tenant isolation enforced server-side even in local development.
- Keep logs free of credentials, tokens, signed URLs, and sensitive payloads.
- Treat Bedrock prompts, retrieved context, and AI responses as tenant-scoped
  data.
