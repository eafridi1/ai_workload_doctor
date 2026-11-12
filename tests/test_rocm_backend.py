import unittest
from unittest.mock import patch, Mock

from backends import (
    BackendUnavailableError,
    ExecutionBackend,
    ExecutionRequest,
    ROCmExecutionBackend,
)


class TestROCmExecutionBackend(unittest.TestCase):

    def setUp(self):
        self.backend = ROCmExecutionBackend()

    def test_backend_implements_interface(self):
        self.assertIsInstance(self.backend, ExecutionBackend)

    @patch("backends.rocm_backend.shutil.which", return_value=None)
    def test_missing_rocminfo_reports_unavailable(self, mock_which):
        capabilities = self.backend.get_capabilities()

        self.assertFalse(capabilities.available)
        self.assertIn("not installed", capabilities.unavailable_reason)

    @patch("backends.rocm_backend.subprocess.run")
    @patch("backends.rocm_backend.shutil.which", return_value="/usr/bin/rocminfo")
    def test_detects_amd_gpu(self, mock_which, mock_run):
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Agent 2\n  Name: gfx1100\n",
        )

        capabilities = self.backend.get_capabilities()

        self.assertTrue(capabilities.available)
        self.assertEqual(capabilities.backend_name, "amd-rocm")
        self.assertIn("gfx1100", capabilities.device_name)
        self.assertEqual(capabilities.supported_operations, ())

    @patch("backends.rocm_backend.subprocess.run")
    @patch("backends.rocm_backend.shutil.which", return_value="/usr/bin/rocminfo")
    def test_cpu_only_environment_reports_unavailable(
        self, mock_which, mock_run
    ):
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Agent 1\n  Name: Intel CPU\n",
        )

        capabilities = self.backend.get_capabilities()

        self.assertFalse(capabilities.available)
        self.assertIn("No AMD GPU", capabilities.unavailable_reason)

    @patch("backends.rocm_backend.subprocess.run")
    @patch("backends.rocm_backend.shutil.which", return_value="/usr/bin/rocminfo")
    def test_rocminfo_failure_reports_unavailable(
        self, mock_which, mock_run
    ):
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
        )

        capabilities = self.backend.get_capabilities()

        self.assertFalse(capabilities.available)

    @patch("backends.rocm_backend.subprocess.run")
    @patch("backends.rocm_backend.shutil.which", return_value="/usr/bin/rocminfo")
    def test_detection_timeout_reports_unavailable(
        self, mock_which, mock_run
    ):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="rocminfo",
            timeout=10,
        )

        capabilities = self.backend.get_capabilities()

        self.assertFalse(capabilities.available)
        self.assertIn("timed out", capabilities.unavailable_reason)

    @patch.object(
        ROCmExecutionBackend,
        "get_capabilities",
    )
    def test_execution_is_not_implemented(self, mock_capabilities):
        from backends import BackendCapabilities

        mock_capabilities.return_value = BackendCapabilities(
            backend_name="amd-rocm",
            available=True,
            device_name="AMD GPU (gfx1100)",
        )

        request = ExecutionRequest(
            action_id="rocm-test-001",
            workload_path="sample_workload.py",
            operation="benchmark",
        )

        with self.assertRaises(BackendUnavailableError):
            self.backend.execute(request)


if __name__ == "__main__":
    unittest.main()
