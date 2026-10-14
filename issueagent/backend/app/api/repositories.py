import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .deps import get_current_user, owned_repository
from ..core.config import get_settings
from ..core.security import seal_secret
from ..db.database import get_db
from ..models.entities import Repository, User
from ..schemas.schemas import RepositoryConnect, RepositoryOut
from ..services.github_service import GitHubService, ProviderUnavailable

router = APIRouter(prefix="/api/v1/repositories", tags=["repositories"])
log = logging.getLogger(__name__)


@router.get("", response_model=list[RepositoryOut])
def list_repositories(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Repository]:
    return db.query(Repository).filter(Repository.user_id == user.id).order_by(Repository.updated_at.desc()).all()


@router.post("/connect", response_model=RepositoryOut, status_code=201)
async def connect_repository(payload: RepositoryConnect, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Repository:
    settings = get_settings()
    demo = payload.demo_mode
    service = GitHubService(settings)
    try:
        info = await service.validate_repository(payload.github_token, payload.owner.strip(), payload.name.strip(), demo=demo)
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    existing = db.query(Repository).filter(Repository.user_id == user.id, Repository.full_name == info["full_name"]).first()
    repository = existing or Repository(user_id=user.id, full_name=info["full_name"], github_token_encrypted="")
    owner_info = info.get("owner")
    owner_name = owner_info.get("login") if isinstance(owner_info, dict) else owner_info
    repository.owner = owner_name or payload.owner
    repository.name = info.get("name", payload.name)
    repository.description = info.get("description") or ""
    repository.default_branch = info.get("default_branch") or info.get("default_branch", "main")
    repository.language = info.get("language") or "Unknown"
    repository.stars = info.get("stargazers_count", 0)
    repository.forks = info.get("forks_count", 0)
    repository.open_issues = info.get("open_issues_count", 0)
    repository.provider_mode = info.get("provider_mode", "live")
    repository.github_token_encrypted = seal_secret(payload.github_token or "demo-token")
    db.add(repository)
    db.commit()
    db.refresh(repository)
    return repository


@router.get("/{repository_id}", response_model=RepositoryOut)
def get_repository(repository_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Repository:
    return owned_repository(repository_id, user, db)


@router.delete("/{repository_id}")
def disconnect_repository(repository_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    repository = owned_repository(repository_id, user, db)
    db.delete(repository)
    db.commit()
    return {"status": "disconnected"}
