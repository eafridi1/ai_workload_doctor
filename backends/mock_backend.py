"""Mock workload execution backend.

Simulates structured execution requests for local development.
It does not execute workload code or access GPU hardware.
"""

from backends.contracts import (
    BackendCapabilities,
    BackendExecutionResult,
    BackendUnavailableError,
    ExecutionRequest,
)


class MockExecutionBackend:
    """Simulated backend implementing the shared execution contract."""

    def __init__(
        self,
        supported_operations: tuple[str, ...] = ("benchmark",),
    ) -> None:
        if not supported_operations:
            raise ValueError("At least one supported operation is required.")

        self.supported_operations = tuple(supported_operations)

    def get_capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            backend_name="mock",
            available=True,
            supported_operations=self.supported_operations,
            device_name="Mock Execution Environment",
            runtime_version="mock-1.0",
        )

    def execute(
        self,
        request: ExecutionRequest,
    ) -> BackendExecutionResult:
        """Return a simulated result without executing workload code."""

        if request.operation not in self.supported_operations:
            raise BackendUnavailableError(
                f"Mock backend does not support operation: "
                f"{request.operation}"
            )

        return BackendExecutionResult(
            backend_name="mock",
            success=True,
            elapsed_seconds=0.0,
            output={
                "action_id": request.action_id,
                "workload_path": request.workload_path,
                "operation": request.operation,
                "parameters": dict(request.parameters),
                "execution_mode": "simulation",
            },
            metadata={
                "simulated": True,
                "hardware_accelerated": False,
                "timing_measured": False,
                "note": "No actual workload execution or benchmarking occurred.",
            },
        )
