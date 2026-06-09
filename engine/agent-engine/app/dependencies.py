"""Dependency injection - manages global service instances."""

import os
from functools import lru_cache

from app.services.llm_router import LLMRouter
from app.services.memory_manager import MemoryManager
from app.services.prompt_builder import PromptBuilder
from app.services.memory_writer import MemoryWriter
from app.services.embedding import EmbeddingService
from app.services.judge_engine import JudgeEngine


@lru_cache
def get_config() -> dict:
    return {
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "database_url": os.getenv("DATABASE_URL", "postgres://dev:dev123@localhost:5432/sanrenxing"),
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "qdrant_url": os.getenv("QDRANT_URL", "http://localhost:6333"),
        "nats_url": os.getenv("NATS_URL", "nats://localhost:4222"),
    }


_llm_router: LLMRouter | None = None
_memory_manager: MemoryManager | None = None
_prompt_builder: PromptBuilder | None = None
_memory_writer: MemoryWriter | None = None
_embedding_service: EmbeddingService | None = None
_judge_engine: JudgeEngine | None = None


async def init_services():
    """Initialize all service instances. Call during app startup."""
    global _llm_router, _memory_manager, _prompt_builder, _memory_writer
    global _embedding_service, _judge_engine

    config = get_config()

    _llm_router = LLMRouter(
        anthropic_api_key=config["anthropic_api_key"],
        openai_api_key=config["openai_api_key"],
    )

    _memory_manager = MemoryManager(qdrant_url=config["qdrant_url"])
    await _memory_manager.ensure_collection()

    _prompt_builder = PromptBuilder()

    _embedding_service = EmbeddingService(api_key=config["openai_api_key"])

    _memory_writer = MemoryWriter(
        llm_router=_llm_router,
        memory_manager=_memory_manager,
    )

    _judge_engine = JudgeEngine(_llm_router)


def get_llm_router() -> LLMRouter:
    assert _llm_router is not None, "Services not initialized"
    return _llm_router


def get_memory_manager() -> MemoryManager:
    assert _memory_manager is not None, "Services not initialized"
    return _memory_manager


def get_prompt_builder() -> PromptBuilder:
    assert _prompt_builder is not None, "Services not initialized"
    return _prompt_builder


def get_memory_writer() -> MemoryWriter:
    assert _memory_writer is not None, "Services not initialized"
    return _memory_writer


def get_embedding_service() -> EmbeddingService:
    assert _embedding_service is not None, "Services not initialized"
    return _embedding_service


def get_judge_engine() -> JudgeEngine:
    assert _judge_engine is not None, "Services not initialized"
    return _judge_engine
