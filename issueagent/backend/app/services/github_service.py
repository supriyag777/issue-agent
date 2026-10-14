from datetime import datetime, timezone
from typing import Any

import httpx

from ..core.config import Settings


class ProviderUnavailable(Exception):
    pass


class GitHubService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _headers(self, token: str) -> dict[str, str]:
        return {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28"}

    async def _request(self, method: str, url: str, token: str, **kwargs: Any) -> Any:
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                response = await client.request(method, url, headers=self._headers(token), **kwargs)
        except httpx.HTTPError as exc:
            raise ProviderUnavailable(f"GitHub network request failed: {exc}") from exc
        if response.status_code >= 400:
            detail = response.text[:500]
            raise ProviderUnavailable(f"GitHub returned {response.status_code}: {detail}")
        return response.json()

    async def validate_repository(self, token: str | None, owner: str, name: str, demo: bool = False) -> dict[str, Any]:
        if demo:
            now = datetime.now(timezone.utc).isoformat()
            return {"full_name": f"{owner}/{name}", "owner": owner, "name": name, "description": "A clearly labeled demo repository for previewing the review workflow.", "default_branch": "main", "language": "TypeScript", "stargazers_count": 128, "forks_count": 14, "open_issues_count": 7, "updated_at": now, "provider_mode": "demo"}
        if not token:
            raise ProviderUnavailable("A GitHub Personal Access Token is required when demo mode is disabled")
        return await self._request("GET", f"{self.settings.github_api_url}/repos/{owner}/{name}", token)

    async def list_issues(self, repository: Any, state: str = "open", search: str = "") -> list[dict[str, Any]]:
        token = repository.token
        if repository.provider_mode == "demo":
            issues = [
                {"number": 124, "title": "Login fails when password contains special characters", "body": "Users report authentication errors when passwords contain Unicode or shell-sensitive characters. Please inspect password validation and token issuance.", "state": "open", "labels": [{"name": "bug"}, {"name": "authentication"}], "user": {"login": "demo-contributor"}, "comments": 4, "created_at": "2026-09-18T10:00:00Z", "updated_at": "2026-10-01T15:40:00Z", "html_url": "https://github.com/demo/issueagent/issues/124"},
                {"number": 119, "title": "Add retry handling to repository sync", "body": "Transient GitHub errors should be retried with a bounded backoff.", "state": "open", "labels": [{"name": "enhancement"}], "user": {"login": "demo-maintainer"}, "comments": 2, "created_at": "2026-09-01T11:00:00Z", "updated_at": "2026-09-28T09:20:00Z", "html_url": "https://github.com/demo/issueagent/issues/119"},
                {"number": 101, "title": "Document local test commands", "body": "Make the supported verification commands visible to contributors.", "state": "closed", "labels": [{"name": "documentation"}], "user": {"login": "demo-maintainer"}, "comments": 1, "created_at": "2026-08-12T08:00:00Z", "updated_at": "2026-09-02T12:00:00Z", "html_url": "https://github.com/demo/issueagent/issues/101"},
            ]
            return [i for i in issues if (state == "all" or i["state"] == state) and (not search or search.lower() in (i["title"] + " " + i["body"]).lower() or search == str(i["number"]))]
        params = {"state": state, "per_page": 50, "sort": "updated", "direction": "desc"}
        data = await self._request("GET", f"{self.settings.github_api_url}/repos/{repository.owner}/{repository.name}/issues", token, params=params)
        return [item for item in data if "pull_request" not in item and (not search or search.lower() in (item.get("title", "") + " " + item.get("body", "")).lower() or search == str(item.get("number")))]

    async def get_issue(self, repository: Any, number: int) -> dict[str, Any]:
        if repository.provider_mode == "demo":
            for issue in await self.list_issues(repository, "all"):
                if issue["number"] == number:
                    issue["comments_data"] = [{"author": "demo-reviewer", "body": "Could we add a regression test for the edge case?", "created_at": "2026-09-22T12:30:00Z"}]
                    return issue
            raise ProviderUnavailable("Demo issue was not found")
        issue = await self._request("GET", f"{self.settings.github_api_url}/repos/{repository.owner}/{repository.name}/issues/{number}", repository.token)
        issue["comments_data"] = await self._request("GET", f"{self.settings.github_api_url}/repos/{repository.owner}/{repository.name}/issues/{number}/comments", repository.token, params={"per_page": 50})
        return issue

    async def search_code(self, repository: Any, query: str) -> list[dict[str, Any]]:
        if repository.provider_mode == "demo":
            return [{"name": "security.py", "path": "backend/app/core/security.py", "score": 1.0}, {"name": "auth.py", "path": "backend/app/api/auth.py", "score": 0.92}, {"name": "test_auth.py", "path": "backend/app/tests/test_auth.py", "score": 0.75}]
        data = await self._request("GET", f"{self.settings.github_api_url}/search/code", repository.token, params={"q": f"{query} repo:{repository.full_name}", "per_page": 20})
        return data.get("items", [])

    async def get_file(self, repository: Any, path: str, ref: str | None = None) -> str:
        if repository.provider_mode == "demo":
            demo_files = {
                "backend/app/core/security.py": "def verify_password(password: str, hashed: str) -> bool:\n    return password_hash.verify(password, hashed)\n\n\ndef create_access_token(subject: str) -> str:\n    return jwt.encode({\"sub\": subject}, settings.jwt_secret, algorithm=\"HS256\")\n",
                "backend/app/api/auth.py": "@router.post(\"/login\")\nasync def login(payload: LoginRequest):\n    user = authenticate(payload.email, payload.password)\n    return issue_token(user)\n",
                "backend/app/tests/test_auth.py": "def test_special_character_password():\n    assert login(password=\"p@ss:word/with spaces\")\n",
            }
            return demo_files.get(path, "# Demo source context\n\n# Relevant implementation will be retrieved from GitHub in live mode.\n")
        params = {"ref": ref} if ref else {}
        data = await self._request("GET", f"{self.settings.github_api_url}/repos/{repository.owner}/{repository.name}/contents/{path}", repository.token, params=params)
        import base64
        return base64.b64decode(data["content"].replace("\n", "")).decode("utf-8", errors="replace")

    async def create_branch(self, repository: Any, branch: str) -> str:
        if repository.provider_mode == "demo":
            return f"demo-ref-{branch}"
        base = await self._request("GET", f"{self.settings.github_api_url}/repos/{repository.owner}/{repository.name}/git/ref/heads/{repository.default_branch}", repository.token)
        await self._request("POST", f"{self.settings.github_api_url}/repos/{repository.owner}/{repository.name}/git/refs", repository.token, json={"ref": f"refs/heads/{branch}", "sha": base["object"]["sha"]})
        return base["object"]["sha"]

    async def upsert_file(self, repository: Any, branch: str, path: str, content: str, message: str) -> str:
        if repository.provider_mode == "demo":
            return "demo-commit-sha"
        import base64
        current = None
        try:
            current = await self._request("GET", f"{self.settings.github_api_url}/repos/{repository.owner}/{repository.name}/contents/{path}", repository.token, params={"ref": branch})
        except ProviderUnavailable:
            pass
        payload: dict[str, Any] = {"message": message, "content": base64.b64encode(content.encode()).decode(), "branch": branch}
        if current and current.get("sha"):
            payload["sha"] = current["sha"]
        response = await self._request("PUT", f"{self.settings.github_api_url}/repos/{repository.owner}/{repository.name}/contents/{path}", repository.token, json=payload)
        return response.get("commit", {}).get("sha", "")

    async def delete_file(self, repository: Any, branch: str, path: str, message: str) -> str:
        if repository.provider_mode == "demo":
            return "demo-delete-commit-sha"
        current = await self._request("GET", f"{self.settings.github_api_url}/repos/{repository.owner}/{repository.name}/contents/{path}", repository.token, params={"ref": branch})
        response = await self._request("DELETE", f"{self.settings.github_api_url}/repos/{repository.owner}/{repository.name}/contents/{path}", repository.token, json={"message": message, "sha": current["sha"], "branch": branch})
        return response.get("commit", {}).get("sha", "")

    async def create_draft_pr(self, repository: Any, branch: str, title: str, body: str) -> dict[str, Any]:
        if repository.provider_mode == "demo":
            return {"number": 42, "html_url": "https://github.com/demo/issueagent/pull/42", "title": title, "draft": True, "state": "open"}
        return await self._request("POST", f"{self.settings.github_api_url}/repos/{repository.owner}/{repository.name}/pulls", repository.token, json={"title": title, "head": branch, "base": repository.default_branch, "body": body, "draft": True})
