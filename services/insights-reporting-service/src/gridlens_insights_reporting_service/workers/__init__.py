"""Worker entrypoints for the insights reporting service."""

from gridlens_insights_reporting_service.workers.main import readiness

__all__ = ["readiness"]
