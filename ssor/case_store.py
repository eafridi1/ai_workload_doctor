
import fcntl
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ssor.case_record import CaseRecord


class ConcurrencyConflictError(RuntimeError):
    """Raised when a case has changed since it was loaded."""


class CaseStore:
    """Atomic SSoR storage with concurrency control and revision history."""

    def __init__(self, directory: str = "reports/ssor"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _safe_case_id(self, case_id: str) -> str:
        if not isinstance(case_id, str):
            raise ValueError("case_id must be a string.")

        safe_id = "".join(
            char for char in case_id
            if char.isalnum() or char in "-_"
        )
        if not safe_id:
            raise ValueError("Invalid case_id.")
        return safe_id

    def _path(self, case_id: str) -> Path:
        return self.directory / f"{self._safe_case_id(case_id)}.json"

    def _history_dir(self, case_id: str) -> Path:
        return (
            self.directory
            / "history"
            / self._safe_case_id(case_id)
        )

    @staticmethod
    def _canonical_hash(data: dict) -> str:
        content = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )
        temp_path = Path(temp_name)

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                file.write(content)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())

            os.replace(temp_path, path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @staticmethod
    def _change_summary(
        previous: CaseRecord | None,
        current: CaseRecord,
    ) -> str:
        if previous is None:
            return "Initial case creation"

        before = previous.to_dict()
        after = current.to_dict()

        ignored = {"revision", "updated_at"}
        changed = sorted(
            key
            for key in after
            if key not in ignored and before.get(key) != after.get(key)
        )

        if not changed:
            return "Case saved; no tracked field changes"

        return "Updated fields: " + ", ".join(changed)

    def save(self, case: CaseRecord) -> str:
        """Save a new revision and its snapshot if the revision is current."""
        if not isinstance(case, CaseRecord):
            raise TypeError("case must be a CaseRecord instance.")

        case.validate_schema()
        if not case.verify_event_chain():
            raise ValueError("SSoR event-chain integrity check failed.")

        path = self._path(case.case_id)
        lock_path = path.with_suffix(path.suffix + ".lock")

        with lock_path.open("a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

            try:
                previous = None

                if path.is_file():
                    previous = self.load(case.case_id)
                    if case.revision != previous.revision:
                        raise ConcurrencyConflictError(
                            f"Stale SSoR case '{case.case_id}': "
                            f"expected revision {case.revision}, "
                            f"current revision is {previous.revision}."
                        )
                    next_revision = previous.revision + 1
                else:
                    if case.revision != 0:
                        raise ConcurrencyConflictError(
                            f"Case '{case.case_id}' does not exist, "
                            f"but supplied revision is {case.revision}."
                        )
                    next_revision = 1

                saved_at = datetime.now(timezone.utc).isoformat()
                data = case.to_dict()
                data["revision"] = next_revision
                data["updated_at"] = saved_at

                candidate = CaseRecord.from_dict(data)
                if not candidate.verify_event_chain():
                    raise ValueError(
                        "SSoR event-chain integrity check failed."
                    )

                snapshot = candidate.to_dict()
                history_path = (
                    self._history_dir(case.case_id)
                    / f"revision-{next_revision:06d}.json"
                )

                # The current case revision is authoritative. If a previous
                # process crashed after writing a snapshot but before
                # replacing the current case, discard that orphan snapshot.
                if history_path.exists():
                    history_path.unlink()

                entry = {
                    "case_id": candidate.case_id,
                    "revision": next_revision,
                    "timestamp": saved_at,
                    "summary": self._change_summary(
                        previous, candidate
                    ),
                    "snapshot_hash": self._canonical_hash(snapshot),
                    "snapshot": snapshot,
                }

                history_content = json.dumps(
                    entry, indent=2, sort_keys=True, allow_nan=False
                )
                current_content = json.dumps(
                    snapshot, indent=2, sort_keys=True, allow_nan=False
                )

                self._atomic_write(history_path, history_content)

                try:
                    self._atomic_write(path, current_content)
                except Exception:
                    history_path.unlink(missing_ok=True)
                    raise

                case.revision = next_revision
                case.updated_at = saved_at
                return str(path)

            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def load(
        self,
        case_id: str,
        verify_integrity: bool = True,
    ) -> CaseRecord:
        """Load and validate the current case."""
        path = self._path(case_id)

        if not path.is_file():
            raise FileNotFoundError(f"SSoR case not found: {case_id}")

        try:
            data = json.loads(
                path.read_text(encoding="utf-8"),
                parse_constant=lambda value: (
                    (_ for _ in ()).throw(
                        ValueError(f"Invalid JSON numeric constant: {value}")
                    )
                ),
            )
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            raise ValueError(
                f"SSoR case contains invalid JSON: {case_id}"
            ) from exc

        case = CaseRecord.from_dict(data)

        if verify_integrity and not case.verify_event_chain():
            raise ValueError(
                f"SSoR event-chain integrity check failed: {case_id}"
            )

        return case

    def get_history(self, case_id: str) -> list[dict]:
        """Return verified revision metadata and snapshots, oldest first."""
        history_dir = self._history_dir(case_id)

        if not history_dir.is_dir():
            return []

        entries = []

        for history_path in sorted(history_dir.glob("revision-*.json")):
            try:
                entry = json.loads(
                    history_path.read_text(encoding="utf-8"),
                    parse_constant=lambda value: (
                        (_ for _ in ()).throw(
                            ValueError(f"Invalid JSON constant: {value}")
                        )
                    ),
                )

                snapshot = entry["snapshot"]
                expected_hash = entry["snapshot_hash"]

                if not isinstance(snapshot, dict):
                    raise ValueError("Snapshot must be a dictionary.")

                if self._canonical_hash(snapshot) != expected_hash:
                    raise ValueError(
                        f"History snapshot integrity check failed: "
                        f"{history_path.name}"
                    )

                case = CaseRecord.from_dict(snapshot)
                if not case.verify_event_chain():
                    raise ValueError(
                        f"History event-chain integrity check failed: "
                        f"{history_path.name}"
                    )

                if (
                    entry.get("case_id") != case_id
                    or entry.get("revision") != case.revision
                    or history_path.name
                    != f"revision-{case.revision:06d}.json"
                ):
                    raise ValueError(
                        f"History metadata mismatch: {history_path.name}"
                    )

                entries.append(entry)

            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"Invalid SSoR history entry: {history_path.name}"
                ) from exc

        return entries
