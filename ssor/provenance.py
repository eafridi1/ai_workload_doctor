from datetime import datetime, timezone
from typing import Any


def create_provenance(
    source: str,
    source_type: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a provenance record for an SSoR fact or event."""

    return {
        "source": source,
        "source_type": source_type,
        "details": details or {},
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }
