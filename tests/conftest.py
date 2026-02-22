import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import os
from dataclasses import dataclass
import datetime as _dt

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Required environment variables for module imports in dependencies/config
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("EXTERNAL_API_URL", "http://example.test")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("HOME_URL", "http://localhost")
os.environ.setdefault("LOCAL_URL", "http://127.0.0.1")

# Compat for Python <3.11 when app imports `from datetime import UTC`
if not hasattr(_dt, "UTC"):
    _dt.UTC = _dt.timezone.utc


from dependencies import get_current_active_user  # noqa: E402
from routers import api, auth  # noqa: E402


@dataclass
class ActiveUser:
    username: str = "tester"
    is_active: bool = True


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(api.router)

    async def _current_user_override():
        return ActiveUser()

    app.dependency_overrides[get_current_active_user] = _current_user_override
    app.dependency_overrides[auth.auth_limit] = lambda: None
    app.dependency_overrides[api.api_limit] = lambda: None
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
