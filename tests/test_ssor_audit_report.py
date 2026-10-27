import json
import tempfile
import unittest
from pathlib import Path

from core.doctor_pipeline import WorkloadDoctorPipeline
from ssor.case_record import CaseRecord
from ssor.case_store import CaseStore


class TestSSoRAuditReport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.store = CaseStore(self.temp_dir.name)
        self.pipeline = WorkloadDoctorPipeline(
            workload_path="workloads/sample_workload.py",
            case_id="audit-test",
        )
        self.pipeline.case_store = self.store
        self.pipeline.case = CaseRecord(
            case_id="audit-test",
            workload="workloads/sample_workload.py",
        )

    def save_revision(self, version):
        self.pipeline.case.analysis = {"version": version}
        self.pipeline.case.record_event(
            "test_revision",
            {"version": version},
        )
        self.pipeline.save_case()

    def test_report_contains_revision_metadata_and_events(self):
        self.save_revision(1)
        self.save_revision(2)

        report = self.pipeline.generate_audit_report()

        self.assertEqual(report["report_type"], "ssor_revision_audit")
        self.assertEqual(report["case_id"], "audit-test")
        self.assertEqual(report["integrity_status"], "verified")
        self.assertEqual(report["revision_count"], 2)
        self.assertEqual(report["first_revision"], 1)
        self.assertEqual(report["latest_revision"], 2)
        self.assertEqual(
            [item["revision"] for item in report["revisions"]],
            [1, 2],
        )
        self.assertTrue(report["revisions"][0]["snapshot_hash"])
        self.assertIn(
            "test_revision",
            [
                event["event"]
                for event in report["revisions"][1]["governance_events"]
            ],
        )
        json.dumps(report, allow_nan=False)

    def test_report_does_not_change_active_case(self):
        self.save_revision(1)
        before = self.pipeline.case.to_dict()

        self.pipeline.generate_audit_report()

        self.assertEqual(self.pipeline.case.to_dict(), before)

    def test_report_does_not_change_saved_history(self):
        self.save_revision(1)
        before = self.store.get_history("audit-test")

        self.pipeline.generate_audit_report()

        self.assertEqual(self.store.get_history("audit-test"), before)

    def test_empty_history_returns_empty_report(self):
        report = self.pipeline.generate_audit_report()

        self.assertEqual(report["revision_count"], 0)
        self.assertIsNone(report["first_revision"])
        self.assertIsNone(report["latest_revision"])
        self.assertEqual(report["revisions"], [])
        self.assertEqual(report["integrity_status"], "verified")

    def test_corrupted_history_is_rejected(self):
        self.save_revision(1)

        history_path = (
            Path(self.temp_dir.name)
            / "history"
            / "audit-test"
            / "revision-000001.json"
        )
        entry = json.loads(history_path.read_text(encoding="utf-8"))
        entry["snapshot"]["analysis"]["version"] = 999
        history_path.write_text(
            json.dumps(entry),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "integrity"):
            self.pipeline.generate_audit_report()


if __name__ == "__main__":
    unittest.main()
