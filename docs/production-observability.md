# Production Observability

GridLens application code should call the shared observability helpers for
logs, metrics, traces, FastAPI request instrumentation, queue propagation, and
worker jobs. Production deployments keep service code backend-neutral.
Application containers write structured JSON logs to stdout and emit OTLP
metrics and traces to an AWS Distro for OpenTelemetry (ADOT) collector sidecar.

The production exporter contract is tracked at
`infra/production/observability.env.example`:

```text
OBSERVABILITY_MODE=production
LOG_EXPORTER=stdout
METRICS_EXPORTER=otlp
TRACES_EXPORTER=otlp
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

Deployment tooling should provide AWS identity through the runtime environment,
such as task roles or workload identity. Do not inject static access keys into
Compose files, task definitions, images, tests, or documentation examples.

Expected ECS production routing:

- Structured JSON logs: stdout/stderr shipped to CloudWatch Logs by the ECS
  `awslogs` log driver.
- Metrics: OTLP HTTP to the ADOT sidecar, exported to CloudWatch metrics under
  `CLOUDWATCH_METRIC_NAMESPACE`.
- Traces: OTLP HTTP to the ADOT sidecar, exported to AWS X-Ray using the
  configured service name and resource attributes.

The same helper calls must work in all modes:

- `test`: no-op or in-memory exporters for offline tests.
- `local`: OTLP collector to Prometheus, Loki, Tempo, and Grafana.
- `production`: stdout logs plus OTLP metrics/traces to ADOT. Application code
  must not configure CloudWatch Logs or X-Ray exporters directly.

Production telemetry must follow the same safe-data rules as local telemetry:
redact account numbers, meter IDs, prompt text, source records, credentials,
tokens, signed URLs, SQL, nested exception details, and cross-tenant data before
values are logged, recorded as metric attributes, or attached to spans.
