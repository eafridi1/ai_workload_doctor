"""Workload execution backend interfaces and implementations."""

from backends.contracts import (
    BackendCapabilities,
    BackendError,
    BackendExecutionError,
    BackendExecutionResult,
    BackendUnavailableError,
    ExecutionBackend,
    ExecutionRequest,
)
from backends.mock_backend import MockExecutionBackend

__all__ = [
    "BackendCapabilities",
    "BackendError",
    "BackendExecutionError",
    "BackendExecutionResult",
    "BackendUnavailableError",
    "ExecutionBackend",
    "ExecutionRequest",
    "MockExecutionBackend",
]
