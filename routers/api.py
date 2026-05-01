from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_throttle import RateLimiter

from dependencies import external_api_service, get_current_active_user
from domain.models import IngestionRun, IngestionStatus, Platform, UserDB

api_limit = RateLimiter(times=60, seconds=60)
router = APIRouter(prefix="/api/v1/ingestion", dependencies=[Depends(api_limit)])


@router.get("/")
async def root():
    return {"message": "Welcome to the Ingestion API"}


@router.get("/runs", response_model=list[IngestionRun])
async def get_all_runs(current_user: UserDB = Depends(get_current_active_user)):
    run = await external_api_service.all()
    if not run:
        return []
    return run


@router.get("/runs/{run_id}", response_model=IngestionRun)
async def get_run_by_id(
    run_id: UUID, current_user: UserDB = Depends(get_current_active_user)
):
    run = await external_api_service.find_by_id(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/runs/platform/{platform}", response_model=list[IngestionRun])
async def get_runs_by_platform(
    platform: str, current_user: UserDB = Depends(get_current_active_user)
):
    runs = await external_api_service.find_by_platform(platform)
    return runs


@router.get("/platforms", response_model=list[Platform])
async def get_all_platforms(current_user: UserDB = Depends(get_current_active_user)):
    platforms = await external_api_service.get_all_platforms()
    return platforms


@router.get("/status/{status}", response_model=list[IngestionRun])
async def get_runs_by_status(
    status: IngestionStatus, current_user: UserDB = Depends(get_current_active_user)
):
    runs = await external_api_service.find_by_status(status)
    return runs
