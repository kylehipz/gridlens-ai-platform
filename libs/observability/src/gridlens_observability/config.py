import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ObservabilitySettings:
    mode: str = "test"
    log_exporter: str = "stdout"
    metrics_exporter: str = "noop"
    traces_exporter: str = "noop"
    otlp_endpoint: str | None = None
    service_name: str = "gridlens"
    smoke_routes_enabled: bool = False

    @property
    def is_local(self) -> bool:
        return self.mode == "local"

    @property
    def is_production(self) -> bool:
        return self.mode == "production"


def settings_from_env(environ: dict[str, str] | None = None) -> ObservabilitySettings:
    env = environ or os.environ
    mode = env.get("OBSERVABILITY_MODE", "test").lower()
    defaults = _defaults_for_mode(mode)
    return ObservabilitySettings(
        mode=mode,
        log_exporter=env.get("LOG_EXPORTER", defaults.log_exporter),
        metrics_exporter=env.get("METRICS_EXPORTER", defaults.metrics_exporter),
        traces_exporter=env.get("TRACES_EXPORTER", defaults.traces_exporter),
        otlp_endpoint=env.get("OTEL_EXPORTER_OTLP_ENDPOINT", defaults.otlp_endpoint),
        service_name=env.get("OTEL_SERVICE_NAME", "gridlens"),
        smoke_routes_enabled=_enabled(
            env.get("OBSERVABILITY_SMOKE_ROUTES_ENABLED"),
            default=defaults.smoke_routes_enabled,
        ),
    )


def _defaults_for_mode(mode: str) -> ObservabilitySettings:
    if mode == "local":
        return ObservabilitySettings(
            mode=mode,
            log_exporter="loki",
            metrics_exporter="prometheus",
            traces_exporter="tempo",
            otlp_endpoint="http://otel-collector:4318",
            smoke_routes_enabled=True,
        )
    if mode == "production":
        return ObservabilitySettings(
            mode=mode,
            log_exporter="stdout",
            metrics_exporter="otlp",
            traces_exporter="otlp",
            otlp_endpoint="http://localhost:4318",
        )
    return ObservabilitySettings(mode=mode)


def _enabled(raw: str | None, *, default: bool) -> bool:
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}
