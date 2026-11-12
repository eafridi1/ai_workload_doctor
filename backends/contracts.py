"""Shared contracts for workload execution backends.

This module defines interfaces and data structures only.
It does not execute workloads or detect hardware.
"""

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable


@dataclass(frozen=True)
class BackendCapabilities:
    """Describe what an execution backend can currently support."""

    backend_name: str
    available: bool
    supported_operations: tuple[str, ...] = ()
    device_name: str | None = None
    runtime_version: str | None = None
    unavailable_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.backend_name.strip():
            raise ValueError("backend_name cannot be empty.")

        if not self.available and not self.unavailable_reason:
            raise ValueError(
                "An unavailable backend must provide unavailable_reason."
            )


@dataclass(frozen=True)
class ExecutionRequest:
    """A structured request to run a supported workload operation."""

    action_id: str
    workload_path: str
    operation: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if not self.action_id.strip():
            raise ValueError("action_id cannot be empty.")

        if not self.workload_path.strip():
            raise ValueError("workload_path cannot be empty.")

        if not self.operation.strip():
            raise ValueError("operation cannot be empty.")

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")

        object.__setattr__(
            self,
            "parameters",
            dict(self.parameters),
        )


@dataclass(frozen=True)
class BackendExecutionResult:
    """Standardized result returned by an execution backend."""

    backend_name: str
    success: bool
    elapsed_seconds: float
    output: Mapping[str, Any] = field(default_factory=dict)
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.backend_name.strip():
            raise ValueError("backend_name cannot be empty.")

        if self.elapsed_seconds < 0:
            raise ValueError("elapsed_seconds cannot be negative.")

        if self.success and self.error is not None:
            raise ValueError(
                "A successful result cannot contain an error."
            )

        object.__setattr__(self, "output", dict(self.output))
        object.__setattr__(self, "metadata", dict(self.metadata))


class BackendError(RuntimeError):
    """Base exception for backend-related failures."""


class BackendUnavailableError(BackendError):
    """Raised when a backend cannot perform the requested operation."""


class BackendExecutionError(BackendError):
    """Raised when a backend fails while executing a request."""


@runtime_checkable
class ExecutionBackend(Protocol):
    """Interface every workload execution backend must implement.

    Governance approval must be checked by the calling pipeline before
    execute() is called. A backend is not an authorization component.
    """

    def get_capabilities(self) -> BackendCapabilities:
        """Return current backend availability and supported operations."""
        ...

    def execute(
        self,
        request: ExecutionRequest,
    ) -> BackendExecutionResult:
        """Execute one supported, structured workload operation."""
        ...
