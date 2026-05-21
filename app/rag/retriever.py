"""RAG retriever for augmenting prompts with retrieved context."""

import logging
from typing import Any, Dict, List

from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retriever that fetches relevant documents to augment LLM prompts."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: QdrantVectorStore | None = None,
    ) -> None:
        """Initialize the RAG retriever.

        Args:
            embedding_service: Service for generating query embeddings.
            vector_store: Vector store for searching documents.
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or QdrantVectorStore()

    async def retrieve(
        self, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query.

        Args:
            query: The user query.
            top_k: Number of documents to retrieve.

        Returns:
            List of retrieved documents with score, text, and metadata.
        """
        try:
            query_vector = await self.embedding_service.embed_text(query)
            results = await self.vector_store.search(query_vector, top_k=top_k)
            return results
        except Exception as e:
            logger.error("Failed to retrieve documents: %s", e)
            return []

    async def augment_prompt(
        self, query: str, context: List[Dict[str, Any]]
    ) -> str:
        """Format retrieved context into an augmented prompt.

        Args:
            query: The original user query.
            context: List of retrieved documents.

        Returns:
            Augmented prompt string with context and question.
        """
        if not context:
            return query

        context_lines = "\n".join(
            f"{i + 1}. {doc['text']}" for i, doc in enumerate(context)
        )

        return (
            f"Context:\n{context_lines}\n\n"
            f"Question: {query}\nAnswer:"
        )
