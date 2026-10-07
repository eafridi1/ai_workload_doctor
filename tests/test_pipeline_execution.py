import tempfile
import unittest
from pathlib import Path

from core.doctor_pipeline import WorkloadDoctorPipeline


class TestPipelineExecution(unittest.TestCase):

    def create_workload(self, directory, content):
        path = Path(directory) / "workload.py"
        path.write_text(content, encoding="utf-8")
        return path

    def test_successful_optimization_is_accepted(self):
        original = """def run_workload():
    total = 0
    for i in range(200000):
        total += i
    return total
"""

        optimized = """def run_workload():
    return sum(range(200000))
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            workload_path = self.create_workload(
                temp_dir,
                original,
            )

            pipeline = WorkloadDoctorPipeline(
                str(workload_path)
            )

            before = pipeline.benchmark(
                capture_output=True
            )

            action = pipeline.create_action(
                {
                    "candidate": "replace loop with built-in sum",
                    "category": "performance",
                    "reason": "Use optimized built-in operation.",
                    "evidence": [
                        "loop-based accumulation detected"
                    ],
                    "requires_human_approval": True,
                    "verification_required": True,
                },
                "AMD-03.7-success",
            )

            action.approve("test-reviewer")

            result = pipeline.execute_optimization(
                action=action,
                new_content=optimized,
                before_benchmark=before,
                reference_output=before.get("output"),
            )

            self.assertEqual(
                result["status"],
                "accepted",
            )

            self.assertEqual(
                result["verification"]["decision"],
                "accept",
            )

            self.assertTrue(
                result["verification"]["correctness_passed"]
            )

            self.assertTrue(
                result["verification"]["performance_improved"]
            )

            self.assertEqual(
                workload_path.read_text(
                    encoding="utf-8"
                ),
                optimized,
            )

    def test_failed_optimization_is_rolled_back(self):
        original = """def run_workload():
    total = 0
    for i in range(200000):
        total += i
    return total
"""

        incorrect_candidate = """def run_workload():
    return 123
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            workload_path = self.create_workload(
                temp_dir,
                original,
            )

            pipeline = WorkloadDoctorPipeline(
                str(workload_path)
            )

            before = pipeline.benchmark(
                capture_output=True
            )

            action = pipeline.create_action(
                {
                    "candidate": "unsafe replacement",
                    "category": "performance",
                    "reason": (
                        "Test rollback after "
                        "failed verification."
                    ),
                    "evidence": [
                        "synthetic negative test"
                    ],
                    "requires_human_approval": True,
                    "verification_required": True,
                },
                "AMD-03.7-rollback",
            )

            action.approve("test-reviewer")

            result = pipeline.execute_optimization(
                action=action,
                new_content=incorrect_candidate,
                before_benchmark=before,
                reference_output=before.get("output"),
            )

            self.assertEqual(
                result["status"],
                "rolled_back",
            )

            self.assertEqual(
                result["verification"]["decision"],
                "reject",
            )

            self.assertFalse(
                result["verification"]["correctness_passed"]
            )

            self.assertEqual(
                workload_path.read_text(
                    encoding="utf-8"
                ),
                original,
            )

            self.assertTrue(
                result["rollback"]["rolled_back"]
            )

            self.assertIn(
                "rolled_back",
                str(result["action"]["history"]),
            )


if __name__ == "__main__":
    unittest.main()
