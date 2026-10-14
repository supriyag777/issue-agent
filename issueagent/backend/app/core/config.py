from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI GitHub Issue Agent"
    app_env: str = "development"
    demo_mode: bool = True
    database_url: str = "sqlite:///./issueagent.db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24
    token_encryption_key: str = ""
    github_api_url: str = "https://api.github.com"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"
    test_command: str = ""
    repository_worktree_root: str = ""
    max_code_chars: int = 18000
    max_files_per_analysis: int = 8

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]

    @property
    def github_configured(self) -> bool:
        return bool(self.github_api_url)

    @property
    def ai_configured(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
