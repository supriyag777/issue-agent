from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .deps import get_current_user
from ..core.security import create_access_token, hash_password, verify_password
from ..db.database import get_db
from ..models.entities import User
from ..schemas.schemas import AuthResponse, LoginRequest, UserCreate, UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> AuthResponse:
    email = payload.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return AuthResponse(access_token=create_access_token(str(user.id), user.email, user.name), user=user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return AuthResponse(access_token=create_access_token(str(user.id), user.email, user.name), user=user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/logout")
def logout(_: User = Depends(get_current_user)) -> dict[str, str]:
    return {"status": "ok", "message": "Client session can be cleared safely"}
