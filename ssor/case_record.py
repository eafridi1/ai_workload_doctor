import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


GENESIS_HASH = "0" * 64
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")

CASE_DICT_FIELDS = (
    "analysis",
    "candidate",
    "approval",
    "execution",
    "benchmarks",
    "verification",
)

CASE_LIST_FIELDS = ("evidence", "provenance", "events")

REQUIRED_CASE_FIELDS = {
    "case_id",
    "workload",
    "analysis",
    "candidate",
    "evidence",
    "approval",
    "execution",
    "benchmarks",
    "verification",
    "outcome",
    "provenance",
    "events",
    "created_at",
    "updated_at",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_timestamp(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty ISO timestamp.")

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO timestamp.") from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must include a timezone.")


def _event_hash(event_data: dict[str, Any]) -> str:
    """Calculate a deterministic SHA-256 hash for an audit event."""
    canonical = json.dumps(
        event_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_event(event: Any, index: int) -> None:
    prefix = f"events[{index}]"

    if not isinstance(event, dict):
        raise ValueError(f"{prefix} must be a dictionary.")

    required = {
        "event",
        "details",
        "timestamp",
        "previous_hash",
        "event_hash",
    }
    missing = required - event.keys()
    if missing:
        raise ValueError(
            f"{prefix} missing required fields: {', '.join(sorted(missing))}."
        )

    if not isinstance(event["event"], str) or not event["event"].strip():
        raise ValueError(f"{prefix}.event must be a non-empty string.")

    if not isinstance(event["details"], dict):
        raise ValueError(f"{prefix}.details must be a dictionary.")

    _validate_timestamp(event["timestamp"], f"{prefix}.timestamp")

    for field_name in ("previous_hash", "event_hash"):
        value = event[field_name]
        if not isinstance(value, str) or not HASH_PATTERN.fullmatch(value):
            raise ValueError(
                f"{prefix}.{field_name} must be a 64-character lowercase SHA-256 hash."
            )

    try:
        json.dumps(event, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{prefix} contains invalid JSON data.") from exc


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
    revision: int = 0

    def validate_schema(self) -> None:
        """Raise ValueError when the case or its events violate the schema."""
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            raise ValueError("case_id must be a non-empty string.")

        if not isinstance(self.workload, str) or not self.workload.strip():
            raise ValueError("workload must be a non-empty string.")

        for field_name in CASE_DICT_FIELDS:
            if not isinstance(getattr(self, field_name), dict):
                raise ValueError(f"{field_name} must be a dictionary.")

        for field_name in CASE_LIST_FIELDS:
            value = getattr(self, field_name)
            if not isinstance(value, list):
                raise ValueError(f"{field_name} must be a list.")

        for field_name in ("evidence", "provenance"):
            for index, item in enumerate(getattr(self, field_name)):
                if not isinstance(item, dict):
                    raise ValueError(
                        f"{field_name}[{index}] must be a dictionary."
                    )

        if not isinstance(self.outcome, str) or not self.outcome.strip():
            raise ValueError("outcome must be a non-empty string.")

        _validate_timestamp(self.created_at, "created_at")
        _validate_timestamp(self.updated_at, "updated_at")

        for index, event in enumerate(self.events):
            _validate_event(event, index)
        if (
            not isinstance(self.revision, int)
            or isinstance(self.revision, bool)
            or self.revision < 0
        ):
            raise ValueError("revision must be a non-negative integer.")

        try:
            json.dumps(self.to_dict(), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("Case contains data that is not valid JSON.") from exc

    def record_event(
        self,
        event: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Append an event linked to the previous event's hash."""
        if not isinstance(event, str) or not event.strip():
            raise ValueError("event must be a non-empty string.")

        if details is not None and not isinstance(details, dict):
            raise ValueError("event details must be a dictionary.")

        previous_hash = (
            self.events[-1].get("event_hash", GENESIS_HASH)
            if self.events
            else GENESIS_HASH
        )

        event_data = {
            "event": event,
            "details": details or {},
            "timestamp": _now(),
            "previous_hash": previous_hash,
        }

        event_data["event_hash"] = _event_hash(event_data)
        _validate_event(event_data, len(self.events))
        self.events.append(event_data)
        self.updated_at = _now()

    def verify_event_chain(self) -> bool:
        """Verify event structure, hashes, and previous-event links."""
        previous_hash = GENESIS_HASH

        for index, event in enumerate(self.events):
            try:
                _validate_event(event, index)

                if event["previous_hash"] != previous_hash:
                    return False

                event_data = {
                    key: value
                    for key, value in event.items()
                    if key != "event_hash"
                }

                calculated_hash = _event_hash(event_data)
                if calculated_hash != event["event_hash"]:
                    return False

                previous_hash = event["event_hash"]

            except (TypeError, ValueError, KeyError):
                return False

        return True

    def add_evidence(self, evidence: dict[str, Any]) -> None:
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be a dictionary.")
        self.evidence.append(evidence)
        self.updated_at = _now()

    def add_provenance(self, provenance: dict[str, Any]) -> None:
        if not isinstance(provenance, dict):
            raise ValueError("provenance must be a dictionary.")
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
            "revision": self.revision,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CaseRecord":
        """Create a case only from a complete, schema-valid record."""
        if not isinstance(data, dict):
            raise ValueError("Case record must be a dictionary.")

        missing = REQUIRED_CASE_FIELDS - data.keys()
        if missing:
            raise ValueError(
                f"Case record missing required fields: {', '.join(sorted(missing))}."
            )

        case = cls(
            case_id=data["case_id"],
            workload=data["workload"],
            analysis=data["analysis"],
            candidate=data["candidate"],
            evidence=data["evidence"],
            approval=data["approval"],
            execution=data["execution"],
            benchmarks=data["benchmarks"],
            verification=data["verification"],
            outcome=data["outcome"],
            provenance=data["provenance"],
            events=data["events"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            revision=data.get("revision", 0),
        )
        case.validate_schema()
        return case
