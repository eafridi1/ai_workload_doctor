import fcntl
import json
import os
import tempfile
from pathlib import Path

from ssor.case_record import CaseRecord


class ConcurrencyConflictError(RuntimeError):
    """Raised when a case has changed since it was loaded."""


class CaseStore:
    """Validated, atomic JSON storage with optimistic concurrency control."""

    def __init__(self, directory: str = "reports/ssor"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, case_id: str) -> Path:
        if not isinstance(case_id, str):
            raise ValueError("case_id must be a string.")

        safe_case_id = "".join(
            character
            for character in case_id
            if character.isalnum() or character in "-_"
        )

        if not safe_case_id:
            raise ValueError("Invalid case_id.")

        return self.directory / f"{safe_case_id}.json"

    def save(self, case: CaseRecord) -> str:
        """Save only if the caller's revision matches the current revision."""
        if not isinstance(case, CaseRecord):
            raise TypeError("case must be a CaseRecord instance.")

        case.validate_schema()
        if not case.verify_event_chain():
            raise ValueError("SSoR event-chain integrity check failed.")

        path = self._path(case.case_id)
        lock_path = path.with_suffix(path.suffix + ".lock")

        # Lock the read-check-write sequence so cooperating processes
        # cannot both update the same case using the same old revision.
        with lock_path.open("a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

            try:
                if path.is_file():
                    current = self.load(case.case_id)
                    current_revision = current.revision

                    if case.revision != current_revision:
                        raise ConcurrencyConflictError(
                            f"Stale SSoR case '{case.case_id}': "
                            f"expected revision {case.revision}, "
                            f"current revision is {current_revision}."
                        )

                    next_revision = current_revision + 1
                else:
                    if case.revision != 0:
                        raise ConcurrencyConflictError(
                            f"SSoR case '{case.case_id}' does not exist, "
                            f"but supplied revision is {case.revision}."
                        )

                    next_revision = 1

                data = case.to_dict()
                data["revision"] = next_revision

                # Validate the exact record that will be persisted.
                candidate = CaseRecord.from_dict(data)
                if not candidate.verify_event_chain():
                    raise ValueError(
                        "SSoR event-chain integrity check failed."
                    )

                content = json.dumps(
                    candidate.to_dict(),
                    indent=2,
                    sort_keys=True,
                    allow_nan=False,
                )

                fd, temp_name = tempfile.mkstemp(
                    prefix=f".{path.name}.",
                    suffix=".tmp",
                    dir=path.parent,
                )
                temp_path = Path(temp_name)

                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
                        temp_file.write(content)
                        temp_file.write("\n")
                        temp_file.flush()
                        os.fsync(temp_file.fileno())

                    os.replace(temp_path, path)
                    case.revision = next_revision

                finally:
                    if temp_path.exists():
                        temp_path.unlink()

                return str(path)

            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def load(
        self,
        case_id: str,
        verify_integrity: bool = True,
    ) -> CaseRecord:
        """Load and validate a case, optionally verifying its event chain."""
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
