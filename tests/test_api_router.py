import uuid
from datetime import datetime

from domain.models import IngestionStatus
from routers import api as api_router


class StubExternalApi:
    def __init__(self, all_runs=None, by_id=None, by_status=None):
        self._all = all_runs if all_runs is not None else []
        self._by_id = by_id
        self._by_status = by_status if by_status is not None else []

    async def all(self):
        return self._all

    async def find_by_id(self, run_id):
        return self._by_id

    async def find_by_status(self, status):
        return self._by_status


def _sample_run_dict(run_id: str):
    return {
        "id": run_id,
        "startedAt": datetime(2026, 1, 1, 12, 0, 0).isoformat(),
        "finishedAt": None,
        "status": "Running",
    }


def test_root_returns_welcome(client):
    response = client.get("/api/v1/ingestion/")

    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to the Ingestion API"


def test_get_all_runs_returns_data(client, monkeypatch):
    run = _sample_run_dict(str(uuid.uuid4()))
    monkeypatch.setattr(
        api_router, "external_api_service", StubExternalApi(all_runs=[run])
    )

    response = client.get(
        "/api/v1/ingestion/runs", headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_all_runs_returns_404_when_empty(client, monkeypatch):
    monkeypatch.setattr(
        api_router, "external_api_service", StubExternalApi(all_runs=[])
    )

    response = client.get(
        "/api/v1/ingestion/runs", headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_run_by_id_returns_one(client, monkeypatch):
    run = _sample_run_dict(str(uuid.uuid4()))
    monkeypatch.setattr(api_router, "external_api_service", StubExternalApi(by_id=run))

    response = client.get(
        f"/api/v1/ingestion/runs/{run['id']}", headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 200
    assert response.json()["id"] == run["id"]


def test_get_run_by_id_returns_404_when_missing(client, monkeypatch):
    run_id = str(uuid.uuid4())
    monkeypatch.setattr(api_router, "external_api_service", StubExternalApi(by_id=None))

    response = client.get(
        f"/api/v1/ingestion/runs/{run_id}", headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 404


def test_get_runs_by_status_returns_data(client, monkeypatch):
    run = _sample_run_dict(str(uuid.uuid4()))
    monkeypatch.setattr(
        api_router, "external_api_service", StubExternalApi(by_status=[run])
    )

    response = client.get(
        f"/api/v1/ingestion/status/{IngestionStatus.RUNNING.value}",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 200
    assert response.json()[0]["status"] == "Running"


def test_get_runs_by_status_returns_404_when_empty(client, monkeypatch):
    monkeypatch.setattr(
        api_router, "external_api_service", StubExternalApi(by_status=[])
    )

    response = client.get(
        f"/api/v1/ingestion/status/{IngestionStatus.FAILED.value}",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 200
    assert response.json() == []
