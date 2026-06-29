"""Worker entrypoints for the data operations service."""

from gridlens_data_operations_service.workers.main import readiness

__all__ = ["readiness"]
