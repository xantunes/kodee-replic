"""Embedding service using OpenAI or Azure OpenAI via LangChain."""

import logging
from typing import Any, List

from app.config import settings

logger = logging.getLogger(__name__)


def _create_embeddings(model: str) -> Any:
    """Create the appropriate embeddings client based on configuration.

    Args:
        model: Embedding model name.

    Returns:
        OpenAIEmbeddings or AzureOpenAIEmbeddings instance.
    """
    if settings.AZURE_OPENAI_ENDPOINT:
        from langchain_openai import AzureOpenAIEmbeddings

        deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT or model
        return AzureOpenAIEmbeddings(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_deployment=deployment,
        )

    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=model,
        api_key=settings.OPENAI_API_KEY,
    )


class EmbeddingService:
    """Service for generating text embeddings using OpenAI or Azure OpenAI."""

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        """Initialize the embedding client.

        Args:
            model: OpenAI embedding model to use.
        """
        self.model = model
        self._embeddings = _create_embeddings(model)

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
