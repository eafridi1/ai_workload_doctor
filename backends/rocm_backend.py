"""ROCm capability detection and execution backend."""

import re
import shutil
import subprocess

from backends.contracts import (
    BackendCapabilities,
    BackendExecutionResult,
    BackendUnavailableError,
    ExecutionRequest,
)


class ROCmExecutionBackend:
    """Detect ROCm GPU availability without executing workloads."""

    def __init__(self, detection_timeout: float = 10.0) -> None:
        if detection_timeout <= 0:
            raise ValueError("detection_timeout must be greater than zero.")

        self.detection_timeout = detection_timeout

    def get_capabilities(self) -> BackendCapabilities:
        """Detect an accessible AMD GPU using rocminfo."""

        rocminfo_path = shutil.which("rocminfo")

        if rocminfo_path is None:
            return BackendCapabilities(
                backend_name="amd-rocm",
                available=False,
                unavailable_reason="rocminfo is not installed or not in PATH.",
            )

        try:
            result = subprocess.run(
                [rocminfo_path],
                capture_output=True,
                text=True,
                timeout=self.detection_timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return BackendCapabilities(
                backend_name="amd-rocm",
                available=False,
                unavailable_reason="ROCm detection timed out.",
            )
        except OSError as exc:
            return BackendCapabilities(
                backend_name="amd-rocm",
                available=False,
                unavailable_reason=f"Unable to run rocminfo: {exc}",
            )

        if result.returncode != 0:
            return BackendCapabilities(
                backend_name="amd-rocm",
                available=False,
                unavailable_reason="rocminfo returned an error.",
            )

        gpu_match = re.search(
            r"\bName:\s*(gfx[0-9a-f]+)\b",
            result.stdout,
            re.IGNORECASE,
        )

        if gpu_match is None:
            return BackendCapabilities(
                backend_name="amd-rocm",
                available=False,
                unavailable_reason="No AMD GPU agent was detected by rocminfo.",
            )

        gpu_architecture = gpu_match.group(1)

        return BackendCapabilities(
            backend_name="amd-rocm",
            available=True,
            supported_operations=(),
            device_name=f"AMD GPU ({gpu_architecture})",
            runtime_version=None,
        )

    def execute(
        self,
        request: ExecutionRequest,
    ) -> BackendExecutionResult:
        """Reject execution until the real ROCm executor is implemented."""

        capabilities = self.get_capabilities()

        if not capabilities.available:
            raise BackendUnavailableError(
                capabilities.unavailable_reason
            )

        raise BackendUnavailableError(
            "ROCm hardware was detected, but actual workload execution "
            "has not been implemented."
        )
