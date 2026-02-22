import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import datetime as _dt
import os
from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import config.settings

# Required environment variables for module imports in dependencies/config
SECRET_KEY = config.settings.SECRET_KEY
ALGORITHM = config.settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
EXTERNAL_API_URL = config.settings.EXTERNAL_API_URL
OAUTH2_SCHEME = config.settings.OAUTH2_SCHEME
DATABASE_URL = config.settings.DATABASE_URL
HOME_URL = config.settings.HOME_URL
LOCAL_URL = config.settings.LOCAL_URL
os.environ.setdefault("SECRET_KEY", SECRET_KEY)
os.environ.setdefault("ALGORITHM", ALGORITHM)
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", str(ACCESS_TOKEN_EXPIRE_MINUTES))
os.environ.setdefault("EXTERNAL_API_URL", EXTERNAL_API_URL)
os.environ.setdefault("DATABASE_URL", DATABASE_URL)
os.environ.setdefault("HOME_URL", HOME_URL)
os.environ.setdefault("LOCAL_URL", LOCAL_URL)

# Compat for Python <3.11 when app imports `from datetime import UTC`
if not hasattr(_dt, "UTC"):
    _dt.UTC = _dt.UTC


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
