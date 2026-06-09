"""Chat router - handles conversation message streaming."""

from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


class SendMessageRequest(BaseModel):
    content: str
    spirit_id: UUID
    context_window: int = 20


class MessageChunk(BaseModel):
    type: str  # "text_delta" | "tool_use" | "done"
    content: str = ""
    metadata: dict | None = None


async def _stream_response(conversation_id: UUID, request: SendMessageRequest):
    """Generate SSE stream for a conversation message response.

    Coordinates between LLMRouter, MemoryManager, and PromptBuilder to produce
    a streaming agent response with tool use capabilities.
    """
    # 1. Retrieve conversation history and relevant memories
    # 2. Build prompt with context
    # 3. Stream LLM response with tool calls

    yield f"event: text_delta\ndata: {{\"content\": \"Thinking...\"}}\n\n"

    # TODO: Replace with actual LLM streaming
    # - Load spirit personality profile
    # - Retrieve episodic memories via MemoryManager
    # - Build system prompt via PromptBuilder
    # - Route to appropriate LLM via LLMRouter
    # - Stream response chunks

    yield f"event: text_delta\ndata: {{\"content\": \"This is a placeholder response from spirit.\"}}\n\n"
    yield f"event: done\ndata: {{\"message_id\": \"placeholder\"}}\n\n"


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
) -> StreamingResponse:
    """Send a message in a conversation and receive a streaming SSE response.

    The agent engine will:
    1. Load the spirit's personality and memory context
    2. Build the prompt with episodic memories and tool definitions
    3. Route to the appropriate LLM based on scene complexity
    4. Stream the response as Server-Sent Events
    """
    return StreamingResponse(
        _stream_response(conversation_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
