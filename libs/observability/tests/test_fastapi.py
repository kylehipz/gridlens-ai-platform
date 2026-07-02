import logging
from collections.abc import Awaitable, Callable

import httpx
from fastapi import FastAPI, Request
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

    @app.get("/ready")
    async def ready(request: Request) -> dict[str, str]:
        return {
            "status": "ok",
            "request_id": request.state.request_id,
            "correlation_id": request.state.correlation_id,
        }

    with caplog.at_level(logging.INFO, logger="gridlens.test-service.http"):
        response = run_request(
            app,
            lambda client: client.get(
                "/ready",
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
    assert response.json()["request_id"] == "req_test"
    assert response.json()["correlation_id"] == "corr_test"

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


def test_fastapi_middleware_suppresses_health_completion_logs(caplog) -> None:
    metrics = InMemoryMetricExporter()
    traces = InMemoryTraceExporter()
    set_metric_exporter(metrics)
    set_trace_exporter(traces)

    app = FastAPI()
    instrument_fastapi_app(app, service_name="test-service")

    @app.get("/health")
    async def health(request: Request) -> dict[str, str]:
        return {"status": "ok", "request_id": request.state.request_id}

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    with caplog.at_level(logging.INFO, logger="gridlens.test-service.http"):
        health_response = run_request(
            app, lambda client: client.get("/health", headers={"X-Request-ID": "req_health"})
        )
        healthz_response = run_request(
            app, lambda client: client.get("/healthz", headers={"X-Request-ID": "req_healthz"})
        )

    assert health_response.status_code == 200
    assert health_response.headers["X-Request-ID"] == "req_health"
    assert healthz_response.status_code == 200
    assert healthz_response.headers["X-Request-ID"] == "req_healthz"
    assert not [
        record for record in caplog.records if record.getMessage() == "http_request_completed"
    ]
    assert [
        record
        for record in metrics.records()
        if record.name == "gridlens.http.server.requests" and record.attributes["route"] == "/health"
    ]
    assert [
        record
        for record in metrics.records()
        if record.name == "gridlens.http.server.requests" and record.attributes["route"] == "/healthz"
    ]
    assert len(traces.records()) == 2


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
    metrics = InMemoryMetricExporter()

    def capture_metric_exporter(*, endpoint: str, service_name: str) -> None:
        assert endpoint == "http://otel-collector:4318"
        assert service_name == "test-service"
        set_metric_exporter(metrics)

    monkeypatch.setenv("OBSERVABILITY_MODE", "local")
    monkeypatch.setenv("LOG_EXPORTER", "stdout")
    monkeypatch.setenv("TRACES_EXPORTER", "noop")
    monkeypatch.setattr(
        "gridlens_observability.setup.configure_otel_metrics",
        capture_metric_exporter,
    )

    app = FastAPI()
    instrument_fastapi_app(app, service_name="test-service")

    response = run_request(app, lambda client: client.get("/__observability/smoke"))
    assert response.status_code == 200
    assert response.json()["checks"] == ["log", "metric", "trace"]

    assert "gridlens.observability.smoke.requests" in [
        record.name for record in metrics.records()
    ]
    metrics_response = run_request(app, lambda client: client.get("/metrics"))
    assert metrics_response.status_code == 404


def test_smoke_response_trace_id_matches_recorded_route_and_http_spans(monkeypatch) -> None:
    traces = InMemoryTraceExporter()
    set_trace_exporter(traces)
    monkeypatch.setenv("OBSERVABILITY_MODE", "test")
    monkeypatch.setenv("OBSERVABILITY_SMOKE_ROUTES_ENABLED", "true")

    app = FastAPI()
    instrument_fastapi_app(app, service_name="test-service")

    response = run_request(app, lambda client: client.get("/__observability/smoke"))

    assert response.status_code == 200
    trace_id = response.json()["trace_id"]
    records = traces.records()
    assert [record.name for record in records] == ["observability.smoke", "http.server"]
    assert {record.trace_id for record in records} == {trace_id}
    assert records[1].span_id == records[0].parent_span_id


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
