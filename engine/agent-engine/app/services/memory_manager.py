"""Memory Manager - handles episodic memory storage and retrieval via Qdrant."""

from dataclasses import dataclass
from uuid import UUID

import numpy as np
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)


@dataclass
class Memory:
    """Represents an episodic memory entry."""

    memory_id: str
    spirit_id: UUID
    content: str
    embedding: list[float]
    importance: float
    timestamp: str
    context_tags: list[str]
    decay_factor: float = 1.0


@dataclass
class RetrievedMemory:
    """A memory retrieved with relevance score."""

    memory: Memory
    relevance_score: float


COLLECTION_NAME = "episodic_memories"
EMBEDDING_DIM = 1536  # text-embedding-3-small dimension


class MemoryManager:
    """Manages spirit episodic memories using Qdrant for vector similarity search.

    Supports:
    - Storing new memories with embeddings and metadata
    - Retrieving relevant memories by semantic similarity
    - Time-decay weighted retrieval for recency bias
    - Importance-based filtering for memory consolidation
    """

    def __init__(self, qdrant_url: str, collection_name: str = COLLECTION_NAME):
        self._client = AsyncQdrantClient(url=qdrant_url)
        self._collection_name = collection_name

    async def ensure_collection(self) -> None:
        """Create the memories collection if it doesn't exist."""
        collections = await self._client.get_collections()
        existing_names = [c.name for c in collections.collections]

        if self._collection_name not in existing_names:
            await self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )

    async def store(
        self,
        spirit_id: UUID,
        content: str,
        embedding: list[float],
        importance: float = 0.5,
        context_tags: list[str] | None = None,
        memory_id: str | None = None,
    ) -> str:
        """Store a new episodic memory for a spirit.

        Args:
            spirit_id: The spirit this memory belongs to.
            content: The textual content of the memory.
            embedding: Pre-computed embedding vector.
            importance: Importance score (0.0 to 1.0).
            context_tags: Tags for categorical filtering.
            memory_id: Optional custom ID, auto-generated if not provided.

        Returns:
            The ID of the stored memory point.
        """
        from uuid import uuid4
        from datetime import datetime, timezone

        point_id = memory_id or str(uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "spirit_id": str(spirit_id),
                "content": content,
                "importance": importance,
                "timestamp": timestamp,
                "context_tags": context_tags or [],
                "decay_factor": 1.0,
            },
        )

        await self._client.upsert(
            collection_name=self._collection_name,
            points=[point],
        )

        return point_id

    async def retrieve(
        self,
        spirit_id: UUID,
        query_embedding: list[float],
        top_k: int = 10,
        min_importance: float = 0.0,
        context_tags: list[str] | None = None,
        apply_decay: bool = True,
    ) -> list[RetrievedMemory]:
        """Retrieve relevant memories for a spirit based on semantic similarity.

        Args:
            spirit_id: Filter memories to this spirit.
            query_embedding: The query vector to search against.
            top_k: Maximum number of memories to return.
            min_importance: Minimum importance threshold.
            context_tags: Optional filter by context tags.
            apply_decay: Whether to apply time-decay weighting.

        Returns:
            List of memories ranked by relevance score (similarity * decay * importance).
        """
        # Build filter conditions
        must_conditions = [
            FieldCondition(key="spirit_id", match=MatchValue(value=str(spirit_id))),
        ]

        if context_tags:
            for tag in context_tags:
                must_conditions.append(
                    FieldCondition(key="context_tags", match=MatchValue(value=tag))
                )

        search_filter = Filter(must=must_conditions)

        results = await self._client.search(
            collection_name=self._collection_name,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=top_k * 2,  # Fetch extra to allow post-filtering
        )

        retrieved: list[RetrievedMemory] = []
        for point in results:
            payload = point.payload or {}
            importance = payload.get("importance", 0.5)

            if importance < min_importance:
                continue

            # Calculate final relevance score
            similarity = point.score
            decay = payload.get("decay_factor", 1.0) if apply_decay else 1.0
            relevance_score = similarity * decay * (0.5 + 0.5 * importance)

            memory = Memory(
                memory_id=str(point.id),
                spirit_id=spirit_id,
                content=payload.get("content", ""),
                embedding=[],  # Don't return full embedding to save memory
                importance=importance,
                timestamp=payload.get("timestamp", ""),
                context_tags=payload.get("context_tags", []),
                decay_factor=decay,
            )

            retrieved.append(RetrievedMemory(memory=memory, relevance_score=relevance_score))

        # Sort by relevance and truncate
        retrieved.sort(key=lambda m: m.relevance_score, reverse=True)
        return retrieved[:top_k]

    async def decay_memories(self, spirit_id: UUID, decay_rate: float = 0.995) -> int:
        """Apply time decay to all memories of a spirit.

        Called periodically to reduce the influence of older memories.
        Returns the number of memories updated.
        """
        # Scroll through all memories for this spirit
        scroll_filter = Filter(
            must=[FieldCondition(key="spirit_id", match=MatchValue(value=str(spirit_id)))]
        )

        points, _ = await self._client.scroll(
            collection_name=self._collection_name,
            scroll_filter=scroll_filter,
            limit=1000,
            with_payload=True,
        )

        updated = 0
        for point in points:
            payload = point.payload or {}
            current_decay = payload.get("decay_factor", 1.0)
            new_decay = current_decay * decay_rate

            await self._client.set_payload(
                collection_name=self._collection_name,
                payload={"decay_factor": new_decay},
                points=[point.id],
            )
            updated += 1

        return updated
