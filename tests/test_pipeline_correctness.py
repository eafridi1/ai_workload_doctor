import unittest

from core.doctor_pipeline import WorkloadDoctorPipeline


class TestPipelineCorrectness(unittest.TestCase):
    def setUp(self):
        self.pipeline = WorkloadDoctorPipeline(
            workload_path="workloads/benchmark_workload.py"
        )
        self.before = {"average_time_seconds": 2.0}
        self.after = {"average_time_seconds": 1.0}

    def test_equivalent_outputs_and_improvement_pass(self):
        result = self.pipeline.verify(
            self.before,
            self.after,
            reference_output={"total": 100, "items": [1, 2, 3]},
            candidate_output={"total": 100, "items": [1, 2, 3]},
        )
        self.assertTrue(result["correctness_passed"])
        self.assertTrue(result["performance_improved"])
        self.assertTrue(result["verified"])
        self.assertEqual(
            result["correctness_result"]["mismatch_count"], 0
        )

    def test_incorrect_output_is_rejected_even_if_faster(self):
        result = self.pipeline.verify(
            self.before,
            self.after,
            reference_output={"total": 100},
            candidate_output={"total": 99},
        )
        self.assertFalse(result["correctness_passed"])
        self.assertFalse(result["verified"])
        self.assertEqual(result["decision"], "reject")
        self.assertGreater(
            result["correctness_result"]["mismatch_count"], 0
        )

    def test_missing_correctness_evidence_fails_closed(self):
        result = self.pipeline.verify(self.before, self.after)
        self.assertFalse(result["correctness_passed"])
        self.assertFalse(result["verified"])
        self.assertEqual(result["decision"], "reject")

    def test_one_output_without_the_other_raises(self):
        with self.assertRaises(ValueError):
            self.pipeline.verify(
                self.before,
                self.after,
                reference_output=100,
            )


if __name__ == "__main__":
    unittest.main()
