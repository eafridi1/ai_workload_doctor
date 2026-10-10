import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any


def _canonical_json(data: Any) -> str:
    """Serialize data consistently for integrity hashing."""

    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def content_hash(data: Any) -> str:
    """Return the SHA-256 hash of JSON-compatible content."""

    encoded = _canonical_json(data).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify_content_hash(data: Any, expected_hash: str) -> bool:
    """Check whether content matches its expected SHA-256 hash."""

    if not isinstance(expected_hash, str):
        return False

    actual_hash = content_hash(data)

    return hmac.compare_digest(actual_hash, expected_hash)


def create_provenance(
    source: str,
    source_type: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a provenance record with a hash of its recorded details."""

    recorded_details = details or {}

    return {
        "source": source,
        "source_type": source_type,
        "details": recorded_details,
        "content_hash": content_hash(recorded_details),
        "hash_algorithm": "SHA-256",
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }
