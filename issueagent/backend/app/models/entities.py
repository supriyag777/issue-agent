from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    repositories: Mapped[list["Repository"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Repository(Base):
    __tablename__ = "repositories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    owner: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(200))
    full_name: Mapped[str] = mapped_column(String(321))
    description: Mapped[str] = mapped_column(Text, default="")
    default_branch: Mapped[str] = mapped_column(String(200), default="main")
    language: Mapped[str] = mapped_column(String(100), default="Unknown")
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)
    open_issues: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    github_token_encrypted: Mapped[str] = mapped_column(Text)
    provider_mode: Mapped[str] = mapped_column(String(30), default="live")
    user: Mapped[User] = relationship(back_populates="repositories")
    issues: Mapped[list["Issue"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="repository", cascade="all, delete-orphan")

    @property
    def token(self) -> str:
        from ..core.security import unseal_secret
        return unseal_secret(self.github_token_encrypted)


class Issue(Base):
    __tablename__ = "issues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), index=True)
    github_number: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text, default="")
    state: Mapped[str] = mapped_column(String(20), default="open")
    labels_json: Mapped[str] = mapped_column(Text, default="[]")
    author: Mapped[str] = mapped_column(String(200), default="unknown")
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    comments_json: Mapped[str] = mapped_column(Text, default="[]")
    html_url: Mapped[str] = mapped_column(String(1000), default="")
    repository: Mapped[Repository] = relationship(back_populates="issues")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="issue", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), index=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="completed")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    context_json: Mapped[str] = mapped_column(Text, default="[]")
    error: Mapped[str] = mapped_column(Text, default="")
    provider_mode: Mapped[str] = mapped_column(String(30), default="live")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    repository: Mapped[Repository] = relationship(back_populates="analyses")
    issue: Mapped[Issue] = relationship(back_populates="analyses")
    changes: Mapped[list["CodeChange"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")


class CodeChange(Base):
    __tablename__ = "code_changes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="proposed")
    branch_name: Mapped[str] = mapped_column(String(255), default="")
    diff: Mapped[str] = mapped_column(Text, default="")
    files_json: Mapped[str] = mapped_column(Text, default="[]")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    test_status: Mapped[str] = mapped_column(String(30), default="pending")
    test_output: Mapped[str] = mapped_column(Text, default="")
    commit_sha: Mapped[str] = mapped_column(String(100), default="")
    analysis: Mapped[Analysis] = relationship(back_populates="changes")
    pull_request: Mapped["PullRequest | None"] = relationship(back_populates="change", uselist=False, cascade="all, delete-orphan")


class PullRequest(Base):
    __tablename__ = "pull_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    change_id: Mapped[int] = mapped_column(ForeignKey("code_changes.id"), unique=True)
    github_number: Mapped[int] = mapped_column(Integer, default=0)
    url: Mapped[str] = mapped_column(String(1000), default="")
    title: Mapped[str] = mapped_column(String(500))
    draft: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    change: Mapped[CodeChange] = relationship(back_populates="pull_request")
