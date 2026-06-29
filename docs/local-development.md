# Local Development

This document defines the intended local development setup for GridLens. The
goal is to make day-to-day development reproducible while still exercising the
managed AWS services that materially affect product behavior.

## Development Posture

Local development should use Docker Compose for application runtime and local
stateful dependencies, while using AWS directly for managed cloud services that
are difficult to emulate accurately.

The local stack should run:

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
```

When stable Makefile targets exist, prefer wrapping this command in a documented
target such as `make dev`.

## Debugging Ports

Each local service should expose a debugger port in the development overlay.
Debugger ports are for local development only and must not be exposed in
production images, production Compose examples, or deployed infrastructure.

Use predictable port assignments so developers can attach IDEs consistently.
For example:

| Component | HTTP port | Debug port |
|---|---:|---:|
| API gateway | 8000 | 5678 |
| Identity service | 8010 | 5680 |
| Data operations service | 8020 | 5681 |
| Assistant service | 8030 | 5682 |
| Evaluation service | 8040 | 5683 |
| Reporting service | 8050 | 5684 |
| Worker processes | n/a | Service-specific |

The first local runtime publishes the scaffolded API on port `8000`, the API
debugger on port `5678`, and the worker debugger on port `5679`. Exact ports for
later services may change as implementation begins, but every service should
have a documented debugger port and avoid collisions with other local services.

## Environment Variables

`.env.example` is the public-safe environment contract for local development.
It includes local PostgreSQL connection values, scaffold service ports, AWS SSO
profile settings, and development-only placeholders for managed Cognito, S3,
SQS, and Bedrock resources.

The default local runtime does not require MinIO, LocalStack, ElasticMQ, or
other AWS emulators. Endpoint override variables may be added later for explicit
testing needs, but they are not canonical local development defaults.

## Tests

Unit tests should run without network access and without AWS credentials.

Integration tests that exercise Cognito, S3, SQS, or Bedrock should be marked as
live AWS tests and should require an explicit opt-in environment variable or
Makefile target. Live tests must use synthetic data and development resources
only.

Tests should not assume a developer has an active SSO session unless the test
target is explicitly documented as requiring AWS.

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
