# GridLens Observability

`gridlens_observability` is the application-facing observability API for
GridLens services and workers. Service code should use these helpers instead of
calling Prometheus, Loki, CloudWatch, X-Ray, or OpenTelemetry SDKs directly.

## Context Fields

Bind context at request, queue, worker, and audit boundaries:

- `request_id`: user-visible request identifier returned in API error responses.
- `correlation_id`: workflow identifier shared across service, queue, worker,
  and audit records.
- `trace_id` and `span_id`: distributed trace identifiers.
- `tenant_id`: tenant identifier after server-side authorization.
- `actor_id`: authenticated user, system actor, or worker actor.
- `service`: emitting service name.
- `worker`: worker process name when applicable.
- `job_id`: background job identifier when applicable.

Use `bind_context`, `clear_context`, and `reset_context` for manual context
management. `instrument_fastapi_app` and `observe_worker_job` bind and clear
context automatically for HTTP requests and worker jobs.

## Logs

Use `structured_record` or `json_log_record` for JSON logs. Required fields for
request logs are:

- `message`
- `request_id`
- `correlation_id`
- `trace_id`
- `span_id`
- `service`
- `method`
- `route`
- `status_code`
- `duration_ms`

Worker failure logs must include:

- `message=worker_job_failed`
- `job_id`
- `tenant_id`
- `correlation_id`
- `request_id` when available
- `trace_id` and `span_id` when available
- `failure_category`
- `user_message`
- `error_type`

Do not log raw exception messages when they may contain secrets or tenant data.
Use a user-safe message and keep raw diagnostics out of structured payloads.

## Metrics

Record metrics through the facade functions:

- `counter(name, value=1, **attributes)`
- `histogram(name, value, unit=None, **attributes)`
- `gauge(name, value, unit=None, **attributes)`

Current standard metric names:

- `gridlens.http.server.requests`
- `gridlens.http.server.duration`
- `gridlens.http.server.errors`
- `gridlens.worker.job.duration`
- `gridlens.worker.job.errors`

Future features should keep labels low-cardinality. Allowed metric attributes
include service, worker, route template, HTTP method, status code, failure
category, queue name, model family, and bounded status values. Do not use
account numbers, meter IDs, prompt text, source records, object keys, signed
URLs, SQL, or raw tenant payloads as metric labels.

## Traces

Use `start_span`, `inject_trace_context`, and `extract_trace_context` to create
and propagate spans. Required span attributes follow the same safe-data rules as
metrics. Current standard spans are:

- `http.server` for FastAPI request handling.
- `worker.consume` for worker message processing.

Queue messages should carry `request_id`, `correlation_id`, `trace_id`, and
`span_id` attributes. Worker helpers bind those attributes before logging or
recording metrics.

## Redaction

All logs, metrics, and spans pass through shared redaction helpers. These
helpers mask account-like numbers such as `1234567890` as `******7890`, strip
bearer tokens and signed URLs, and replace common secret fields such as
`token`, `authorization`, `api_key`, `password`, `secret`, and `credential`.

Never emit:

- Account numbers or meter IDs.
- Prompt text, retrieved context, source rows, generated answers, or citations
  containing tenant data.
- Credentials, tokens, passwords, API keys, signed URLs, or SSO cache values.
- SQL text, stack traces, nested exception details, or provider payloads.
- Cross-tenant identifiers or payloads.

## Exporter Modes

Exporter selection is environment-driven through `settings_from_env`:

- `OBSERVABILITY_MODE=test`: no-op or in-memory exporters for offline tests.
- `OBSERVABILITY_MODE=local`: Prometheus, Loki, Tempo, and Grafana through the
  local OTLP collector.
- `OBSERVABILITY_MODE=production`: CloudWatch metrics, CloudWatch Logs, and
  X-Ray through deployment configuration.

The local stack is documented in `docs/local-development.md`. Production
settings are documented in `docs/production-observability.md` and
`infra/production/observability.env.example`.
