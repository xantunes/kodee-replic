"""Qdrant vector store for document retrieval."""

import logging
import uuid
from typing import Any, Dict, List

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import settings

logger = logging.getLogger(__name__)

VECTOR_SIZE = 1536


class QdrantVectorStore:
    """Vector store backed by Qdrant."""

    def __init__(
        self,
        host: str | None = None,
        collection_name: str | None = None,
    ) -> None:
        """Initialize the Qdrant vector store.

        Args:
            host: Qdrant server URL. Defaults to settings.QDRANT_URL.
            collection_name: Name of the Qdrant collection. Defaults to settings.QDRANT_COLLECTION.
        """
        self.host = host or settings.QDRANT_URL
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self._client: QdrantClient | None = None

    @property
    def client(self) -> QdrantClient:
        """Lazy-initialize the Qdrant client."""
        if self._client is None:
            self._client = QdrantClient(url=self.host)
            self._ensure_collection()
        return self._client

    def _ensure_collection(self) -> None:
        """Ensure the Qdrant collection exists with the correct vector size."""
        try:
            collections = self.client.get_collections().collections
            collection_names = {c.name for c in collections}

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(
                    "Created Qdrant collection: %s", self.collection_name
                )
        except Exception as e:
            logger.error("Failed to ensure Qdrant collection: %s", e)
            raise

    async def add_documents(self, docs: List[Dict[str, Any]]) -> None:
        """Add documents to the vector store.

        Args:
            docs: List of documents with keys: id (optional), text, metadata (optional).
        """
        try:
            points: List[PointStruct] = []
            for doc in docs:
                doc_id = doc.get("id") or str(uuid.uuid4())
                vector = doc["vector"]
                payload = {
                    "text": doc["text"],
                    "metadata": doc.get("metadata") or {},
                }
                points.append(
                    PointStruct(id=doc_id, vector=vector, payload=payload)
                )

            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
        except Exception as e:
            logger.error("Failed to add documents to Qdrant: %s", e)
            raise

    async def search(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar documents in the vector store.

        Args:
            query_vector: The embedding vector to search for.
            top_k: Number of top results to return.

        Returns:
            List of matching documents with score, text, and metadata.
        """
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
            )

            return [
                {
                    "id": r.id,
                    "score": r.score,
                    "text": r.payload.get("text", ""),
                    "metadata": r.payload.get("metadata", {}),
                }
                for r in results
            ]
        except Exception as e:
            logger.error("Failed to search Qdrant: %s", e)
            raise
