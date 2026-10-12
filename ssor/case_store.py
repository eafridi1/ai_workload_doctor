
import json
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
        """Save a case record as formatted JSON."""

        path = self._path(case.case_id)

        path.write_text(
            json.dumps(
                case.to_dict(),
                indent=2,
                sort_keys=True,
                allow_nan=False,
            ),
            encoding="utf-8",
        )

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
