import tempfile
import unittest

from core.doctor_pipeline import WorkloadDoctorPipeline
from ssor.case_record import CaseRecord
from ssor.case_store import CaseStore, ConcurrencyConflictError


class TestPipelineRevisionAudit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.pipeline = WorkloadDoctorPipeline(
            workload_path="workloads/sample_workload.py",
        )
        self.pipeline.case_store = CaseStore(self.temp_dir.name)
        self.pipeline.case = CaseRecord(
            case_id="pipeline-audit-test",
            workload="workloads/sample_workload.py",
        )

    def save_two_revisions(self):
        self.pipeline.case.analysis = {"version": 1}
        self.pipeline.save_case()

        self.pipeline.case.analysis = {"version": 2}
        self.pipeline.save_case()

    def test_list_revisions(self):
        self.save_two_revisions()

        history = self.pipeline.list_case_revisions()

        self.assertEqual(
            [item["revision"] for item in history],
            [1, 2],
        )

    def test_preview_does_not_change_active_case(self):
        self.save_two_revisions()
        active_revision = self.pipeline.case.revision

        snapshot = self.pipeline.preview_case_revision(1)

        self.assertEqual(snapshot["analysis"], {"version": 1})
        self.assertEqual(self.pipeline.case.revision, active_revision)
        self.assertEqual(self.pipeline.case.analysis, {"version": 2})

    def test_compare_revisions(self):
        self.save_two_revisions()

        result = self.pipeline.compare_case_revisions(1, 2)

        self.assertEqual(
            result["changes"]["analysis"]["before"],
            {"version": 1},
        )
        self.assertEqual(
            result["changes"]["analysis"]["after"],
            {"version": 2},
        )

    def test_recovery_creates_new_revision(self):
        self.save_two_revisions()

        recovered = self.pipeline.recover_case_revision(
            revision=1,
            expected_current_revision=2,
        )

        self.assertEqual(recovered["revision"], 3)
        self.assertEqual(recovered["analysis"], {"version": 1})
        self.assertEqual(
            recovered["events"][-1]["event"],
            "revision_recovered",
        )

        history = self.pipeline.list_case_revisions()
        self.assertEqual(
            [item["revision"] for item in history],
            [1, 2, 3],
        )

    def test_stale_recovery_is_rejected(self):
        self.save_two_revisions()

        with self.assertRaises(ConcurrencyConflictError):
            self.pipeline.recover_case_revision(
                revision=1,
                expected_current_revision=1,
            )

    def test_missing_revision_is_rejected(self):
        self.save_two_revisions()

        with self.assertRaises(FileNotFoundError):
            self.pipeline.preview_case_revision(99)


if __name__ == "__main__":
    unittest.main()
