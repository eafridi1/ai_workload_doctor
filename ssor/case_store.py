
import json
import os
import tempfile
from pathlib import Path

from ssor.case_record import CaseRecord


class CaseStore:
    """Persistent JSON storage for SSoR case records."""

    def __init__(self, directory: str = "reports/ssor"):
        self.directory = Path(directory)
        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _path(self, case_id: str) -> Path:
        safe_case_id = "".join(
            character
            for character in case_id
            if character.isalnum()
            or character in "-_"
        )

        if not safe_case_id:
            raise ValueError("Invalid case_id.")

        return self.directory / f"{safe_case_id}.json"

    def save(self, case: CaseRecord) -> str:
        """Atomically save a case as formatted JSON."""

        path = self._path(case.case_id)

        content = json.dumps(
            case.to_dict(),
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

        finally:
            if temp_path.exists():
                temp_path.unlink()

        return str(path)

    def load(
        self,
        case_id: str,
        verify_integrity: bool = True,
    ) -> CaseRecord:
        """Load a case, verifying its audit chain by default."""

        path = self._path(case_id)

        if not path.is_file():
            raise FileNotFoundError(
                f"SSoR case not found: {case_id}"
            )

        data = json.loads(
            path.read_text(encoding="utf-8")
        )
        case = CaseRecord.from_dict(data)

        if verify_integrity and not case.verify_event_chain():
            raise ValueError(
                f"SSoR event-chain integrity check failed: {case_id}"
            )

        return case
