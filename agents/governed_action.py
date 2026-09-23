from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class GovernedOptimizationAction:
    """
    Represent an optimization action through its governance lifecycle.

    Lifecycle:

        candidate
            ↓
        recommended
            ↓
        awaiting_human_approval
            ↓
        approved / rejected
            ↓
        executed
            ↓
        verified / failed
            ↓
        accepted / rolled_back

    The model records state and evidence.
    It does not execute workload code.
    """

    action_id: str
    candidate: str
    category: str
    reason: str
    evidence: list[str] = field(default_factory=list)

    status: str = "candidate"

    requires_human_approval: bool = True
    verification_required: bool = True

    human_approved: bool = False

    before_benchmark: dict[str, Any] | None = None
    after_benchmark: dict[str, Any] | None = None

    verification_result: dict[str, Any] | None = None

    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    history: list[dict[str, Any]] = field(
        default_factory=list
    )

    def record_event(
        self,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record a governance lifecycle event."""

        event = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "status": status,
            "details": details or {},
        }

        self.history.append(event)
        self.status = status

    def recommend(self) -> None:
        """Move a candidate to the recommendation stage."""

        self.record_event(
            "recommended",
            {
                "reason": self.reason,
            },
        )

    def request_human_approval(self) -> None:
        """Place the action into the human approval queue."""

        self.record_event(
            "awaiting_human_approval",
            {
                "requires_human_approval": (
                    self.requires_human_approval
                ),
            },
        )

    def approve(self, reviewer: str) -> None:
        """Approve the action for controlled execution."""

        self.human_approved = True

        self.record_event(
            "approved",
            {
                "reviewer": reviewer,
            },
        )

    def reject(self, reviewer: str, reason: str) -> None:
        """Reject the proposed optimization action."""

        self.human_approved = False

        self.record_event(
            "rejected",
            {
                "reviewer": reviewer,
                "reason": reason,
            },
        )

    def mark_executed(self) -> None:
        """Record that the approved action was executed."""

        if self.requires_human_approval and not self.human_approved:
            raise PermissionError(
                "Human approval is required before execution."
            )

        self.record_event(
            "executed",
            {},
        )

    def record_benchmark(
        self,
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> None:
        """Attach before/after benchmark evidence."""

        self.before_benchmark = before
        self.after_benchmark = after

        self.record_event(
            "benchmarked",
            {
                "before": before,
                "after": after,
            },
        )

    def record_verification(
        self,
        verification_result: dict[str, Any],
    ) -> None:
        """Attach correctness or safety verification evidence."""

        self.verification_result = verification_result

        self.record_event(
            "verified",
            {
                "verification_result": verification_result,
            },
        )

    def accept(self) -> None:
        """Accept the optimization after verification."""

        if self.verification_required:
            if self.verification_result is None:
                raise ValueError(
                    "Verification is required before acceptance."
                )

        self.record_event(
            "accepted",
            {},
        )

    def rollback(self, reason: str) -> None:
        """Record that the optimization should be rolled back."""

        self.record_event(
            "rolled_back",
            {
                "reason": reason,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""

        return {
            "action_id": self.action_id,
            "candidate": self.candidate,
            "category": self.category,
            "reason": self.reason,
            "evidence": self.evidence,
            "status": self.status,
            "requires_human_approval": (
                self.requires_human_approval
            ),
            "verification_required": (
                self.verification_required
            ),
            "human_approved": self.human_approved,
            "before_benchmark": self.before_benchmark,
            "after_benchmark": self.after_benchmark,
            "verification_result": self.verification_result,
            "created_at": self.created_at,
            "history": self.history,
        }
