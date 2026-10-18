import json
import tempfile
import unittest
from pathlib import Path

from ssor.case_record import CaseRecord
from ssor.case_store import CaseStore


class TestSSoRSchema(unittest.TestCase):
    def make_case(self, case_id="schema-test"):
        return CaseRecord(
            case_id=case_id,
            workload="workloads/sample_workload.py",
        )

    def test_valid_case_passes_schema_validation(self):
        case = self.make_case()
        case.record_event("analysis_completed", {"lines": 10})

        case.validate_schema()

        self.assertTrue(case.verify_event_chain())

    def test_missing_required_field_is_rejected_on_load(self):
        case = self.make_case()
        data = case.to_dict()
        del data["workload"]

        with self.assertRaisesRegex(ValueError, "missing required fields"):
            CaseRecord.from_dict(data)

    def test_incorrect_dictionary_field_type_is_rejected(self):
        case = self.make_case()
        case.analysis = ["not", "a", "dictionary"]

        with self.assertRaisesRegex(ValueError, "analysis must be a dictionary"):
            case.validate_schema()

    def test_incorrect_list_field_type_is_rejected(self):
        case = self.make_case()
        case.evidence = {"not": "a list"}

        with self.assertRaisesRegex(ValueError, "evidence must be a list"):
            case.validate_schema()

    def test_invalid_timestamp_is_rejected(self):
        case = self.make_case()
        case.created_at = "not-a-timestamp"

        with self.assertRaisesRegex(ValueError, "created_at"):
            case.validate_schema()

    def test_malformed_event_is_rejected(self):
        case = self.make_case()
        case.events = [
            {
                "event": "analysis_completed",
                "details": {},
                "timestamp": "2026-01-01T00:00:00+00:00",
                "previous_hash": "invalid",
                "event_hash": "invalid",
            }
        ]

        with self.assertRaisesRegex(ValueError, "previous_hash"):
            case.validate_schema()

    def test_store_refuses_to_save_invalid_case(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(directory=temp_dir)
            case = self.make_case()
            case.analysis = "invalid"

            with self.assertRaisesRegex(ValueError, "analysis"):
                store.save(case)

            self.assertEqual(list(Path(temp_dir).glob("*.json")), [])

    def test_store_refuses_to_save_broken_event_chain(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(directory=temp_dir)
            case = self.make_case()
            case.record_event("analysis_completed", {"lines": 10})
            case.events[0]["details"]["lines"] = 999

            with self.assertRaisesRegex(ValueError, "integrity check failed"):
                store.save(case)

            self.assertEqual(list(Path(temp_dir).glob("*.json")), [])

    def test_load_rejects_missing_required_field(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(directory=temp_dir)
            case = self.make_case()
            path = Path(store.save(case))

            data = json.loads(path.read_text(encoding="utf-8"))
            del data["outcome"]
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing required fields"):
                store.load(case.case_id)

    def test_load_rejects_incorrect_field_type(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(directory=temp_dir)
            case = self.make_case()
            path = Path(store.save(case))

            data = json.loads(path.read_text(encoding="utf-8"))
            data["evidence"] = "not-a-list"
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "evidence must be a list"):
                store.load(case.case_id)

    def test_valid_case_round_trips_through_store(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(directory=temp_dir)
            case = self.make_case()
            case.record_event("analysis_completed", {"lines": 10})

            store.save(case)
            loaded = store.load(case.case_id)

            self.assertEqual(loaded.to_dict(), case.to_dict())
            self.assertTrue(loaded.verify_event_chain())


if __name__ == "__main__":
    unittest.main()
