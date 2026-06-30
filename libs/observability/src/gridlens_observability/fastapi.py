import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from gridlens_contracts.errors import ErrorEnvelope
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .context import bind_context, clear_context
from .logging import json_log_record
from .metrics import counter, gauge, histogram
from .setup import configure_observability
from .tracing import TraceContext, extract_trace_context, start_span

REQUEST_ID_HEADER = "x-request-id"
CORRELATION_ID_HEADER = "x-correlation-id"
TRACE_ID_HEADER = "x-trace-id"
SPAN_ID_HEADER = "x-span-id"


class ObservabilityASGIMiddleware:
    def __init__(self, app: ASGIApp, *, service_name: str) -> None:
        self.app = app
        self.service_name = service_name
        self.logger = logging.getLogger(f"gridlens.{service_name}.http")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = _headers_from_scope(scope)
        request_id = headers.get(REQUEST_ID_HEADER) or uuid4().hex
        correlation_id = headers.get(CORRELATION_ID_HEADER) or request_id
        parent = _parent_trace_from_headers(headers)
        method = str(scope.get("method", ""))
        route = str(scope.get("path", ""))
        status_code = 500
        response_started = False
        started_at = perf_counter()
        span_context: TraceContext | None = None

        async def send_with_observability(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status_code = int(message["status"])
                raw_headers = list(message.get("headers", []))
                raw_headers.append((b"x-request-id", request_id.encode("utf-8")))
                raw_headers.append((b"x-correlation-id", correlation_id.encode("utf-8")))
                message["headers"] = raw_headers
            await send(message)

        bind_context(
            request_id=request_id,
            correlation_id=correlation_id,
            service=self.service_name,
        )
        try:
            try:
                with start_span(
                    "http.server",
                    parent=parent,
                    http_method=method,
                    http_route=route,
                    service=self.service_name,
                ) as active_span:
                    span_context = active_span
                    await self.app(scope, receive, send_with_observability)
            except Exception as exc:
                if response_started:
                    raise
                if span_context:
                    bind_context(trace_id=span_context.trace_id, span_id=span_context.span_id)
                counter(
                    "gridlens.http.server.errors",
                    service=self.service_name,
                    route=route,
                    method=method,
                    error_type=exc.__class__.__name__,
                )
                self.logger.exception(
                    json_log_record(
                        "http_request_failed",
                        status_code=status_code,
                        route=route,
                        method=method,
                        error_type=exc.__class__.__name__,
                    )
                )
                response = JSONResponse(
                    status_code=500,
                    content=ErrorEnvelope(
                        code="internal_error",
                        message="An unexpected error occurred.",
                        request_id=request_id,
                    ).to_dict(),
                )
                status_code = response.status_code
                await response(scope, receive, send_with_observability)

            if span_context:
                bind_context(trace_id=span_context.trace_id, span_id=span_context.span_id)

            duration_ms = (perf_counter() - started_at) * 1000
            histogram(
                "gridlens.http.server.duration",
                duration_ms,
                unit="ms",
                service=self.service_name,
                route=route,
                method=method,
                status_code=status_code,
            )
            counter(
                "gridlens.http.server.requests",
                service=self.service_name,
                route=route,
                method=method,
                status_code=status_code,
            )
            self.logger.info(
                json_log_record(
                    "http_request_completed",
                    status_code=status_code,
                    route=route,
                    method=method,
                    duration_ms=duration_ms,
                )
            )
        finally:
            clear_context()


def instrument_fastapi_app(app: FastAPI, *, service_name: str) -> FastAPI:
    settings = configure_observability(service_name=service_name)
    if settings.smoke_routes_enabled:
        _add_smoke_routes(app, service_name=service_name)
    app.add_middleware(ObservabilityASGIMiddleware, service_name=service_name)
    return app


def _add_smoke_routes(app: FastAPI, *, service_name: str) -> None:
    async def smoke() -> dict[str, object]:
        counter(
            "gridlens.observability.smoke.requests",
            service=service_name,
            route="/__observability/smoke",
        )
        histogram(
            "gridlens.observability.smoke.duration",
            1,
            unit="ms",
            service=service_name,
            route="/__observability/smoke",
        )
        gauge("gridlens.observability.smoke.gauge", 1, service=service_name)
        with start_span("observability.smoke", service=service_name) as span:
            json_log_record(
                "observability_smoke",
                service=service_name,
                route="/__observability/smoke",
                account_number="1234567890",
            )
            return {
                "status": "ok",
                "service": service_name,
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "checks": ["log", "metric", "trace"],
            }

    async def fail() -> None:
        counter(
            "gridlens.observability.smoke.failures",
            service=service_name,
            route="/__observability/fail",
        )
        json_log_record(
            "observability_smoke_failure",
            service=service_name,
            route="/__observability/fail",
            failure_category="manual_smoke",
            user_message="Manual observability failure smoke route.",
        )
        raise RuntimeError("manual observability smoke failure token=abc")

    app.add_api_route("/__observability/smoke", smoke, methods=["GET"], include_in_schema=False)
    app.add_api_route("/__observability/fail", fail, methods=["GET"], include_in_schema=False)


def _headers_from_scope(scope: Scope) -> dict[str, str]:
    return {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in scope.get("headers", [])
    }


def _parent_trace_from_headers(headers: dict[str, str]) -> TraceContext | None:
    return extract_trace_context(
        {
            "trace_id": headers.get(TRACE_ID_HEADER, ""),
            "span_id": headers.get(SPAN_ID_HEADER, ""),
        }
    )
