"""Memory Writer - extracts and stores memories from conversations asynchronously."""

import asyncio
import logging
from uuid import UUID

from app.services.llm_router import LLMRouter, Scene
from app.services.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
你是一个记忆提取系统。分析以下英语学习对话，提取需要记住的信息。

请从对话中提取以下类别的信息（如果存在）：

1. **knowledge_update**: 用户在哪些知识点上表现如何（答对/答错/部分正确）
   格式：{"topic": "知识点", "performance": "correct/incorrect/partial", "detail": "具体情况"}

2. **preference**: 用户展现出的学习偏好
   格式：{"type": "偏好类型", "value": "偏好内容"}

3. **episodic**: 值得记住的对话事件
   格式：{"event": "事件描述", "importance": 0.1-1.0}

用 JSON 数组返回，每条一个对象，包含 category 和 data 字段。如果没有值得记忆的内容，返回空数组 []。

对话内容：
{conversation}
"""

PROFILE_UPDATE_PROMPT = """\
根据以下新的学习表现记录，更新学生的知识图谱掌握度。

当前知识图谱（topic: mastery 0.0-1.0）：
{current_graph}

新表现记录：
{performance_records}

规则：
- 答对一次：掌握度 +0.05（最高 1.0）
- 答错一次：掌握度 -0.08（最低 0.0）
- 部分正确：掌握度 +0.02
- 新知识点的初始掌握度为 0.3

返回更新后的完整知识图谱，JSON 格式：{"topic": mastery, ...}
仅返回 JSON，不要其他文字。
"""


class MemoryWriter:
    """Extracts memories from conversations and updates owner profile."""

    def __init__(self, llm_router: LLMRouter, memory_manager: MemoryManager):
        self._llm = llm_router
        self._memory = memory_manager

    async def process_conversation(
        self,
        spirit_id: UUID,
        messages: list[dict[str, str]],
        embedding_func,
    ) -> dict:
        """Process a completed conversation turn and extract memories.

        Args:
            spirit_id: The spirit that participated.
            messages: The conversation messages.
            embedding_func: Async function to generate embeddings.

        Returns:
            Dict with counts of extracted memories by category.
        """
        conversation_text = self._format_conversation(messages)

        try:
            response = await self._llm.route(
                scene=Scene.CASUAL_CHAT,
                system_prompt="You are a memory extraction system. Always respond with valid JSON.",
                messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(
                    conversation=conversation_text
                )}],
            )

            import json
            memories = json.loads(response.content)
            if not isinstance(memories, list):
                return {"extracted": 0}

        except Exception as e:
            logger.error(f"Memory extraction failed: {e}")
            return {"extracted": 0, "error": str(e)}

        counts = {"knowledge_update": 0, "preference": 0, "episodic": 0}

        for mem in memories:
            category = mem.get("category", "episodic")
            data = mem.get("data", {})

            if category == "knowledge_update":
                counts["knowledge_update"] += 1
                # Knowledge updates are handled by profile updater separately

            elif category == "preference":
                content = f"学习偏好：{data.get('type', '')}: {data.get('value', '')}"
                embedding = await embedding_func(content)
                await self._memory.store(
                    spirit_id=spirit_id,
                    content=content,
                    embedding=embedding,
                    importance=0.7,
                    context_tags=["preference"],
                )
                counts["preference"] += 1

            elif category == "episodic":
                content = data.get("event", "")
                importance = data.get("importance", 0.5)
                if content:
                    embedding = await embedding_func(content)
                    await self._memory.store(
                        spirit_id=spirit_id,
                        content=content,
                        embedding=embedding,
                        importance=importance,
                        context_tags=["episodic"],
                    )
                    counts["episodic"] += 1

        return {"extracted": sum(counts.values()), **counts}

    async def update_knowledge_graph(
        self,
        current_graph: dict[str, float],
        performance_records: list[dict],
    ) -> dict[str, float]:
        """Update knowledge graph based on new performance data.

        Uses simple rule-based updates (no LLM needed for this).
        """
        updated = dict(current_graph)

        for record in performance_records:
            topic = record.get("topic", "")
            performance = record.get("performance", "")

            if not topic:
                continue

            current = updated.get(topic, 0.3)

            if performance == "correct":
                updated[topic] = min(1.0, current + 0.05)
            elif performance == "incorrect":
                updated[topic] = max(0.0, current - 0.08)
            elif performance == "partial":
                updated[topic] = min(1.0, current + 0.02)
            else:
                updated.setdefault(topic, 0.3)

        return updated

    def _format_conversation(self, messages: list[dict[str, str]]) -> str:
        lines = []
        for msg in messages[-10:]:  # Last 10 messages max
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prefix = "学生" if role == "user" else "精灵"
            lines.append(f"{prefix}: {content}")
        return "\n".join(lines)
