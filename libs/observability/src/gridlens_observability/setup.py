from .config import ObservabilitySettings, settings_from_env
from .logging import configure_json_logging, configure_otel_logging
from .metrics import configure_otel_metrics
from .tracing import configure_otel_tracing


def configure_observability(
    *, service_name: str, environ: dict[str, str] | None = None
) -> ObservabilitySettings:
    settings = settings_from_env(environ)
    endpoint = settings.otlp_endpoint
    configure_json_logging()

    if endpoint and settings.metrics_exporter in {"prometheus", "otlp"}:
        configure_otel_metrics(endpoint=endpoint, service_name=service_name)
    if endpoint and settings.log_exporter == "loki":
        configure_otel_logging(endpoint=endpoint, service_name=service_name)
    if endpoint and settings.traces_exporter in {"tempo", "otlp"}:
        configure_otel_tracing(endpoint=endpoint, service_name=service_name)

    return settings
