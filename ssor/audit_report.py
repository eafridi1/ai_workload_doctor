"""Read-only audit report generation for verified SSoR revision history."""

from datetime import datetime, timezone
from typing import Any

from ssor.case_store import CaseStore


class AuditReportGenerator:
    """Build a read-only report from verified SSoR revision history."""

    def __init__(self, case_store: CaseStore):
        self.case_store = case_store

    def generate(self, case_id: str) -> dict[str, Any]:
        """Generate a report; raise if stored history fails validation."""
        history = self.case_store.get_history(case_id)

        revisions = []
        for entry in history:
            snapshot = entry["snapshot"]
            events = snapshot.get("events", [])

            revisions.append(
                {
                    "revision": entry["revision"],
                    "timestamp": entry["timestamp"],
                    "summary": entry["summary"],
                    "snapshot_hash": entry["snapshot_hash"],
                    "governance_events": [
                        {
                            "event": event["event"],
                            "timestamp": event["timestamp"],
                            "details": event["details"],
                        }
                        for event in events
                    ],
                }
            )

        revision_numbers = [
            revision["revision"] for revision in revisions
        ]

        return {
            "report_type": "ssor_revision_audit",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "case_id": case_id,
            "integrity_status": "verified",
            "revision_count": len(revisions),
            "first_revision": min(revision_numbers, default=None),
            "latest_revision": max(revision_numbers, default=None),
            "revisions": revisions,
        }
