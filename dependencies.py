from uuid import UUID

import httpx
from fastapi import Depends

import config.settings
from domain.models import IngestionRun, IngestionStatus, Platform, UserDB
from services.TokenService import TokenService
from services.UserService import is_valid_request

# --- Configuration ---
SECRET_KEY = config.settings.SECRET_KEY
ALGORITHM = config.settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
EXTERNAL_API_URL = config.settings.EXTERNAL_API_URL
OAUTH2_SCHEME = config.settings.OAUTH2_SCHEME

# --- Stateless service ---
token_service = TokenService(SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES)


# --- External API Service ---
class ExternalAPIService:
    def __init__(self):
        if not EXTERNAL_API_URL:
            raise RuntimeError("EXTERNAL_API_URL is not set in .env")
        self.client = httpx.AsyncClient(base_url=EXTERNAL_API_URL)

    async def all(self) -> list[IngestionRun]:
        resp = await self.client.get("/runs")
        resp.raise_for_status()
        return [IngestionRun(**run) for run in resp.json()]

    async def find_by_id(self, run_id: UUID) -> IngestionRun | None:
        resp = await self.client.get(f"/runs/{run_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return IngestionRun(**resp.json())

    async def find_by_status(self, status: IngestionStatus) -> list[IngestionRun]:
        resp = await self.client.get(f"/status/{status}")
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return [IngestionRun(**run) for run in resp.json()]

    async def find_by_platform(self, platform: str) -> list[IngestionRun]:
        resp = await self.client.get(f"/runs/platform/{platform}")
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return [IngestionRun(**run) for run in resp.json()]

    async def get_all_platforms(self) -> list[Platform]:
        resp = await self.client.get("/platforms")
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return [Platform(**platform) for platform in resp.json()]

    async def close(self):
        await self.client.aclose()


external_api_service = ExternalAPIService()


# --- Security Dependency ---
async def get_current_active_user(user: UserDB = Depends(is_valid_request)) -> UserDB:
    return user
