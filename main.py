from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config.settings
from dependencies import external_api_service
from routers import api, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    #
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")
    await external_api_service.close()


app = FastAPI(lifespan=lifespan)

cors_origins = [config.settings.HOME_URL, config.settings.LOCAL_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, tags=["api"])
app.include_router(auth.router, tags=["auth"])
