from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CaseRecord:
    """State System of Record for one workload optimization case."""

    case_id: str
    workload: str
    analysis: dict[str, Any] = field(default_factory=dict)
    candidate: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    approval: dict[str, Any] = field(default_factory=dict)
    execution: dict[str, Any] = field(default_factory=dict)
    benchmarks: dict[str, Any] = field(default_factory=dict)
    verification: dict[str, Any] = field(default_factory=dict)
    outcome: str = "open"
    provenance: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def record_event(
        self,
        event: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.events.append(
            {
                "event": event,
                "details": details or {},
                "timestamp": _now(),
            }
        )
        self.updated_at = _now()

    def add_evidence(
        self,
        evidence: dict[str, Any],
    ) -> None:
        self.evidence.append(evidence)
        self.updated_at = _now()

    def add_provenance(
        self,
        provenance: dict[str, Any],
    ) -> None:
        self.provenance.append(provenance)
        self.updated_at = _now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "workload": self.workload,
            "analysis": self.analysis,
            "candidate": self.candidate,
            "evidence": self.evidence,
            "approval": self.approval,
            "execution": self.execution,
            "benchmarks": self.benchmarks,
            "verification": self.verification,
            "outcome": self.outcome,
            "provenance": self.provenance,
            "events": self.events,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CaseRecord":
        return cls(
            case_id=data["case_id"],
            workload=data["workload"],
            analysis=data.get("analysis", {}),
            candidate=data.get("candidate", {}),
            evidence=data.get("evidence", []),
            approval=data.get("approval", {}),
            execution=data.get("execution", {}),
            benchmarks=data.get("benchmarks", {}),
            verification=data.get("verification", {}),
            outcome=data.get("outcome", "open"),
            provenance=data.get("provenance", []),
            events=data.get("events", []),
            created_at=data.get("created_at", _now()),
            updated_at=data.get("updated_at", _now()),
        )

