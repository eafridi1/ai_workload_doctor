import tempfile
import unittest
from pathlib import Path

from ssor.case_record import CaseRecord
from ssor.case_store import CaseStore
from ssor.provenance import create_provenance


class TestSSoR(unittest.TestCase):

    def test_case_record_tracks_state(self):
        case = CaseRecord(
            case_id="AMD-03.8-001",
            workload="sample_workload.py",
        )

        case.analysis = {
            "frameworks": ["PyTorch"],
            "gpu_usage": True,
        }

        case.candidate = {
            "candidate": "replace_cpu_operation",
            "category": "performance",
        }

        case.add_evidence(
            {
                "type": "benchmark",
                "value": "candidate faster",
            }
        )

        case.record_event(
            "analysis_completed",
            {"status": "success"},
        )

        self.assertEqual(
            case.case_id,
            "AMD-03.8-001",
        )

        self.assertEqual(
            case.analysis["frameworks"],
            ["PyTorch"],
        )

        self.assertEqual(
            len(case.evidence),
            1,
        )

        self.assertEqual(
            len(case.events),
            1,
        )

    def test_case_can_be_saved_and_loaded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(temp_dir)

            case = CaseRecord(
                case_id="AMD-03.8-002",
                workload="optimization_reference.py",
            )

            case.outcome = "accepted"

            case.approval = {
                "approved": True,
                "reviewer": "human",
            }

            path = store.save(case)

            self.assertTrue(
                Path(path).is_file()
            )

            loaded = store.load(
                "AMD-03.8-002"
            )

            self.assertEqual(
                loaded.case_id,
                case.case_id,
            )

            self.assertEqual(
                loaded.workload,
                case.workload,
            )

            self.assertEqual(
                loaded.outcome,
                "accepted",
            )

            self.assertTrue(
                loaded.approval["approved"]
            )

    def test_provenance_is_recorded(self):
        provenance = create_provenance(
            source="benchmark_engine",
            source_type="system",
            details={
                "run": 1,
                "purpose": "performance verification",
            },
        )

        self.assertEqual(
            provenance["source"],
            "benchmark_engine",
        )

        self.assertEqual(
            provenance["source_type"],
            "system",
        )

        self.assertEqual(
            provenance["details"]["purpose"],
            "performance verification",
        )

        self.assertIn(
            "captured_at",
            provenance,
        )


if __name__ == "__main__":
    unittest.main()
