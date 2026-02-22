from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from db.DB import get_db
from dependencies import token_service


class FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._result


class FakeDB:
    def __init__(self, query_map=None):
        self.query_map = query_map or {}
        self.added = []
        self.committed = False

    def query(self, model):
        return FakeQuery(self.query_map.get(model))

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True


@pytest.fixture
def auth_app(app):
    return app


def test_login_returns_tokens_for_valid_credentials(auth_app, client):
    hashed_password = token_service.hash_password("pass-123")
    user = SimpleNamespace(id="user-1", username="alice", hashed_password=hashed_password)
    fake_db = FakeDB()

    from services.UserService import UserService

    original = UserService.get_user
    UserService.get_user = lambda self, username: user
    auth_app.dependency_overrides[get_db] = lambda: fake_db

    response = client.post(
        "/api/v1/auth/token",
        data={"username": "alice", "password": "pass-123"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )

    UserService.get_user = original

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body
    assert "refresh_token" in body
    assert fake_db.committed is True
    assert len(fake_db.added) == 1


def test_login_rejects_invalid_credentials(auth_app, client):
    from services.UserService import UserService

    original = UserService.get_user
    UserService.get_user = lambda self, username: None
    auth_app.dependency_overrides[get_db] = lambda: FakeDB()

    response = client.post(
        "/api/v1/auth/token",
        data={"username": "bad", "password": "bad"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )

    UserService.get_user = original

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_refresh_returns_new_access_token(auth_app, client):
    from domain.models import RefreshTokenDB, UserDB

    refresh = "my-refresh-token"
    refresh_db = SimpleNamespace(
        user_id="user-1",
        expires_at=datetime.utcnow() + timedelta(days=1),
        is_revoked=False,
    )
    user = SimpleNamespace(id="user-1", username="alice")
    fake_db = FakeDB({RefreshTokenDB: refresh_db, UserDB: user})

    auth_app.dependency_overrides[get_db] = lambda: fake_db

    response = client.post("/api/v1/auth/refresh", params={"refresh_token": refresh})

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_refresh_rejects_expired_token(auth_app, client):
    from domain.models import RefreshTokenDB

    refresh_db = SimpleNamespace(
        user_id="user-1",
        expires_at=datetime.utcnow() - timedelta(minutes=1),
        is_revoked=False,
    )
    fake_db = FakeDB({RefreshTokenDB: refresh_db})
    auth_app.dependency_overrides[get_db] = lambda: fake_db

    response = client.post("/api/v1/auth/refresh", params={"refresh_token": "expired"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"


def test_logout_revokes_token(auth_app, client):
    from domain.models import RefreshTokenDB

    refresh_db = SimpleNamespace(is_revoked=False)
    fake_db = FakeDB({RefreshTokenDB: refresh_db})
    auth_app.dependency_overrides[get_db] = lambda: fake_db

    response = client.post("/api/v1/auth/logout", params={"refresh_token": "valid"})

    assert response.status_code == 200
    assert refresh_db.is_revoked is True
    assert fake_db.committed is True


def test_logout_rejects_missing_token(auth_app, client):
    fake_db = FakeDB()
    auth_app.dependency_overrides[get_db] = lambda: fake_db

    response = client.post("/api/v1/auth/logout", params={"refresh_token": "missing"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid token"


def test_register_creates_user(auth_app, client):
    from services.UserService import get_user_service

    class StubUserService:
        def get_user(self, username):
            return None

        def create_user(self, user_db):
            user_db.id = "f938d755-24c2-4fe4-92ad-6c40f42dc95d"
            user_db.role = "USER"
            user_db.is_active = True
            user_db.is_superuser = False
            user_db.created_at = datetime.now(timezone.utc)
            return user_db

    auth_app.dependency_overrides[get_user_service] = lambda: StubUserService()
    auth_app.dependency_overrides[get_db] = lambda: FakeDB()

    response = client.post(
        "/api/v1/auth/register",
        json={"username": "new-user", "email": "new@user.com", "password": "abc123"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "new-user"


def test_register_rejects_duplicate_username(auth_app, client):
    from services.UserService import get_user_service

    class StubUserService:
        def get_user(self, username):
            return SimpleNamespace(username=username)

    auth_app.dependency_overrides[get_user_service] = lambda: StubUserService()
    auth_app.dependency_overrides[get_db] = lambda: FakeDB()

    response = client.post(
        "/api/v1/auth/register",
        json={"username": "taken", "email": "taken@user.com", "password": "abc123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"
