"""Document ingestion service for the RAG pipeline."""

import logging
import uuid
from pathlib import Path
from typing import Dict, List

from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


class DocumentIngestor:
    """Ingest documents into the RAG vector store."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: QdrantVectorStore | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        """Initialize the document ingestor.

        Args:
            embedding_service: Service for generating embeddings.
            vector_store: Vector store for storing documents.
            chunk_size: Maximum size of each text chunk.
            chunk_overlap: Overlap between consecutive chunks.
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or QdrantVectorStore()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks.

        First attempts to split by paragraphs. If a paragraph exceeds
        chunk_size, falls back to fixed-size sliding windows.

        Args:
            text: The text to chunk.

        Returns:
            List of text chunks.
        """
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[str] = []

        for paragraph in paragraphs:
            if len(paragraph) <= self.chunk_size:
                chunks.append(paragraph)
            else:
                # Fixed-size sliding window for long paragraphs
                start = 0
                while start < len(paragraph):
                    end = start + self.chunk_size
                    chunks.append(paragraph[start:end])
                    start += self.chunk_size - self.chunk_overlap

        return chunks

    async def ingest_text(
        self, text: str, metadata: Dict[str, str] | None = None
    ) -> str:
        """Chunk text, embed it, and store in Qdrant.

        Args:
            text: The text to ingest.
            metadata: Optional metadata to attach to the document.

        Returns:
            The document ID.
        """
        doc_id = str(uuid.uuid4())
        chunks = self.chunk_text(text)

        if not chunks:
            logger.warning("No chunks generated for text.")
            return doc_id

        embeddings = await self.embedding_service.embed_texts(chunks)

        docs = [
            {
                "id": f"{doc_id}_{i}",
                "text": chunk,
                "vector": embedding,
                "metadata": {**(metadata or {}), "chunk_index": i, "doc_id": doc_id},
            }
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]

        await self.vector_store.add_documents(docs)
        logger.info("Ingested document %s with %d chunks", doc_id, len(docs))
        return doc_id

    async def ingest_file(
        self, file_path: str, metadata: Dict[str, str] | None = None
    ) -> str:
        """Read a file and ingest its contents.

        Args:
            file_path: Path to the file to ingest.
            metadata: Optional metadata to attach to the document.

        Returns:
            The document ID.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        text = path.read_text(encoding="utf-8")
        file_metadata = {
            "source": file_path,
            "filename": path.name,
            **(metadata or {}),
        }
        return await self.ingest_text(text, metadata=file_metadata)
