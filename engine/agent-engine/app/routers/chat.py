"""Chat router - handles conversation streaming with tool/proxy mode support."""

import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.dependencies import (
    get_llm_router,
    get_memory_manager,
    get_prompt_builder,
    get_memory_writer,
    get_embedding_service,
)
from app.services.llm_router import Scene
from app.services.prompt_builder import SpiritProfile, OwnerProfile

logger = logging.getLogger(__name__)

router = APIRouter()


class SendMessageRequest(BaseModel):
    content: str
    mode: str = "tool"  # "tool" or "proxy"


class ConversationContext(BaseModel):
    """Loaded from database in production; for now, passed or mocked."""
    spirit_id: str
    spirit_name: str = "AAgent"
    skills: list[dict] = []
    owner_profile: dict = {}
    history: list[dict] = []


# In-memory conversation store (replace with Redis/DB in production)
_conversations: dict[str, dict] = {}


def _get_or_create_conversation(conversation_id: str) -> dict:
    if conversation_id not in _conversations:
        _conversations[conversation_id] = {
            "spirit_id": "default-spirit",
            "spirit_name": "AAgent",
            "mode": "tool",
            "skills": [
                {"name": "语境造句引擎", "description": "根据目标单词生成贴近生活的语境例句"},
                {"name": "语法纠错", "description": "检查并纠正英语语法错误，解释错误原因"},
                {"name": "词根词缀分析", "description": "拆解单词构成，帮助记忆和推测词义"},
                {"name": "口语对话模拟", "description": "模拟真实英语对话场景进行口语练习"},
            ],
            "owner_profile": {
                "vocabulary_level": 4500,
                "cefr_level": "B1",
                "weak_points": ["虚拟语气", "定语从句", "时态"],
                "strong_points": ["基础词汇", "简单句型", "日常对话"],
                "study_preferences": "喜欢例句记忆法，偏好口语化表达",
                "expression_style": "简洁，偏口语化",
                "knowledge_graph": {
                    "grammar.tense.simple_past": 0.75,
                    "grammar.tense.past_perfect": 0.35,
                    "grammar.clause.relative": 0.4,
                    "grammar.subjunctive": 0.25,
                    "vocabulary.cet4_core": 0.85,
                    "vocabulary.cet6_core": 0.55,
                    "reading.comprehension": 0.6,
                    "writing.essay": 0.45,
                },
            },
            "history": [],
        }
    return _conversations[conversation_id]


async def _stream_chat(conversation_id: str, request: SendMessageRequest):
    """Core chat streaming logic with mode switching."""
    conv = _get_or_create_conversation(conversation_id)
    conv["mode"] = request.mode

    # Add user message to history
    conv["history"].append({"role": "user", "content": request.content})

    llm = get_llm_router()
    prompt_builder = get_prompt_builder()
    memory_mgr = get_memory_manager()
    embedding_svc = get_embedding_service()

    # 1. Retrieve relevant memories
    memories_text: list[str] = []
    try:
        query_embedding = await embedding_svc.embed(request.content)
        spirit_uuid = UUID(conv["spirit_id"]) if len(conv["spirit_id"]) > 10 else UUID(int=0)
        retrieved = await memory_mgr.retrieve(
            spirit_id=spirit_uuid,
            query_embedding=query_embedding,
            top_k=5,
        )
        memories_text = [m.memory.content for m in retrieved]
    except Exception as e:
        logger.warning(f"Memory retrieval failed (non-fatal): {e}")

    # 2. Build prompt based on mode
    spirit_profile = SpiritProfile(
        name=conv["spirit_name"],
        skills=conv["skills"],
    )

    if request.mode == "proxy":
        owner_data = conv["owner_profile"]
        owner_profile = OwnerProfile(
            vocabulary_level=owner_data.get("vocabulary_level", 0),
            cefr_level=owner_data.get("cefr_level", "A2"),
            weak_points=owner_data.get("weak_points", []),
            strong_points=owner_data.get("strong_points", []),
            study_preferences=owner_data.get("study_preferences", ""),
            expression_style=owner_data.get("expression_style", ""),
            knowledge_graph=owner_data.get("knowledge_graph", {}),
        )
        system_prompt = prompt_builder.build_proxy_prompt(
            profile=spirit_profile,
            owner=owner_profile,
            memories=memories_text,
        )
        scene = Scene.DEEP_DIALOGUE
    else:
        system_prompt = prompt_builder.build_tool_prompt(
            profile=spirit_profile,
            memories=memories_text,
        )
        scene = Scene.CASUAL_CHAT

    # 3. Prepare messages for LLM
    llm_messages = []
    for msg in conv["history"][-20:]:  # Last 20 messages as context
        llm_messages.append({"role": msg["role"], "content": msg["content"]})

    # 4. Stream response
    full_response = []
    try:
        async for chunk in llm.route_stream(
            scene=scene,
            system_prompt=system_prompt,
            messages=llm_messages,
        ):
            full_response.append(chunk)
            data = json.dumps({"delta": chunk, "finish_reason": None}, ensure_ascii=False)
            yield f"data: {data}\n\n"
    except Exception as e:
        logger.error(f"LLM streaming failed: {e}")
        error_msg = "抱歉，我暂时无法回答，请稍后再试。"
        data = json.dumps({"delta": error_msg, "finish_reason": None}, ensure_ascii=False)
        yield f"data: {data}\n\n"
        full_response.append(error_msg)

    # 5. Signal completion
    complete_text = "".join(full_response)
    done_data = json.dumps({"delta": "", "finish_reason": "stop"}, ensure_ascii=False)
    yield f"data: {done_data}\n\n"

    # 6. Save assistant message to history
    conv["history"].append({"role": "assistant", "content": complete_text})

    # 7. Trigger async memory extraction (fire-and-forget)
    asyncio.create_task(_extract_memories_background(conv, conversation_id))


async def _extract_memories_background(conv: dict, conversation_id: str):
    """Background task to extract and store memories from the conversation."""
    try:
        memory_writer = get_memory_writer()
        embedding_svc = get_embedding_service()

        # Only process last 2 messages (the user message + assistant response)
        recent = conv["history"][-2:]
        spirit_uuid = UUID(conv["spirit_id"]) if len(conv["spirit_id"]) > 10 else UUID(int=0)

        result = await memory_writer.process_conversation(
            spirit_id=spirit_uuid,
            messages=recent,
            embedding_func=embedding_svc.embed,
        )
        logger.info(f"Memory extraction for {conversation_id}: {result}")
    except Exception as e:
        logger.error(f"Background memory extraction failed: {e}")


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
) -> StreamingResponse:
    """Send a message and receive a streaming SSE response.

    Modes:
    - tool: Agent responds as a learning assistant (shows capabilities)
    - proxy: Agent responds as owner's proxy (simulates owner's level)
    """
    return StreamingResponse(
        _stream_chat(conversation_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation info and mode."""
    conv = _get_or_create_conversation(conversation_id)
    return {
        "id": conversation_id,
        "spirit_name": conv["spirit_name"],
        "mode": conv["mode"],
        "message_count": len(conv["history"]),
    }


@router.put("/conversations/{conversation_id}/mode")
async def switch_mode(conversation_id: str, mode: str):
    """Switch between tool and proxy mode."""
    conv = _get_or_create_conversation(conversation_id)
    if mode not in ("tool", "proxy"):
        return {"error": "mode must be 'tool' or 'proxy'"}
    conv["mode"] = mode
    return {"id": conversation_id, "mode": mode}
