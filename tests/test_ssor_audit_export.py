
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.doctor_pipeline import WorkloadDoctorPipeline
from ssor.case_record import CaseRecord
from ssor.case_store import CaseStore


class TestSSoRAuditExport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.root = Path(self.temp_dir.name)
        self.store = CaseStore(self.root / "cases")
        self.export_dir = self.root / "exports"

        self.pipeline = WorkloadDoctorPipeline(
            workload_path="workloads/sample_workload.py",
            case_id="audit-export-test",
        )
        self.pipeline.case_store = self.store
        self.pipeline.case = CaseRecord(
            case_id="audit-export-test",
            workload="workloads/sample_workload.py",
        )

    def save_revision(self, version):
        self.pipeline.case.analysis = {"version": version}
        self.pipeline.case.record_event(
            "test_revision",
            {"version": version},
        )
        self.pipeline.save_case()

    def test_export_creates_readable_json_file(self):
        self.save_revision(1)

        exported_path = Path(
            self.pipeline.export_audit_report(
                export_dir=self.export_dir,
            )
        )

        self.assertTrue(exported_path.is_file())
        self.assertEqual(
            exported_path.name,
            "audit-export-test-audit.json",
        )

        report = json.loads(
            exported_path.read_text(encoding="utf-8")
        )

        self.assertEqual(report["case_id"], "audit-export-test")
        self.assertEqual(report["integrity_status"], "verified")
        self.assertEqual(report["revision_count"], 1)

    def test_export_overwrites_previous_report(self):
        self.save_revision(1)

        first_path = Path(
            self.pipeline.export_audit_report(
                export_dir=self.export_dir,
            )
        )

        self.save_revision(2)

        second_path = Path(
            self.pipeline.export_audit_report(
                export_dir=self.export_dir,
            )
        )

        self.assertEqual(first_path, second_path)

        report = json.loads(
            second_path.read_text(encoding="utf-8")
        )
        self.assertEqual(report["revision_count"], 2)

    def test_export_rejects_invalid_case_id(self):
        from ssor.audit_exporter import AuditReportExporter

        exporter = AuditReportExporter(self.export_dir)

        with self.assertRaises(ValueError):
            exporter.export(
                "../outside",
                {
                    "report_type": "ssor_revision_audit",
                    "integrity_status": "verified",
                    "case_id": "../outside",
                },
            )

        self.assertFalse(self.export_dir.exists())

    def test_export_rejects_unverified_report(self):
        from ssor.audit_exporter import AuditReportExporter

        exporter = AuditReportExporter(self.export_dir)

        with self.assertRaisesRegex(ValueError, "verified"):
            exporter.export(
                "audit-export-test",
                {
                    "report_type": "ssor_revision_audit",
                    "integrity_status": "unverified",
                    "case_id": "audit-export-test",
                },
            )

        self.assertFalse(self.export_dir.exists())

    def test_export_does_not_modify_case_or_history(self):
        self.save_revision(1)

        case_before = self.pipeline.case.to_dict()
        history_before = self.store.get_history(
            "audit-export-test"
        )

        self.pipeline.export_audit_report(
            export_dir=self.export_dir,
        )

        self.assertEqual(
            self.pipeline.case.to_dict(),
            case_before,
        )
        self.assertEqual(
            self.store.get_history("audit-export-test"),
            history_before,
        )

    def test_corrupted_history_prevents_export(self):
        self.save_revision(1)

        history_path = (
            self.root
            / "cases"
            / "history"
            / "audit-export-test"
            / "revision-000001.json"
        )

        entry = json.loads(
            history_path.read_text(encoding="utf-8")
        )
        entry["snapshot"]["analysis"]["version"] = 999

        history_path.write_text(
            json.dumps(entry),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "integrity"):
            self.pipeline.export_audit_report(
                export_dir=self.export_dir,
            )

        self.assertFalse(self.export_dir.exists())

    def test_failed_atomic_replace_preserves_previous_export(self):
        from ssor.audit_exporter import AuditReportExporter

        exporter = AuditReportExporter(self.export_dir)

        report = {
            "report_type": "ssor_revision_audit",
            "integrity_status": "verified",
            "case_id": "audit-export-test",
            "revision_count": 1,
        }

        destination = exporter.export(
            "audit-export-test",
            report,
        )
        previous_content = destination.read_text(
            encoding="utf-8"
        )

        updated_report = dict(report)
        updated_report["revision_count"] = 2

        with patch(
            "ssor.audit_exporter.os.replace",
            side_effect=OSError("simulated replace failure"),
        ):
            with self.assertRaises(OSError):
                exporter.export(
                    "audit-export-test",
                    updated_report,
                )

        self.assertEqual(
            destination.read_text(encoding="utf-8"),
            previous_content,
        )

        temporary_files = list(
            self.export_dir.glob(".audit-*.tmp")
        )
        self.assertEqual(temporary_files, [])


if __name__ == "__main__":
    unittest.main()
