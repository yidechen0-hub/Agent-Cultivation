"""Embedding service - generates vector embeddings for memory storage and retrieval."""

import openai


class EmbeddingService:
    """Generates text embeddings using OpenAI's embedding API."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self._client = openai.AsyncOpenAI(api_key=api_key)
        self._model = model

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [item.embedding for item in response.data]
