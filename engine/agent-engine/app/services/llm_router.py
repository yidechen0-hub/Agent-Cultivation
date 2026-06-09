"""LLM Router - abstracts calling Claude/OpenAI based on scene requirements."""

from dataclasses import dataclass
from enum import StrEnum
from typing import AsyncGenerator

import anthropic
import openai


class Scene(StrEnum):
    """Defines the complexity/type of interaction to route appropriately."""

    CASUAL_CHAT = "casual_chat"  # Simple conversation -> smaller model
    DEEP_DIALOGUE = "deep_dialogue"  # Complex personality expression -> Claude
    BATTLE_RESPONSE = "battle_response"  # Battle round generation -> Claude
    BATTLE_JUDGE = "battle_judge"  # Judging battle rounds -> Claude (high reasoning)
    KNOWLEDGE_QA = "knowledge_qa"  # Factual Q&A -> OpenAI or Claude
    CREATIVE_WRITING = "creative_writing"  # Creative content -> Claude
    TOOL_CALLING = "tool_calling"  # Tool use scenarios -> Claude


@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    stop_reason: str


@dataclass
class RoutingConfig:
    provider: str  # "anthropic" | "openai"
    model: str
    max_tokens: int
    temperature: float


# Default routing table: scene -> preferred provider/model
ROUTING_TABLE: dict[Scene, RoutingConfig] = {
    Scene.CASUAL_CHAT: RoutingConfig(
        provider="anthropic", model="claude-sonnet-4-20250514", max_tokens=1024, temperature=0.8
    ),
    Scene.DEEP_DIALOGUE: RoutingConfig(
        provider="anthropic", model="claude-sonnet-4-20250514", max_tokens=2048, temperature=0.7
    ),
    Scene.BATTLE_RESPONSE: RoutingConfig(
        provider="anthropic", model="claude-sonnet-4-20250514", max_tokens=2048, temperature=0.6
    ),
    Scene.BATTLE_JUDGE: RoutingConfig(
        provider="anthropic", model="claude-sonnet-4-20250514", max_tokens=4096, temperature=0.3
    ),
    Scene.KNOWLEDGE_QA: RoutingConfig(
        provider="openai", model="gpt-4o", max_tokens=2048, temperature=0.2
    ),
    Scene.CREATIVE_WRITING: RoutingConfig(
        provider="anthropic", model="claude-sonnet-4-20250514", max_tokens=4096, temperature=0.9
    ),
    Scene.TOOL_CALLING: RoutingConfig(
        provider="anthropic", model="claude-sonnet-4-20250514", max_tokens=4096, temperature=0.4
    ),
}


class LLMRouter:
    """Routes LLM requests to the appropriate provider based on scene type.

    Supports both streaming and non-streaming calls to Anthropic Claude
    and OpenAI models with automatic fallback.
    """

    def __init__(
        self,
        anthropic_api_key: str,
        openai_api_key: str,
        routing_overrides: dict[Scene, RoutingConfig] | None = None,
    ):
        self._anthropic = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
        self._openai = openai.AsyncOpenAI(api_key=openai_api_key)
        self._routing_table = {**ROUTING_TABLE, **(routing_overrides or {})}

    def _get_config(self, scene: Scene) -> RoutingConfig:
        return self._routing_table[scene]

    async def route(
        self,
        scene: Scene,
        system_prompt: str,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        """Route a request to the appropriate LLM based on scene.

        Args:
            scene: The type of interaction determining model selection.
            system_prompt: System-level instructions for the LLM.
            messages: Conversation messages in [{"role": ..., "content": ...}] format.
            tools: Optional tool definitions for function calling.

        Returns:
            LLMResponse with content, token usage, and metadata.
        """
        config = self._get_config(scene)

        if config.provider == "anthropic":
            return await self._call_anthropic(config, system_prompt, messages, tools)
        elif config.provider == "openai":
            return await self._call_openai(config, system_prompt, messages, tools)
        else:
            raise ValueError(f"Unknown provider: {config.provider}")

    async def route_stream(
        self,
        scene: Scene,
        system_prompt: str,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a response from the appropriate LLM based on scene.

        Yields text chunks as they arrive from the model.
        """
        config = self._get_config(scene)

        if config.provider == "anthropic":
            async for chunk in self._stream_anthropic(config, system_prompt, messages, tools):
                yield chunk
        elif config.provider == "openai":
            async for chunk in self._stream_openai(config, system_prompt, messages, tools):
                yield chunk
        else:
            raise ValueError(f"Unknown provider: {config.provider}")

    async def _call_anthropic(
        self,
        config: RoutingConfig,
        system_prompt: str,
        messages: list[dict[str, str]],
        tools: list[dict] | None,
    ) -> LLMResponse:
        kwargs: dict = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "system": system_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = await self._anthropic.messages.create(**kwargs)

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return LLMResponse(
            content=content,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            stop_reason=response.stop_reason or "end_turn",
        )

    async def _call_openai(
        self,
        config: RoutingConfig,
        system_prompt: str,
        messages: list[dict[str, str]],
        tools: list[dict] | None,
    ) -> LLMResponse:
        oai_messages = [{"role": "system", "content": system_prompt}, *messages]

        kwargs: dict = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "messages": oai_messages,
        }
        if tools:
            kwargs["tools"] = [{"type": "function", "function": t} for t in tools]

        response = await self._openai.chat.completions.create(**kwargs)

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            stop_reason=choice.finish_reason or "stop",
        )

    async def _stream_anthropic(
        self,
        config: RoutingConfig,
        system_prompt: str,
        messages: list[dict[str, str]],
        tools: list[dict] | None,
    ) -> AsyncGenerator[str, None]:
        kwargs: dict = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "system": system_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        async with self._anthropic.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def _stream_openai(
        self,
        config: RoutingConfig,
        system_prompt: str,
        messages: list[dict[str, str]],
        tools: list[dict] | None,
    ) -> AsyncGenerator[str, None]:
        oai_messages = [{"role": "system", "content": system_prompt}, *messages]

        kwargs: dict = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "messages": oai_messages,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = [{"type": "function", "function": t} for t in tools]

        stream = await self._openai.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
