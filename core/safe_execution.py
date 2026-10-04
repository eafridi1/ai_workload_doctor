"""Safely replace an approved file while preserving a rollback backup."""

import os
import shutil
import tempfile
from pathlib import Path


class SafeFileExecutor:
    def _atomic_replace(self, target: Path, content: bytes) -> None:
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=target.parent,
        )
        temp_path = Path(temp_name)

        try:
            with os.fdopen(fd, "wb") as temp_file:
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())

            shutil.copystat(target, temp_path)
            os.replace(temp_path, target)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def execute(self, action, target_path: str, new_content: str) -> dict:
        target = Path(target_path).resolve()

        if not target.is_file():
            raise FileNotFoundError(f"Target file not found: {target}")

        if action.requires_human_approval and not action.human_approved:
            raise PermissionError("Human approval is required.")

        fd, backup_name = tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".backup",
            dir=target.parent,
        )
        os.close(fd)
        backup = Path(backup_name)

        try:
            shutil.copy2(target, backup)
            action.mark_executed()
        except Exception:
            backup.unlink(missing_ok=True)
            raise

        try:
            self._atomic_replace(target, new_content.encode("utf-8"))
        except Exception:
            self._atomic_replace(target, backup.read_bytes())
            action.rollback("File replacement failed; original restored")
            raise

        return {
            "executed": True,
            "target": str(target),
            "backup_path": str(backup),
        }

    def rollback(self, action, target_path: str, backup_path: str,
                 reason: str) -> dict:
        target = Path(target_path).resolve()
        backup = Path(backup_path).resolve()

        if (
            not target.is_file()
            or backup.parent != target.parent
            or not backup.is_file()
            or not backup.name.startswith(f".{target.name}.")
            or not backup.name.endswith(".backup")
        ):
            raise ValueError("Invalid target or rollback backup.")

        self._atomic_replace(target, backup.read_bytes())
        action.rollback(reason)

        return {
            "rolled_back": True,
            "target": str(target),
        }
