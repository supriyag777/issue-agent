import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .deps import get_current_user, owned_repository
from ..core.config import get_settings
from ..db.database import get_db
from ..models.entities import Issue, Repository, User
from ..schemas.schemas import IssueOut
from ..services.github_service import GitHubService, ProviderUnavailable

router = APIRouter(prefix="/api/v1", tags=["issues"])


def map_issue(raw: dict, repo_id: int) -> dict:
    def parse_date(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return {"repository_id": repo_id, "github_number": raw["number"], "title": raw.get("title", ""), "body": raw.get("body") or "", "state": raw.get("state", "open"), "labels_json": json.dumps([label.get("name", "") for label in raw.get("labels", [])]), "author": (raw.get("user") or {}).get("login", "unknown"), "comments_count": raw.get("comments", 0), "created_at": parse_date(raw.get("created_at")), "updated_at": parse_date(raw.get("updated_at")), "comments_json": json.dumps(raw.get("comments_data", [])), "html_url": raw.get("html_url", "")}


def serialize(issue: Issue) -> IssueOut:
    return IssueOut(id=issue.id, github_number=issue.github_number, title=issue.title, body=issue.body, state=issue.state, labels=json.loads(issue.labels_json or "[]"), author=issue.author, comments_count=issue.comments_count, created_at=issue.created_at, updated_at=issue.updated_at, comments=json.loads(issue.comments_json or "[]"), html_url=issue.html_url)


@router.get("/repositories/{repository_id}/issues", response_model=list[IssueOut])
async def list_issues(repository_id: int, state: str = Query("open", pattern="^(open|closed|all)$"), search: str = "", user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[IssueOut]:
    repo = owned_repository(repository_id, user, db)
    try:
        raw_items = await GitHubService(get_settings()).list_issues(repo, state, search)
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    output: list[Issue] = []
    for raw in raw_items:
        values = map_issue(raw, repo.id)
        issue = db.query(Issue).filter(Issue.repository_id == repo.id, Issue.github_number == raw["number"]).first()
        if not issue:
            issue = Issue(**values)
        else:
            for key, value in values.items():
                if key != "repository_id":
                    setattr(issue, key, value)
        db.add(issue)
        output.append(issue)
    db.commit()
    for issue in output:
        db.refresh(issue)
    return [serialize(issue) for issue in output]


@router.get("/issues/{issue_id}", response_model=IssueOut)
async def get_issue(issue_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> IssueOut:
    issue = db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    owned_repository(issue.repository_id, user, db)
    repo = db.get(Repository, issue.repository_id)
    try:
        raw = await GitHubService(get_settings()).get_issue(repo, issue.github_number)
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    for key, value in map_issue(raw, repo.id).items():
        if key != "repository_id":
            setattr(issue, key, value)
    db.commit()
    db.refresh(issue)
    return serialize(issue)
