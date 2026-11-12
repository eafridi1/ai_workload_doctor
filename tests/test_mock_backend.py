import unittest

from backends import (
    BackendUnavailableError,
    ExecutionBackend,
    ExecutionRequest,
    MockExecutionBackend,
)


class TestMockExecutionBackend(unittest.TestCase):

    def setUp(self):
        self.backend = MockExecutionBackend()

        self.request = ExecutionRequest(
            action_id="mock-test-001",
            workload_path="sample_workload.py",
            operation="benchmark",
            parameters={"iterations": 10},
        )

    def test_backend_implements_interface(self):
        self.assertIsInstance(self.backend, ExecutionBackend)

    def test_backend_capabilities(self):
        capabilities = self.backend.get_capabilities()

        self.assertEqual(capabilities.backend_name, "mock")
        self.assertTrue(capabilities.available)
        self.assertIn("benchmark", capabilities.supported_operations)

    def test_execution_returns_success(self):
        result = self.backend.execute(self.request)

        self.assertTrue(result.success)
        self.assertEqual(result.backend_name, "mock")
        self.assertEqual(result.output["action_id"], "mock-test-001")

    def test_execution_is_explicitly_simulated(self):
        result = self.backend.execute(self.request)

        self.assertTrue(result.metadata["simulated"])
        self.assertFalse(result.metadata["hardware_accelerated"])
        self.assertFalse(result.metadata["timing_measured"])
        self.assertEqual(
            result.output["execution_mode"],
            "simulation",
        )

    def test_unsupported_operation_is_rejected(self):
        request = ExecutionRequest(
            action_id="mock-test-002",
            workload_path="sample_workload.py",
            operation="unsupported_operation",
        )

        with self.assertRaises(BackendUnavailableError):
            self.backend.execute(request)

    def test_mock_does_not_require_workload_file(self):
        request = ExecutionRequest(
            action_id="mock-test-003",
            workload_path="nonexistent_workload.py",
            operation="benchmark",
        )

        result = self.backend.execute(request)

        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()
