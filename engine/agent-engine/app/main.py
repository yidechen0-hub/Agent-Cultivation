"""Agent Engine - FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.routers import chat, battle, spirit


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Startup: initialize connections
    yield
    # Shutdown: close connections


app = FastAPI(
    title="Agent Cultivation Engine",
    description="AI agent engine powering spirit cultivation, battles, and conversations",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(battle.router, prefix="/api/v1", tags=["battle"])
app.include_router(spirit.router, prefix="/api/v1", tags=["spirit"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "agent-engine"}


@app.get("/ready")
async def readiness_check() -> dict[str, str]:
    # TODO: check downstream dependencies (DB, Redis, Qdrant, NATS)
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
