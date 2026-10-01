import unittest

from agents.governed_action import GovernedOptimizationAction


def make_action(**kwargs):
    defaults = {
        "action_id": "test-001",
        "candidate": "test optimization",
        "category": "performance",
        "reason": "governance test",
    }
    defaults.update(kwargs)
    return GovernedOptimizationAction(**defaults)


def passing_verification():
    return {
        "verified": True,
        "decision": "accept",
        "correctness_passed": True,
        "performance_improved": True,
    }


class TestGovernanceAcceptance(unittest.TestCase):
    def test_cannot_accept_without_human_approval(self):
        action = make_action()
        action.record_verification(passing_verification())

        with self.assertRaises(PermissionError):
            action.accept()

    def test_cannot_accept_without_verification(self):
        action = make_action()
        action.approve("reviewer")

        with self.assertRaises(ValueError):
            action.accept()

    def test_cannot_accept_failed_verification(self):
        action = make_action()
        action.approve("reviewer")
        action.record_verification({
            "verified": False,
            "decision": "reject",
            "correctness_passed": False,
            "performance_improved": True,
        })

        with self.assertRaises(ValueError):
            action.accept()

    def test_accepts_approved_verified_action(self):
        action = make_action()
        action.approve("reviewer")
        action.record_verification(passing_verification())
        action.accept()

        self.assertEqual(action.status, "accepted")
        self.assertEqual(action.history[-1]["status"], "accepted")

    def test_approval_can_be_disabled_explicitly(self):
        action = make_action(
            requires_human_approval=False,
            verification_required=False,
        )
        action.accept()

        self.assertEqual(action.status, "accepted")


if __name__ == "__main__":
    unittest.main()
