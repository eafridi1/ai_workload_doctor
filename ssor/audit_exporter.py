"""Atomic persistence of verified SSoR audit reports."""

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


class AuditReportExporter:
    """Persist audit reports safely without modifying SSoR history."""

    def __init__(self, export_dir: str | Path = "reports/ssor/audit_exports"):
        self.export_dir = Path(export_dir)

    def export(
        self,
        case_id: str,
        report: dict[str, Any],
    ) -> Path:
        """Atomically save a verified audit report as JSON."""

        if not isinstance(case_id, str) or not re.fullmatch(
            r"[A-Za-z0-9_-]+", case_id
        ):
            raise ValueError("Invalid case ID for audit export.")

        if (
            not isinstance(report, dict)
            or report.get("report_type") != "ssor_revision_audit"
            or report.get("integrity_status") != "verified"
            or report.get("case_id") != case_id
        ):
            raise ValueError("Report is not a matching verified audit report.")

        self.export_dir.mkdir(parents=True, exist_ok=True)

        destination = (self.export_dir / f"{case_id}-audit.json").resolve()
        export_root = self.export_dir.resolve()

        if destination.parent != export_root:
            raise ValueError("Invalid audit export destination.")

        content = json.dumps(report, indent=2, sort_keys=True) + "\n"
        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=export_root,
                prefix=".audit-",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())

            os.replace(temp_path, destination)
            return destination

        except Exception:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise
