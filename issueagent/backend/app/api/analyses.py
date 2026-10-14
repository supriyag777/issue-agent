import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .deps import get_current_user
from ..core.config import get_settings
from ..db.database import get_db
from ..models.entities import Analysis, Issue, Repository, User
from ..schemas.schemas import AnalysisOut, AnalysisResult, CodeChunk
from ..services.ai_service import AIService, AIUnavailable
from ..services.code_search_service import CodeSearchService
from ..services.github_service import GitHubService, ProviderUnavailable

router = APIRouter(prefix="/api/v1", tags=["analysis"])


def output(analysis: Analysis) -> AnalysisOut:
    result = AnalysisResult.model_validate(json.loads(analysis.result_json)) if analysis.result_json and analysis.result_json != "{}" else None
    context = [CodeChunk.model_validate(item) for item in json.loads(analysis.context_json or "[]")]
    return AnalysisOut(id=analysis.id, issue_id=analysis.issue_id, repository_id=analysis.repository_id, status=analysis.status, provider_mode=analysis.provider_mode, result=result, context=context, error=analysis.error, created_at=analysis.created_at)


@router.post("/issues/{issue_id}/analyze", response_model=AnalysisOut, status_code=201)
async def analyze_issue(issue_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AnalysisOut:
    issue = db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    repository = db.get(Repository, issue.repository_id)
    if not repository or repository.user_id != user.id:
        raise HTTPException(status_code=404, detail="Issue not found")
    settings = get_settings()
    search = CodeSearchService(GitHubService(settings), settings)
    keywords, chunks = await search.search(repository, issue.title, issue.body)
    try:
        result = await AIService(settings).analyze(issue, repository, chunks, keywords)
    except AIUnavailable as exc:
        analysis = Analysis(repository_id=repository.id, issue_id=issue.id, status="unavailable", provider_mode="unavailable", result_json="{}", context_json=json.dumps(chunks), error=str(exc))
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        raise HTTPException(status_code=503, detail={"message": str(exc), "analysis_id": analysis.id})
    analysis = Analysis(repository_id=repository.id, issue_id=issue.id, status="completed", provider_mode="demo" if settings.demo_mode and not settings.openai_api_key else "live", result_json=result.model_dump_json(), context_json=json.dumps(chunks), error="")
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return output(analysis)


@router.get("/analyses/{analysis_id}", response_model=AnalysisOut)
def get_analysis(analysis_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AnalysisOut:
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    repository = db.get(Repository, analysis.repository_id)
    if not repository or repository.user_id != user.id:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return output(analysis)
