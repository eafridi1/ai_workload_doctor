import tempfile
import unittest

from ssor.case_record import CaseRecord
from ssor.case_store import CaseStore, ConcurrencyConflictError


class TestSSoRRevisionRecovery(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.store = CaseStore(self.temp_dir.name)

    def make_case(self):
        return CaseRecord(
            case_id="recovery-test",
            workload="workloads/sample_workload.py",
        )

    def test_preview_does_not_modify_current_case(self):
        case = self.make_case()
        self.store.save(case)
        case.analysis = {"version": 2}
        self.store.save(case)

        preview = self.store.preview_revision(case.case_id, 1)

        self.assertEqual(preview["analysis"], {})
        self.assertEqual(self.store.load(case.case_id).revision, 2)

    def test_compare_revisions_reports_changed_fields(self):
        case = self.make_case()
        self.store.save(case)
        case.analysis = {"version": 2}
        self.store.save(case)

        comparison = self.store.compare_revisions(
            case.case_id, 1, 2
        )

        self.assertEqual(
            comparison["changes"]["analysis"]["before"], {}
        )
        self.assertEqual(
            comparison["changes"]["analysis"]["after"],
            {"version": 2},
        )

    def test_recovery_creates_new_revision_and_preserves_history(self):
        case = self.make_case()
        self.store.save(case)
        case.analysis = {"version": 2}
        self.store.save(case)

        self.store.recover_revision(
            case.case_id,
            revision=1,
            expected_current_revision=2,
        )

        current = self.store.load(case.case_id)
        history = self.store.get_history(case.case_id)

        self.assertEqual(current.revision, 3)
        self.assertEqual(current.analysis, {})
        self.assertEqual(
            current.events[-1]["event"],
            "revision_recovered",
        )
        self.assertEqual(
            [entry["revision"] for entry in history],
            [1, 2, 3],
        )

    def test_stale_recovery_is_rejected(self):
        case = self.make_case()
        self.store.save(case)

        with self.assertRaises(ConcurrencyConflictError):
            self.store.recover_revision(
                case.case_id,
                revision=1,
                expected_current_revision=0,
            )

    def test_missing_revision_is_rejected(self):
        case = self.make_case()
        self.store.save(case)

        with self.assertRaises(FileNotFoundError):
            self.store.preview_revision(case.case_id, 99)


if __name__ == "__main__":
    unittest.main()
