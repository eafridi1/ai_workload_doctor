import unittest

from backends.contracts import (
    BackendCapabilities,
    BackendExecutionResult,
    ExecutionBackend,
    ExecutionRequest,
)


class ExampleBackend:
    """Minimal implementation used to test the interface."""

    def get_capabilities(self):
        return BackendCapabilities(
            backend_name="example",
            available=True,
            supported_operations=("benchmark",),
        )

    def execute(self, request):
        return BackendExecutionResult(
            backend_name="example",
            success=True,
            elapsed_seconds=0.01,
            output={"operation": request.operation},
        )


class TestBackendContract(unittest.TestCase):

    def test_backend_implements_interface(self):
        backend = ExampleBackend()
        self.assertIsInstance(backend, ExecutionBackend)

    def test_capabilities_are_returned(self):
        backend = ExampleBackend()
        capabilities = backend.get_capabilities()

        self.assertTrue(capabilities.available)
        self.assertIn("benchmark", capabilities.supported_operations)

    def test_execution_returns_standard_result(self):
        backend = ExampleBackend()
        request = ExecutionRequest(
            action_id="test-action-001",
            workload_path="sample_workload.py",
            operation="benchmark",
        )

        result = backend.execute(request)

        self.assertTrue(result.success)
        self.assertEqual(result.backend_name, "example")
        self.assertEqual(result.output["operation"], "benchmark")

    def test_unavailable_backend_requires_reason(self):
        with self.assertRaises(ValueError):
            BackendCapabilities(
                backend_name="amd-rocm",
                available=False,
            )

    def test_invalid_execution_timeout_is_rejected(self):
        with self.assertRaises(ValueError):
            ExecutionRequest(
                action_id="test-action-002",
                workload_path="sample_workload.py",
                operation="benchmark",
                timeout_seconds=0,
            )


if __name__ == "__main__":
    unittest.main()
