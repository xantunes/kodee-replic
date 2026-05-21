"""Embedding service using OpenAI via LangChain."""

import logging
from typing import List

from langchain_openai import OpenAIEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        """Initialize the embedding client.

        Args:
            model: OpenAI embedding model to use.
        """
        self.model = model
        self._embeddings = OpenAIEmbeddings(
            model=model,
            api_key=settings.OPENAI_API_KEY,
        )

    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text string.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        try:
            result: List[float] = await self._embeddings.aembed_query(text)
            return result
        except Exception as e:
            logger.error("Failed to embed text: %s", e)
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple text strings.

        Args:
            texts: List of texts to embed.

        Returns:
            A list of embedding vectors.
        """
        try:
            results: List[List[float]] = await self._embeddings.aembed_documents(texts)
            return results
        except Exception as e:
            logger.error("Failed to embed texts: %s", e)
            raise
