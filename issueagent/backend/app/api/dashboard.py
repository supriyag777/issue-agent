import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .changes import serialize as serialize_change
from .deps import get_current_user, owned_repository
from .issues import serialize as serialize_issue
from ..db.database import get_db
from ..models.entities import Analysis, CodeChange, Issue, PullRequest, Repository, User
from ..schemas.schemas import AnalysisOut, DashboardOut, PullRequestOut, RepositoryOut

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


def analysis_out(item: Analysis) -> AnalysisOut:
    from ..schemas.schemas import AnalysisResult, CodeChunk
    return AnalysisOut(id=item.id, issue_id=item.issue_id, repository_id=item.repository_id, status=item.status, provider_mode=item.provider_mode, result=AnalysisResult.model_validate(json.loads(item.result_json)) if item.result_json != "{}" else None, context=[CodeChunk.model_validate(x) for x in json.loads(item.context_json or "[]")], error=item.error, created_at=item.created_at)


@router.get("/repositories/{repository_id}/dashboard", response_model=DashboardOut)
def dashboard(repository_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DashboardOut:
    repo = owned_repository(repository_id, user, db)
    issues = db.query(Issue).filter(Issue.repository_id == repo.id).order_by(Issue.updated_at.desc()).limit(6).all()
    analyses = db.query(Analysis).filter(Analysis.repository_id == repo.id).order_by(Analysis.created_at.desc()).limit(6).all()
    changes = db.query(CodeChange).join(Analysis).filter(Analysis.repository_id == repo.id).order_by(CodeChange.id.desc()).limit(6).all()
    prs = [item.pull_request for item in changes if item.pull_request]
    return DashboardOut(repository=RepositoryOut.model_validate(repo), stats={"open_issues": repo.open_issues, "recent_issues": len(issues), "analyses": db.query(Analysis).filter(Analysis.repository_id == repo.id).count(), "solutions": db.query(CodeChange).join(Analysis).filter(Analysis.repository_id == repo.id).count(), "draft_prs": len(prs)}, recent_issues=[serialize_issue(item) for item in issues], recent_analyses=[analysis_out(item) for item in analyses], changes=[serialize_change(item) for item in changes], pull_requests=[PullRequestOut(id=pr.id, change_id=pr.change_id, github_number=pr.github_number, url=pr.url, title=pr.title, draft=pr.draft, status=pr.status, created_at=pr.created_at) for pr in prs])
