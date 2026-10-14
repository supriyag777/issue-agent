import re
from pathlib import PurePosixPath
from typing import Any

from ..core.config import Settings
from .github_service import GitHubService


class CodeSearchService:
    def __init__(self, github: GitHubService, settings: Settings):
        self.github = github
        self.settings = settings

    def keywords(self, title: str, body: str) -> list[str]:
        text = f"{title} {body}".lower()
        candidates = re.findall(r"[a-zA-Z_][a-zA-Z0-9_+#.-]{2,}", text)
        stop = {"when", "with", "that", "this", "from", "have", "should", "would", "issue", "users", "please", "into", "they", "then", "there", "report"}
        unique: list[str] = []
        for item in candidates:
            normalized = item.strip(".-_")
            if normalized and normalized not in stop and normalized not in unique:
                unique.append(normalized)
        return unique[:18]

    def language(self, path: str) -> str:
        return {".py": "python", ".ts": "typescript", ".tsx": "tsx", ".js": "javascript", ".jsx": "jsx", ".go": "go", ".rs": "rust", ".java": "java", ".rb": "ruby", ".sql": "sql", ".md": "markdown"}.get(PurePosixPath(path).suffix.lower(), "text")

    def chunk(self, path: str, code: str, relevance: float) -> dict[str, Any]:
        lines = code.splitlines()
        limit = 140
        if len(lines) > limit:
            lines = lines[:limit]
        return {"filename": path, "language": self.language(path), "start_line": 1, "end_line": len(lines), "code": "\n".join(lines), "relevance": relevance}

    async def search(self, repository: Any, title: str, body: str) -> tuple[list[str], list[dict[str, Any]]]:
        words = self.keywords(title, body)
        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for query in words[:8]:
            matches = await self.github.search_code(repository, query)
            for match in matches:
                path = match.get("path", "")
                if not path or path in seen or path.endswith((".lock", ".map", ".min.js")):
                    continue
                seen.add(path)
                results.append(match)
                if len(results) >= self.settings.max_files_per_analysis:
                    break
            if len(results) >= self.settings.max_files_per_analysis:
                break
        chunks = []
        budget = self.settings.max_code_chars
        for match in results:
            try:
                code = await self.github.get_file(repository, match["path"], repository.default_branch)
            except Exception:
                continue
            chunk = self.chunk(match["path"], code, float(match.get("score", 0.5)))
            if len(chunk["code"]) > budget:
                chunk["code"] = chunk["code"][:budget]
                chunk["end_line"] = chunk["code"].count("\n") + 1
            budget -= len(chunk["code"])
            chunks.append(chunk)
            if budget <= 0:
                break
        return words, chunks
