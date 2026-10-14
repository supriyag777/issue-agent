from pathlib import PurePosixPath
from difflib import unified_diff
from typing import Any

from ..schemas.schemas import FileChange


class UnsafePatch(Exception):
    pass


def validate_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    pure = PurePosixPath(normalized)
    if not normalized or normalized.startswith("/") or ".." in pure.parts or "\x00" in normalized:
        raise UnsafePatch(f"Unsafe repository path: {path}")
    if len(normalized) > 300 or pure.parts[0] in {".git", ".github/workflows"}:
        raise UnsafePatch(f"Path is not allowed for automated changes: {path}")
    return normalized


def validate_changes(changes: list[FileChange]) -> list[FileChange]:
    if len(changes) > 10:
        raise UnsafePatch("A proposed patch may touch at most 10 files")
    total = 0
    validated = []
    for change in changes:
        path = validate_path(change.path)
        if change.change_type == "delete" and not change.patch and change.new_content is None:
            validated.append(change.model_copy(update={"path": path}))
            continue
        if change.change_type != "delete" and change.new_content is None:
            raise UnsafePatch(f"Change for {path} must include complete new_content before it can be applied safely")
        if change.new_content and len(change.new_content) > 120_000:
            raise UnsafePatch(f"Change for {path} is too large")
        total += len(change.patch) + len(change.new_content or "")
        validated.append(change.model_copy(update={"path": path}))
    if total > 350_000:
        raise UnsafePatch("Proposed patch exceeds the maximum reviewable size")
    return validated


def make_diff(changes: list[FileChange], originals: dict[str, str]) -> str:
    blocks: list[str] = []
    for change in changes:
        old = originals.get(change.path, "").splitlines(keepends=True)
        new = (change.new_content or "").splitlines(keepends=True)
        if change.change_type == "delete":
            new = []
        if not old and not new and change.patch:
            blocks.append(change.patch.rstrip())
            continue
        blocks.extend(unified_diff(old, new, fromfile=f"a/{change.path}", tofile=f"b/{change.path}"))
    return "".join(blocks).rstrip()


def content_for(change: FileChange, original: str) -> str:
    if change.change_type == "delete":
        return ""
    if change.new_content is not None:
        return change.new_content
    raise UnsafePatch(f"Cannot safely apply a patch without complete new_content for {change.path}")
