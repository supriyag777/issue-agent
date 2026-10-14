from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ..core.config import get_settings

settings = get_settings()
# The managed Preview can inject a MySQL-compatible DATABASE_URL, while the
# requested production stack is PostgreSQL. Demo mode must remain bootable
# without a MySQL driver, so use the local SQLite fallback only in that mode.
database_url = settings.database_url
if database_url.startswith("mysql") and settings.demo_mode:
    database_url = "sqlite:///./issueagent.db"
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    from ..models import entities  # noqa: F401
    Base.metadata.create_all(bind=engine)
