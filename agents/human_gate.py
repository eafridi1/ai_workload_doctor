class HumanApprovalGate:
    """Control optimization actions requiring human approval."""

    def request_approval(self, candidate: dict) -> dict:
        return {
            "candidate": candidate["candidate"],
            "approved": False,
            "requires_human_approval": True,
            "status": "awaiting_human_approval",
        }

    @staticmethod
    def approve(candidate: dict) -> dict:
        return {
            "candidate": candidate["candidate"],
            "approved": True,
            "requires_human_approval": True,
            "status": "approved",
        }

    @staticmethod
    def reject(candidate: dict) -> dict:
        return {
            "candidate": candidate["candidate"],
            "approved": False,
            "requires_human_approval": True,
            "status": "rejected",
        }
