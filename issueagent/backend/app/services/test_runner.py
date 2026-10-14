import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..core.config import Settings
from ..schemas.schemas import FileChange
from .patch_service import UnsafePatch, content_for, validate_path


@dataclass
class TestResult:
    status: str
    passed: bool
    output: str


def apply_changes_to_worktree(root: str, changes: list[FileChange]) -> None:
    base = Path(root).resolve()
    for change in changes:
        target = (base / validate_path(change.path)).resolve()
        if base not in target.parents and target != base:
            raise UnsafePatch(f"Worktree path escaped repository root: {change.path}")
        if change.change_type == "delete":
            target.unlink(missing_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content_for(change, target.read_text() if target.exists() else ""), encoding="utf-8")


def run_tests(settings: Settings) -> TestResult:
    if not settings.test_command:
        return TestResult("passed", True, "Structural validation passed. No TEST_COMMAND configured; set one for repository test execution in production.")
    if not settings.repository_worktree_root or not os.path.isdir(settings.repository_worktree_root):
        return TestResult("failed", False, "TEST_COMMAND is configured but REPOSITORY_WORKTREE_ROOT is missing or is not a directory.")
    try:
        completed = subprocess.run(settings.test_command, cwd=settings.repository_worktree_root, shell=True, capture_output=True, text=True, timeout=180, check=False)
    except subprocess.TimeoutExpired:
        return TestResult("failed", False, "Configured tests exceeded the 180 second timeout.")
    output = (completed.stdout + "\n" + completed.stderr).strip()[-12000:]
    return TestResult("passed" if completed.returncode == 0 else "failed", completed.returncode == 0, output or f"Test command exited with {completed.returncode}.")
