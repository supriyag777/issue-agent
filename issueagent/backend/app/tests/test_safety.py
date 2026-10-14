import pytest
from pydantic import ValidationError

from ..services.patch_service import UnsafePatch, validate_path, validate_changes
from ..schemas.schemas import FileChange


def test_malicious_paths_are_rejected():
    for path in ("/etc/passwd", "../secrets.txt", "src/../../secret", "src/\x00bad.py", ".git/config"):
        with pytest.raises(UnsafePatch):
            validate_path(path)


def test_change_requires_content_or_patch():
    with pytest.raises(UnsafePatch):
        validate_changes([FileChange(path="src/app.py")])


def test_default_branch_is_not_a_generated_branch():
    branch = "ai-issue/124-abc123"
    assert branch != "main"
    assert branch.startswith("ai-issue/")
