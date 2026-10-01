import unittest

from agents.governed_action import GovernedOptimizationAction
from core.doctor_pipeline import WorkloadDoctorPipeline


class TestGovernanceLifecycle(unittest.TestCase):
    def setUp(self):
        self.pipeline = WorkloadDoctorPipeline(
            workload_path="workloads/benchmark_workload.py"
        )
        self.action = GovernedOptimizationAction(
            action_id="AMD-035-TEST",
            candidate="test optimization",
            category="performance",
            reason="Validate governed optimization lifecycle",
            evidence=["Synthetic test evidence"],
            requires_human_approval=True,
            verification_required=True,
        )
        self.before = {"average_time_seconds": 2.0}
        self.after = {"average_time_seconds": 1.0}

    def test_successful_lifecycle(self):
        action = self.action

        action.recommend()
        action.request_human_approval()
        action.approve("human_reviewer")
        action.mark_executed()
        action.record_benchmark(self.before, self.after)

        result = self.pipeline.verify(
            self.before,
            self.after,
            reference_output={"result": [1, 2, 3]},
            candidate_output={"result": [1, 2, 3]},
        )
        action.record_verification(result)
        action.accept()

        self.assertEqual(action.status, "accepted")
        self.assertTrue(result["verified"])
        self.assertTrue(action.human_approved)

        statuses = [event["status"] for event in action.history]
        for expected in (
            "recommended",
            "awaiting_human_approval",
            "approved",
            "executed",
            "benchmarked",
            "verified",
            "accepted",
        ):
            self.assertIn(expected, statuses)

    def test_execution_blocked_without_approval(self):
        action = self.action
        action.recommend()
        action.request_human_approval()

        with self.assertRaises(PermissionError):
            action.mark_executed()

        self.assertNotIn(
            "executed",
            [event["status"] for event in action.history],
        )

    def test_incorrect_candidate_is_rolled_back(self):
        action = self.action
        action.recommend()
        action.request_human_approval()
        action.approve("human_reviewer")
        action.mark_executed()
        action.record_benchmark(self.before, self.after)

        result = self.pipeline.verify(
            self.before,
            self.after,
            reference_output={"result": 100},
            candidate_output={"result": 99},
        )
        action.record_verification(result)

        self.assertFalse(result["verified"])
        self.assertEqual(result["decision"], "reject")

        action.rollback("Correctness verification failed")

        self.assertEqual(action.status, "rolled_back")
        self.assertEqual(
            action.history[-1]["status"],
            "rolled_back",
        )

    def test_no_performance_gain_is_rejected(self):
        action = self.action
        action.recommend()
        action.request_human_approval()
        action.approve("human_reviewer")
        action.mark_executed()

        slower = {"average_time_seconds": 2.5}
        action.record_benchmark(self.before, slower)

        result = self.pipeline.verify(
            self.before,
            slower,
            reference_output=50,
            candidate_output=50,
        )
        action.record_verification(result)

        self.assertFalse(result["verified"])
        self.assertEqual(result["decision"], "reject")

        action.rollback("No performance improvement")
        self.assertEqual(action.status, "rolled_back")

    def test_human_rejection_is_recorded(self):
        action = self.action
        action.recommend()
        action.request_human_approval()
        action.reject("human_reviewer", "Not authorized")

        self.assertFalse(action.human_approved)
        self.assertEqual(action.status, "rejected")
        self.assertEqual(
            action.history[-1]["status"],
            "rejected",
        )


if __name__ == "__main__":
    unittest.main()
