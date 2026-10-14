import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_issueagent.db"
os.environ["DEMO_MODE"] = "true"
os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough"
os.environ["TOKEN_ENCRYPTION_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""

from fastapi.testclient import TestClient
import pytest

from ..main import app
from ..db.database import Base, engine
from ..models import entities  # noqa: F401


@pytest.fixture(scope="session")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Path("test_issueagent.db").unlink(missing_ok=True)
