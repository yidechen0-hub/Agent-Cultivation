"""Agent Engine - FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.routers import chat, battle, spirit
from app.dependencies import init_services


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Startup: initialize service instances
    await init_services()
    yield
    # Shutdown: cleanup (connections auto-close)


app = FastAPI(
    title="Agent Cultivation Engine",
    description="AI agent engine powering spirit cultivation, battles, and conversations",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(battle.router, prefix="/api/v1", tags=["battle"])
app.include_router(spirit.router, prefix="/api/v1", tags=["spirit"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "agent-engine"}


@app.get("/ready")
async def readiness_check() -> dict[str, str]:
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8100, reload=True)
