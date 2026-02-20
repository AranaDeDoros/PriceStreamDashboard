from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_throttle import RateLimiter

from dependencies import external_api_service, get_current_active_user
from domain.models import IngestionRun, IngestionStatus, UserDB

api_limit = RateLimiter(times=5, seconds=30)
router = APIRouter(prefix="/api/v1/ingestion",  dependencies=[Depends(api_limit)])


@router.get("/")
async def root():
    return {"message": "Welcome to the Ingestion API"}


@router.get("/runs", response_model=list[IngestionRun])
async def get_all_runs(current_user: UserDB = Depends(get_current_active_user)):
    run = await external_api_service.all()
    if not run:
        raise HTTPException(status_code=404, detail="No runs found")
    return run


@router.get("/runs/{run_id}", response_model=IngestionRun)
async def get_run_by_id(
    run_id: UUID, current_user: UserDB = Depends(get_current_active_user)
):
    run = await external_api_service.find_by_id(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/status/{status}", response_model=list[IngestionRun])
async def get_runs_by_status(
    status: IngestionStatus, current_user: UserDB = Depends(get_current_active_user)
):
    runs = await external_api_service.find_by_status(status)
    if not runs:
        raise HTTPException(status_code=404, detail="No runs found for this status")
    return runs
