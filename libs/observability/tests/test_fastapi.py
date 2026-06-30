import logging
from collections.abc import Awaitable, Callable

import httpx
from fastapi import FastAPI
from gridlens_observability import (
    InMemoryMetricExporter,
    InMemoryTraceExporter,
    instrument_fastapi_app,
    set_metric_exporter,
    set_trace_exporter,
    settings_from_env,
)

RequestRunner = Callable[[httpx.AsyncClient], Awaitable[httpx.Response]]


def run_request(app: FastAPI, request: RequestRunner) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await request(client)

    import asyncio

    return asyncio.run(run())


def test_fastapi_middleware_binds_request_context_and_records_signals(caplog) -> None:
    metrics = InMemoryMetricExporter()
    traces = InMemoryTraceExporter()
    set_metric_exporter(metrics)
    set_trace_exporter(traces)

    app = FastAPI()
    instrument_fastapi_app(app, service_name="test-service")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    with caplog.at_level(logging.INFO, logger="gridlens.test-service.http"):
        response = run_request(
            app,
            lambda client: client.get(
                "/health",
                headers={
                    "X-Request-ID": "req_test",
                    "X-Correlation-ID": "corr_test",
                    "X-Trace-ID": "trace_parent",
                    "X-Span-ID": "span_parent",
                },
            ),
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req_test"
    assert response.headers["X-Correlation-ID"] == "corr_test"

    log_record = next(
        record for record in caplog.records if record.getMessage() == "http_request_completed"
    )
    assert log_record.request_id == "req_test"
    assert log_record.correlation_id == "corr_test"
    assert log_record.trace_id == "trace_parent"
    assert log_record.service == "test-service"

    metric_names = [record.name for record in metrics.records()]
    assert "gridlens.http.server.duration" in metric_names
    assert "gridlens.http.server.requests" in metric_names
    assert metrics.records()[-1].attributes["request_id"] == "req_test"

    span = traces.records()[0]
    assert span.name == "http.server"
    assert span.trace_id == "trace_parent"
    assert span.parent_span_id == "span_parent"
    assert span.attributes["request_id"] == "req_test"


def test_fastapi_middleware_returns_correlated_safe_error_response(caplog) -> None:
    metrics = InMemoryMetricExporter()
    traces = InMemoryTraceExporter()
    set_metric_exporter(metrics)
    set_trace_exporter(traces)

    app = FastAPI()
    instrument_fastapi_app(app, service_name="test-service")

    @app.get("/fail")
    async def fail() -> None:
        raise RuntimeError("secret token=abc")

    with caplog.at_level(logging.INFO, logger="gridlens.test-service.http"):
        response = run_request(
            app, lambda client: client.get("/fail", headers={"X-Request-ID": "req_error"})
        )

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "req_error"
    assert response.json() == {
        "code": "internal_error",
        "message": "An unexpected error occurred.",
        "request_id": "req_error",
    }

    failure_record = next(
        record for record in caplog.records if record.getMessage() == "http_request_failed"
    )
    assert failure_record.request_id == "req_error"
    assert failure_record.error_type == "RuntimeError"
    assert failure_record.error_function == "fail"
    assert failure_record.error_module_path == "test_fastapi"
    assert failure_record.error_file_path.endswith("test_fastapi.py")
    assert isinstance(failure_record.error_line_no, int)
    assert failure_record.levelname == "ERROR"
    assert "secret token=abc" not in str(failure_record.__dict__)

    error_metrics = [
        record for record in metrics.records() if record.name == "gridlens.http.server.errors"
    ]
    assert error_metrics[0].attributes["request_id"] == "req_error"
    assert traces.records()[0].status == "error"


def test_local_smoke_routes_emit_visible_metrics(monkeypatch) -> None:
    metric_posts: list[str] = []

    class Response:
        def close(self) -> None:
            return None

    def capture_metric_post(request, timeout: float):
        metric_posts.append(request.full_url)
        return Response()

    monkeypatch.setenv("OBSERVABILITY_MODE", "local")
    monkeypatch.setenv("LOG_EXPORTER", "stdout")
    monkeypatch.setenv("TRACES_EXPORTER", "noop")
    monkeypatch.setattr("gridlens_observability.metrics.request.urlopen", capture_metric_post)

    app = FastAPI()
    instrument_fastapi_app(app, service_name="test-service")

    response = run_request(app, lambda client: client.get("/__observability/smoke"))
    assert response.status_code == 200
    assert response.json()["checks"] == ["log", "metric", "trace"]

    assert "http://otel-collector:4318/v1/metrics" in metric_posts
    metrics = run_request(app, lambda client: client.get("/metrics"))
    assert metrics.status_code == 404


def test_smoke_routes_can_be_forced_outside_local_mode(monkeypatch) -> None:
    monkeypatch.setenv("OBSERVABILITY_MODE", "test")
    monkeypatch.setenv("OBSERVABILITY_SMOKE_ROUTES_ENABLED", "true")
    settings = settings_from_env()
    assert settings.smoke_routes_enabled

    app = FastAPI()
    instrument_fastapi_app(app, service_name="test-service")
    response = run_request(app, lambda client: client.get("/__observability/fail"))
    assert response.status_code == 500
    assert response.json()["request_id"]
