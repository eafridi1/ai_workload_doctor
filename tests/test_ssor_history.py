
import tempfile
import unittest

from ssor.case_record import CaseRecord
from ssor.case_store import CaseStore, ConcurrencyConflictError


class TestSSoRHistory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.store = CaseStore(self.temp_dir.name)

    def make_case(self):
        return CaseRecord(
            case_id="history-test",
            workload="workloads/sample_workload.py",
        )

    def test_first_save_creates_revision_history(self):
        case = self.make_case()
        self.store.save(case)

        history = self.store.get_history(case.case_id)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["revision"], 1)
        self.assertEqual(history[0]["summary"], "Initial case creation")
        self.assertEqual(history[0]["snapshot"]["revision"], 1)

    def test_updates_create_separate_snapshots(self):
        case = self.make_case()
        self.store.save(case)

        case.analysis = {"language": "Python"}
        self.store.save(case)

        history = self.store.get_history(case.case_id)

        self.assertEqual([item["revision"] for item in history], [1, 2])
        self.assertEqual(history[0]["snapshot"]["analysis"], {})
        self.assertEqual(
            history[1]["snapshot"]["analysis"],
            {"language": "Python"},
        )
        self.assertIn("analysis", history[1]["summary"])

    def test_history_reads_do_not_change_current_revision(self):
        case = self.make_case()
        self.store.save(case)
        revision_before = self.store.load(case.case_id).revision

        self.store.get_history(case.case_id)

        self.assertEqual(
            self.store.load(case.case_id).revision,
            revision_before,
        )

    def test_stale_write_does_not_create_history_entry(self):
        case = self.make_case()
        self.store.save(case)

        writer_a = self.store.load(case.case_id)
        writer_b = self.store.load(case.case_id)

        writer_a.analysis = {"writer": "A"}
        self.store.save(writer_a)

        writer_b.analysis = {"writer": "B"}
        with self.assertRaises(ConcurrencyConflictError):
            self.store.save(writer_b)

        history = self.store.get_history(case.case_id)
        self.assertEqual([item["revision"] for item in history], [1, 2])

    def test_history_detects_snapshot_tampering(self):
        case = self.make_case()
        self.store.save(case)

        history_file = (
            self.store._history_dir(case.case_id)
            / "revision-000001.json"
        )
        import json

        entry = json.loads(history_file.read_text(encoding="utf-8"))
        entry["snapshot"]["workload"] = "tampered.py"
        history_file.write_text(json.dumps(entry), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "integrity check failed"):
            self.store.get_history(case.case_id)

    def test_missing_history_returns_empty_list(self):
        self.assertEqual(self.store.get_history("no-history"), [])


if __name__ == "__main__":
    unittest.main()
