import tempfile
import unittest
from pathlib import Path

from agents.governed_action import GovernedOptimizationAction
from core.safe_execution import SafeFileExecutor


class TestSafeFileExecutor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.target = Path(self.temp_dir.name) / "workload.py"
        self.original = "def run_workload():\n    return 10\n"
        self.updated = "def run_workload():\n    return 20\n"
        self.target.write_text(self.original, encoding="utf-8")
        self.executor = SafeFileExecutor()
        self.action = GovernedOptimizationAction(
            action_id="AMD-036-TEST",
            candidate="test file update",
            category="performance",
            reason="Test safe file execution",
            evidence=["Synthetic test"],
        )

    def approve_action(self):
        self.action.recommend()
        self.action.request_human_approval()
        self.action.approve("human_reviewer")

    def test_execution_blocked_without_approval(self):
        with self.assertRaises(PermissionError):
            self.executor.execute(
                self.action, str(self.target), self.updated
            )
        self.assertEqual(
            self.target.read_text(encoding="utf-8"), self.original
        )

    def test_approved_execution_creates_backup(self):
        self.approve_action()
        result = self.executor.execute(
            self.action, str(self.target), self.updated
        )

        self.assertTrue(result["executed"])
        self.assertEqual(
            self.target.read_text(encoding="utf-8"), self.updated
        )
        self.assertTrue(Path(result["backup_path"]).is_file())
        self.assertEqual(self.action.status, "executed")

    def test_rollback_restores_original_file(self):
        self.approve_action()
        result = self.executor.execute(
            self.action, str(self.target), self.updated
        )

        rollback_result = self.executor.rollback(
            self.action,
            str(self.target),
            result["backup_path"],
            "Test rollback",
        )

        self.assertTrue(rollback_result["rolled_back"])
        self.assertEqual(
            self.target.read_text(encoding="utf-8"), self.original
        )
        self.assertEqual(self.action.status, "rolled_back")


if __name__ == "__main__":
    unittest.main()
