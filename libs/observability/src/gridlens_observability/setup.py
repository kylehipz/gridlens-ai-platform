from .config import ObservabilitySettings, settings_from_env
from .logging import OtlpLogExporter, set_log_exporter
from .metrics import OtlpMetricExporter, set_metric_exporter
from .tracing import OtlpTraceExporter, set_trace_exporter


def configure_observability(
    *, service_name: str, environ: dict[str, str] | None = None
) -> ObservabilitySettings:
    settings = settings_from_env(environ)
    endpoint = settings.otlp_endpoint

    if endpoint and settings.metrics_exporter == "prometheus":
        set_metric_exporter(OtlpMetricExporter(endpoint, service_name=service_name))
    if endpoint and settings.log_exporter == "loki":
        set_log_exporter(OtlpLogExporter(endpoint, service_name=service_name))
    if endpoint and settings.traces_exporter == "tempo":
        set_trace_exporter(OtlpTraceExporter(endpoint, service_name=service_name))

    return settings
