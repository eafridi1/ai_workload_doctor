import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from core.doctor_pipeline import WorkloadDoctorPipeline
from ssor.case_record import CaseRecord
from ssor.case_store import CaseStore
from ssor.provenance import (
    content_hash,
    create_provenance,
    verify_content_hash,
)


class TestSSoR(unittest.TestCase):
    def test_case_record_tracks_state(self):
        case = CaseRecord(
            case_id="test-case",
            workload="sample_workload.py",
        )

        case.record_event(
            "analysis_completed",
            {"frameworks": ["PyTorch"]},
        )
        case.add_evidence({"type": "analysis"})

        data = case.to_dict()

        self.assertEqual(data["case_id"], "test-case")
        self.assertEqual(len(data["events"]), 1)
        self.assertEqual(len(data["evidence"]), 1)

    def test_case_store_saves_and_loads(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(directory=temp_dir)
            case = CaseRecord(
                case_id="save-load-test",
                workload="sample_workload.py",
            )
            case.record_event("test_event", {"value": 1})

            store.save(case)
            loaded = store.load("save-load-test")

            self.assertEqual(loaded.case_id, case.case_id)
            self.assertEqual(
                loaded.events,
                case.events,
            )

    def test_provenance_records_source(self):
        record = create_provenance(
            source="benchmark_engine",
            source_type="system",
            details={"runtime_seconds": 0.25},
        )

        self.assertEqual(record["source"], "benchmark_engine")
        self.assertEqual(record["source_type"], "system")
        self.assertIn("captured_at", record)

    def test_saved_case_can_be_recovered(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(directory=temp_dir)
            case = CaseRecord(
                case_id="recovery-test",
                workload="workloads/sample_workload.py",
            )
            case.analysis = {"language": "Python"}
            case.record_event("analysis_completed")

            store.save(case)

            pipeline = WorkloadDoctorPipeline(
                workload_path="workloads/sample_workload.py"
            )
            pipeline.case_store = store

            recovered = pipeline.load_case("recovery-test")

            self.assertEqual(
                recovered["case_id"],
                "recovery-test",
            )
            self.assertEqual(
                recovered["analysis"]["language"],
                "Python",
            )
            self.assertTrue(
                any(
                    event["event"] == "case_recovered"
                    for event in recovered["events"]
                )
            )

    def test_recovery_of_unknown_case_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(directory=temp_dir)
            pipeline = WorkloadDoctorPipeline(
                workload_path="workloads/sample_workload.py"
            )
            pipeline.case_store = store

            with self.assertRaises(FileNotFoundError):
                pipeline.load_case("missing-case")

    def test_content_hash_is_deterministic(self):
        first = {"value": 42, "source": "benchmark"}
        second = {"source": "benchmark", "value": 42}

        self.assertEqual(
            content_hash(first),
            content_hash(second),
        )

    def test_modified_content_fails_hash_verification(self):
        original = {"runtime_seconds": 0.25}
        original_hash = content_hash(original)

        self.assertTrue(
            verify_content_hash(original, original_hash)
        )

        modified = {"runtime_seconds": 0.01}

        self.assertFalse(
            verify_content_hash(modified, original_hash)
        )

    def test_provenance_includes_content_hash(self):
        record = create_provenance(
            source="benchmark_engine",
            source_type="system",
            details={"runtime_seconds": 0.25},
        )

        self.assertEqual(
            record["hash_algorithm"],
            "SHA-256",
        )
        self.assertTrue(
            verify_content_hash(
                record["details"],
                record["content_hash"],
            )
        )

    def test_new_event_chain_is_valid(self):
        case = CaseRecord(
            case_id="chain-test",
            workload="sample_workload.py",
        )

        case.record_event("analysis_completed", {"lines": 10})
        case.record_event("candidate_detected", {"count": 1})

        self.assertTrue(case.verify_event_chain())

    def test_modified_event_fails_chain_verification(self):
        case = CaseRecord(
            case_id="tamper-test",
            workload="sample_workload.py",
        )

        case.record_event("analysis_completed", {"lines": 10})
        case.events[0]["details"]["lines"] = 999

        self.assertFalse(case.verify_event_chain())

    def test_reordered_events_fail_chain_verification(self):
        case = CaseRecord(
            case_id="reorder-test",
            workload="sample_workload.py",
        )

        case.record_event("analysis_completed")
        case.record_event("candidate_detected")

        case.events.reverse()

        self.assertFalse(case.verify_event_chain())

    def test_case_store_rejects_tampered_event(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(directory=temp_dir)
            case = CaseRecord(
                case_id="tampered-persistence",
                workload="sample_workload.py",
            )
            case.record_event(
                "analysis_completed",
                {"lines": 10},
            )

            store.save(case)

            path = Path(temp_dir) / "tampered-persistence.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["events"][0]["details"]["lines"] = 999
            path.write_text(
                json.dumps(data),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "integrity check failed",
            ):
                store.load("tampered-persistence")

    def test_case_store_loads_valid_event_chain(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(directory=temp_dir)
            case = CaseRecord(
                case_id="valid-persistence",
                workload="sample_workload.py",
            )
            case.record_event(
                "analysis_completed",
                {"lines": 10},
            )

            store.save(case)
            loaded = store.load("valid-persistence")

            self.assertTrue(loaded.verify_event_chain())
            self.assertEqual(loaded.case_id, "valid-persistence")

    def test_failed_atomic_replace_preserves_previous_case(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(directory=temp_dir)
            original = CaseRecord(
                case_id="atomic-save-test",
                workload="original_workload.py",
            )
            original.record_event("original_saved")
            store.save(original)

            updated = CaseRecord(
                case_id="atomic-save-test",
                workload="updated_workload.py",
            )
            updated.record_event("updated_saved")

            with patch(
                "ssor.case_store.os.replace",
                side_effect=OSError("simulated replacement failure"),
            ):
                with self.assertRaisesRegex(
                    OSError,
                    "simulated replacement failure",
                ):
                    store.save(updated)

            loaded = store.load("atomic-save-test")

            self.assertEqual(
                loaded.workload,
                "original_workload.py",
            )
            self.assertEqual(
                loaded.events[0]["event"],
                "original_saved",
            )
            self.assertTrue(loaded.verify_event_chain())

    def test_failed_atomic_replace_cleans_temporary_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(directory=temp_dir)
            case = CaseRecord(
                case_id="atomic-cleanup-test",
                workload="sample_workload.py",
            )
            case.record_event("save_attempt")

            with patch(
                "ssor.case_store.os.replace",
                side_effect=OSError("simulated replacement failure"),
            ):
                with self.assertRaises(OSError):
                    store.save(case)

            temp_files = list(
                Path(temp_dir).glob(".atomic-cleanup-test.json.*.tmp")
            )

            self.assertEqual(temp_files, [])


if __name__ == "__main__":
    unittest.main()
