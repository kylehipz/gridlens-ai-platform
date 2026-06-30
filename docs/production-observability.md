# Production Observability

GridLens application code should call the shared observability helpers for
logs, metrics, traces, FastAPI request instrumentation, queue propagation, and
worker jobs. Production deployments select AWS exporters through environment
configuration, not through service-specific call sites.

The production exporter contract is tracked at
`infra/production/observability.env.example`:

```text
OBSERVABILITY_MODE=production
LOG_EXPORTER=cloudwatch-logs
METRICS_EXPORTER=cloudwatch
TRACES_EXPORTER=xray
```

Deployment tooling should provide AWS identity through the runtime environment,
such as task roles or workload identity. Do not inject static access keys into
Compose files, task definitions, images, tests, or documentation examples.

Expected AWS targets:

- Structured JSON logs: CloudWatch Logs.
- Metrics: CloudWatch metrics under `CLOUDWATCH_METRIC_NAMESPACE`.
- Traces: AWS X-Ray using the configured service name and resource attributes.

The same helper calls must work in all modes:

- `test`: no-op or in-memory exporters for offline tests.
- `local`: OTLP collector to Prometheus, Loki, Tempo, and Grafana.
- `production`: CloudWatch Logs, CloudWatch metrics, and X-Ray exporters.

Production telemetry must follow the same safe-data rules as local telemetry:
redact account numbers, meter IDs, prompt text, source records, credentials,
tokens, signed URLs, SQL, nested exception details, and cross-tenant data before
values are logged, recorded as metric attributes, or attached to spans.
