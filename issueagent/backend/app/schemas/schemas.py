from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RepositoryConnect(BaseModel):
    github_token: str | None = Field(default=None, min_length=1)
    owner: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)
    demo_mode: bool = False


class RepositoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner: str
    name: str
    full_name: str
    description: str
    default_branch: str
    language: str
    stars: int
    forks: int
    open_issues: int
    updated_at: datetime
    provider_mode: str


class IssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    github_number: int
    title: str
    body: str
    state: str
    labels: list[str]
    author: str
    comments_count: int
    created_at: datetime
    updated_at: datetime
    comments: list[dict[str, Any]] = []
    html_url: str


class CodeChunk(BaseModel):
    filename: str
    language: str
    start_line: int
    end_line: int
    code: str
    relevance: float = 0


class FileChange(BaseModel):
    path: str
    change_type: Literal["add", "modify", "delete"] = "modify"
    explanation: str = ""
    patch: str = ""
    new_content: str | None = None


class AnalysisResult(BaseModel):
    summary: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    root_cause: str
    affected_files: list[str] = []
    affected_functions: list[str] = []
    solution: str
    implementation_plan: list[str] = []
    testing_plan: list[str] = []
    risk_level: Literal["low", "medium", "high"] = "medium"
    keywords: list[str] = []
    technologies: list[str] = []
    file_changes: list[FileChange] = []


class AnalysisOut(BaseModel):
    id: int
    issue_id: int
    repository_id: int
    status: str
    provider_mode: str
    result: AnalysisResult | None = None
    context: list[CodeChunk] = []
    error: str = ""
    created_at: datetime


class ApprovalRequest(BaseModel):
    approved: bool


class TestRunOut(BaseModel):
    status: str
    passed: bool
    output: str


class ChangeOut(BaseModel):
    id: int
    analysis_id: int
    status: str
    branch_name: str
    diff: str
    files: list[FileChange]
    approved_at: datetime | None
    test_status: str
    test_output: str
    commit_sha: str
    pull_request: dict[str, Any] | None = None


class PullRequestOut(BaseModel):
    id: int
    change_id: int
    github_number: int
    url: str
    title: str
    draft: bool
    status: str
    created_at: datetime


class DashboardOut(BaseModel):
    repository: RepositoryOut
    stats: dict[str, int]
    recent_issues: list[IssueOut]
    recent_analyses: list[AnalysisOut]
    changes: list[ChangeOut]
    pull_requests: list[PullRequestOut]


class HealthOut(BaseModel):
    status: str
    database: str
    github: str
    ai: str
    demo_mode: bool
