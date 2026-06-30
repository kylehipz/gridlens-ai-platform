import json
import logging
from datetime import UTC, datetime
from inspect import currentframe
from types import TracebackType
from typing import Any, TypedDict
from weakref import WeakSet

from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from .context import bind_context, clear_context, current_context_fields, reset_context
from .redaction import redact_field, redact_value

RESERVED_LOG_RECORD_ATTRS = frozenset(logging.makeLogRecord({}).__dict__) | {
    "message",
    "asctime",
    "level",
}
_JSON_LOG_HANDLERS: WeakSet[logging.Handler] = WeakSet()
_OTEL_LOG_HANDLERS: WeakSet[logging.Handler] = WeakSet()


class LogExtraKwargs(TypedDict):
    extra: dict[str, Any]


class GridlensLogRecordFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.level = _normalize_level(record.levelname)
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        extra_fields = _extra_fields(record)
        extra_fields.setdefault("source_module", record.module)
        extra_fields.setdefault("source_function", record.funcName)
        extra_fields.setdefault("source_line_no", record.lineno)
        payload = _uvicorn_access_record(record) or structured_record(
            record.getMessage(),
            level=record.levelname.lower(),
            logger=record.name,
            timestamp=datetime.fromtimestamp(record.created, UTC).isoformat(),
            include_source=False,
            **extra_fields,
        )
        if record.exc_info and record.exc_info[0]:
            payload["exception_type"] = record.exc_info[0].__name__
            payload.update(exception_source_fields(record.exc_info[2]))
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def configure_json_logging(
    level: int = logging.INFO, *, uvicorn_access_log_enabled: bool = False
) -> None:
    handler = logging.StreamHandler()
    handler.addFilter(GridlensLogRecordFilter())
    handler.setFormatter(JsonFormatter())
    _JSON_LOG_HANDLERS.add(handler)
    root = logging.getLogger()
    root.handlers = [
        existing
        for existing in root.handlers
        if _keep_existing_root_handler(existing)
    ]
    root.handlers.append(handler)
    root.setLevel(level)
    _configure_library_loggers(level, uvicorn_access_log_enabled=uvicorn_access_log_enabled)


def configure_otel_logging(*, endpoint: str, service_name: str, level: int = logging.NOTSET) -> None:
    root = logging.getLogger()
    root.handlers = [
        existing
        for existing in root.handlers
        if not is_gridlens_otel_handler(existing)
    ]
    provider = LoggerProvider(
        resource=Resource.create({"service.name": service_name}),
    )
    provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(endpoint=f"{endpoint.rstrip('/')}/v1/logs"),
        )
    )
    handler = LoggingHandler(level=level, logger_provider=provider)
    handler.addFilter(GridlensLogRecordFilter())
    _OTEL_LOG_HANDLERS.add(handler)
    root.addHandler(handler)


def log_extra(**fields: Any) -> LogExtraKwargs:
    extra = structured_record("", **fields, include_source=True, include_message=False)
    extra.pop("level", None)
    return {"extra": extra}


def is_gridlens_json_handler(handler: logging.Handler) -> bool:
    return handler in _JSON_LOG_HANDLERS


def is_gridlens_otel_handler(handler: logging.Handler) -> bool:
    return handler in _OTEL_LOG_HANDLERS


def structured_record(
    message: str,
    *,
    level: str = "info",
    include_source: bool = True,
    include_message: bool = True,
    **fields: Any,
) -> dict[str, Any]:
    record = current_context_fields()
    record.update({key: redact_field(key, value) for key, value in fields.items()})
    if include_source:
        record.update(_caller_source_fields())
    record["level"] = _normalize_level(level)
    if include_message:
        record["message"] = message
    return record


def exception_source_fields(traceback_obj: TracebackType | None) -> dict[str, int | str]:
    if traceback_obj is None:
        return {}
    current = traceback_obj
    while current.tb_next is not None:
        current = current.tb_next
    frame = current.tb_frame
    return {
        "error_module_path": frame.f_globals.get("__name__", ""),
        "error_file_path": frame.f_code.co_filename,
        "error_function": frame.f_code.co_name,
        "error_line_no": current.tb_lineno,
    }


def _extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    return {
        key: redact_field(key, value)
        for key, value in record.__dict__.items()
        if key not in RESERVED_LOG_RECORD_ATTRS and value is not None
    }


def _caller_source_fields() -> dict[str, int | str]:
    frame = currentframe()
    if frame is None:
        return {}
    caller = frame.f_back
    while caller is not None and caller.f_globals.get("__name__") == __name__:
        caller = caller.f_back
    if caller is None:
        return {}
    return {
        "source_module": caller.f_globals.get("__name__", ""),
        "source_function": caller.f_code.co_name,
        "source_line_no": caller.f_lineno,
    }


def _uvicorn_access_record(record: logging.LogRecord) -> dict[str, Any] | None:
    args = record.args
    if record.name != "uvicorn.access" or not isinstance(args, tuple) or len(args) < 5:
        return None
    client_addr, method, path, http_version, status_code = args[:5]
    return structured_record(
        "http_access",
        level=record.levelname.lower(),
        logger=record.name,
        client_addr=client_addr,
        method=method,
        route=path,
        http_version=http_version,
        status_code=status_code,
        source_module=record.module,
        source_function=record.funcName,
        source_line_no=record.lineno,
        timestamp=datetime.fromtimestamp(record.created, UTC).isoformat(),
        include_source=False,
    )


def _keep_existing_root_handler(handler: logging.Handler) -> bool:
    if is_gridlens_json_handler(handler):
        return False
    if is_gridlens_otel_handler(handler):
        return True
    return _is_pytest_handler(handler)


def _is_pytest_handler(handler: logging.Handler) -> bool:
    return handler.__class__.__module__.startswith("_pytest.")


def _configure_library_loggers(level: int, *, uvicorn_access_log_enabled: bool) -> None:
    for logger_name in ("uvicorn", "uvicorn.error", "fastapi"):
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.propagate = True
        logger.setLevel(level)
        logger.disabled = False

    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers = []
    access_logger.propagate = uvicorn_access_log_enabled
    access_logger.disabled = not uvicorn_access_log_enabled
    access_logger.setLevel(level)


def _normalize_level(level: object) -> str:
    normalized = str(level).lower()
    if normalized in {"debug", "info", "warning", "error", "critical"}:
        return normalized
    if normalized == "warn":
        return "warning"
    if normalized in {"fatal", "exception"}:
        return "error"
    return "info"


__all__ = [
    "JsonFormatter",
    "GridlensLogRecordFilter",
    "bind_context",
    "clear_context",
    "configure_json_logging",
    "configure_otel_logging",
    "exception_source_fields",
    "is_gridlens_json_handler",
    "is_gridlens_otel_handler",
    "log_extra",
    "redact_value",
    "reset_context",
    "structured_record",
]
