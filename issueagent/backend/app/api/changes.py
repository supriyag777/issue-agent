import json
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .deps import get_current_user
from ..core.config import get_settings
from ..db.database import get_db
from ..models.entities import Analysis, CodeChange, PullRequest, Repository, User
from ..schemas.schemas import ApprovalRequest, ChangeOut, FileChange, TestRunOut
from ..services.github_service import GitHubService, ProviderUnavailable
from ..services.patch_service import UnsafePatch, content_for, make_diff, validate_changes
from ..services.test_runner import apply_changes_to_worktree, run_tests

router = APIRouter(prefix="/api/v1", tags=["changes"])


def owned_change(change_id: int, user: User, db: Session) -> tuple[CodeChange, Analysis, Repository]:
    change = db.get(CodeChange, change_id)
    if not change:
        raise HTTPException(status_code=404, detail="Proposed change not found")
    analysis = db.get(Analysis, change.analysis_id)
    repo = db.get(Repository, analysis.repository_id) if analysis else None
    if not analysis or not repo or repo.user_id != user.id:
        raise HTTPException(status_code=404, detail="Proposed change not found")
    return change, analysis, repo


def serialize(change: CodeChange) -> ChangeOut:
    pr = change.pull_request
    return ChangeOut(id=change.id, analysis_id=change.analysis_id, status=change.status, branch_name=change.branch_name, diff=change.diff, files=[FileChange.model_validate(item) for item in json.loads(change.files_json or "[]")], approved_at=change.approved_at, test_status=change.test_status, test_output=change.test_output, commit_sha=change.commit_sha, pull_request={"id": pr.id, "number": pr.github_number, "url": pr.url, "draft": pr.draft, "status": pr.status} if pr else None)


@router.get("/analyses/{analysis_id}/change", response_model=ChangeOut)
async def get_change(analysis_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ChangeOut:
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    repo = db.get(Repository, analysis.repository_id)
    if not repo or repo.user_id != user.id:
        raise HTTPException(status_code=404, detail="Analysis not found")
    change = db.query(CodeChange).filter(CodeChange.analysis_id == analysis_id).first()
    if not change:
        result = json.loads(analysis.result_json or "{}")
        files = [FileChange.model_validate(item) for item in result.get("file_changes", [])]
        try:
            files = validate_changes(files)
        except UnsafePatch as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        originals = {}
        github = GitHubService(get_settings())
        for file in files:
            try:
                originals[file.path] = await github.get_file(repo, file.path, repo.default_branch)
            except ProviderUnavailable:
                originals[file.path] = ""
        diff = make_diff(files, originals)
        change = CodeChange(analysis_id=analysis.id, status="proposed", files_json=json.dumps([item.model_dump() for item in files]), diff=diff)
        db.add(change)
        db.commit()
        db.refresh(change)
    return serialize(change)


@router.post("/changes/{change_id}/approve", response_model=ChangeOut)
def approve_change(change_id: int, payload: ApprovalRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ChangeOut:
    change, _, _ = owned_change(change_id, user, db)
    if not payload.approved:
        change.status = "rejected"
    elif change.status != "proposed":
        raise HTTPException(status_code=409, detail="Only a proposed change can be approved")
    else:
        change.status = "approved"
        change.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(change)
    return serialize(change)


@router.post("/changes/{change_id}/branch", response_model=ChangeOut)
async def create_branch(change_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ChangeOut:
    change, analysis, repo = owned_change(change_id, user, db)
    if change.status != "approved":
        raise HTTPException(status_code=409, detail="User approval is required before branch creation")
    if repo.default_branch in change.branch_name or change.branch_name == repo.default_branch:
        raise HTTPException(status_code=422, detail="Default branch mutation is not allowed")
    branch = f"ai-issue/{analysis.issue_id}-{secrets.token_hex(3)}"
    try:
        await GitHubService(get_settings()).create_branch(repo, branch)
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    change.branch_name = branch
    change.status = "branch_created"
    db.commit()
    db.refresh(change)
    return serialize(change)


@router.post("/changes/{change_id}/validate", response_model=TestRunOut)
async def validate_change(change_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TestRunOut:
    change, analysis, repo = owned_change(change_id, user, db)
    if change.status != "branch_created":
        raise HTTPException(status_code=409, detail="Create an approved non-default branch before validation")
    files = [FileChange.model_validate(item) for item in json.loads(change.files_json or "[]")]
    try:
        for file in files:
            if file.change_type != "delete":
                original = await GitHubService(get_settings()).get_file(repo, file.path, repo.default_branch)
                content_for(file, original)
    except (UnsafePatch, ProviderUnavailable) as exc:
        change.test_status = "failed"
        change.test_output = str(exc)
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc))
    settings = get_settings()
    if settings.test_command and settings.repository_worktree_root:
        try:
            apply_changes_to_worktree(settings.repository_worktree_root, files)
        except (UnsafePatch, OSError) as exc:
            change.test_status = "failed"
            change.test_output = f"Unable to prepare configured test worktree: {exc}"
            db.commit()
            raise HTTPException(status_code=422, detail=change.test_output)
    test_result = run_tests(settings)
    if not test_result.passed:
        change.test_status = test_result.status
        change.test_output = test_result.output
        db.commit()
        raise HTTPException(status_code=422, detail=test_result.output)
    change.test_status = test_result.status
    change.test_output = test_result.output
    change.status = "validated"
    db.commit()
    return TestRunOut(status=test_result.status, passed=test_result.passed, output=test_result.output)


@router.post("/changes/{change_id}/commit", response_model=ChangeOut)
async def commit_change(change_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ChangeOut:
    change, _, repo = owned_change(change_id, user, db)
    if change.status != "validated" or change.test_status != "passed":
        raise HTTPException(status_code=409, detail="Successful validation is required before commit")
    files = [FileChange.model_validate(item) for item in json.loads(change.files_json or "[]")]
    sha = ""
    try:
        github = GitHubService(get_settings())
        for file in files:
            if file.change_type == "delete":
                sha = await github.delete_file(repo, change.branch_name, file.path, f"fix: address issue analysis {change.analysis_id}")
                continue
            original = await github.get_file(repo, file.path, repo.default_branch)
            sha = await github.upsert_file(repo, change.branch_name, file.path, content_for(file, original), f"fix: address issue analysis {change.analysis_id}")
    except (ProviderUnavailable, UnsafePatch) as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    change.commit_sha = sha or "local-validation-commit"
    change.status = "committed"
    db.commit()
    db.refresh(change)
    return serialize(change)


@router.post("/changes/{change_id}/draft-pr", response_model=ChangeOut)
async def create_draft_pr(change_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ChangeOut:
    change, analysis, repo = owned_change(change_id, user, db)
    if change.status != "committed":
        raise HTTPException(status_code=409, detail="A successful commit is required before creating a draft PR")
    issue_title = (analysis.issue.title if analysis.issue else "Issue")
    try:
        result = await GitHubService(get_settings()).create_draft_pr(repo, change.branch_name, f"Draft fix: {issue_title}", f"Generated from AI analysis {analysis.id}.\n\nHuman review is required. This PR is intentionally draft.")
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    pr = PullRequest(change_id=change.id, github_number=result.get("number", 0), url=result.get("html_url", ""), title=result.get("title", issue_title), draft=True, status="draft")
    db.add(pr)
    change.status = "pr_created"
    db.commit()
    db.refresh(change)
    return serialize(change)
