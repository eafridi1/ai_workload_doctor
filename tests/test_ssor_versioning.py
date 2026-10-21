import tempfile
import unittest
from unittest.mock import patch

from ssor.case_record import CaseRecord
from ssor.case_store import CaseStore, ConcurrencyConflictError


class TestSSoRVersioning(unittest.TestCase):
    def make_case(self, case_id="version-test"):
        return CaseRecord(
            case_id=case_id,
            workload="workloads/sample_workload.py",
        )

    def test_first_save_assigns_revision_one(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(temp_dir)
            case = self.make_case()

            store.save(case)

            self.assertEqual(case.revision, 1)
            self.assertEqual(store.load(case.case_id).revision, 1)

    def test_successful_update_increments_revision(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(temp_dir)
            case = self.make_case()
            store.save(case)

            case.analysis = {"language": "Python"}
            store.save(case)

            self.assertEqual(case.revision, 2)
            self.assertEqual(store.load(case.case_id).revision, 2)

    def test_stale_case_cannot_overwrite_newer_revision(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(temp_dir)
            original = self.make_case()
            store.save(original)

            writer_a = store.load(original.case_id)
            writer_b = store.load(original.case_id)

            writer_a.analysis = {"writer": "A"}
            store.save(writer_a)

            writer_b.analysis = {"writer": "B"}
            with self.assertRaises(ConcurrencyConflictError):
                store.save(writer_b)

            current = store.load(original.case_id)
            self.assertEqual(current.revision, 2)
            self.assertEqual(current.analysis, {"writer": "A"})
            self.assertEqual(writer_b.revision, 1)

    def test_failed_save_does_not_increment_revision(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(temp_dir)
            case = self.make_case()
            store.save(case)
            case.analysis = {"update": True}

            with patch(
                "ssor.case_store.os.replace",
                side_effect=OSError("simulated replacement failure"),
            ):
                with self.assertRaisesRegex(
                    OSError, "simulated replacement failure"
                ):
                    store.save(case)

            self.assertEqual(case.revision, 1)
            self.assertEqual(store.load(case.case_id).revision, 1)

    def test_nonzero_revision_cannot_create_missing_case(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(temp_dir)
            case = self.make_case()
            case.revision = 1

            with self.assertRaises(ConcurrencyConflictError):
                store.save(case)

    def test_invalid_revision_is_rejected(self):
        case = self.make_case()
        case.revision = -1

        with self.assertRaisesRegex(ValueError, "revision"):
            case.validate_schema()


if __name__ == "__main__":
    unittest.main()
