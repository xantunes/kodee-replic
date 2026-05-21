"""Tests for the RAG pipeline components."""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.embeddings import EmbeddingService
from app.rag.ingest import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, DocumentIngestor
from app.rag.retriever import RAGRetriever
from app.rag.vector_store import QdrantVectorStore


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    @pytest.mark.asyncio
    async def test_embed_text_returns_list_of_floats(self) -> None:
        """Test that embed_text returns a list of floats."""
        mock_embeddings = MagicMock()
        mock_embeddings.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])

        with patch(
            "app.rag.embeddings._create_embeddings", return_value=mock_embeddings
        ):
            service = EmbeddingService()
            result = await service.embed_text("hello world")

        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)
        assert result == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_embed_texts_returns_list_of_list_of_floats(self) -> None:
        """Test that embed_texts returns a list of embedding vectors."""
        mock_embeddings = MagicMock()
        mock_embeddings.aembed_documents = AsyncMock(
            return_value=[[0.1, 0.2], [0.3, 0.4]]
        )

        with patch(
            "app.rag.embeddings._create_embeddings", return_value=mock_embeddings
        ):
            service = EmbeddingService()
            result = await service.embed_texts(["text1", "text2"])

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(vec, list) for vec in result)
        assert all(isinstance(x, float) for vec in result for x in vec)

    @pytest.mark.asyncio
    async def test_embed_text_raises_on_error(self) -> None:
        """Test that embed_text raises on API error."""
        mock_embeddings = MagicMock()
        mock_embeddings.aembed_query = AsyncMock(side_effect=RuntimeError("API down"))

        with patch(
            "app.rag.embeddings._create_embeddings", return_value=mock_embeddings
        ):
            service = EmbeddingService()
            with pytest.raises(RuntimeError, match="API down"):
                await service.embed_text("hello")


class TestQdrantVectorStore:
    """Tests for QdrantVectorStore."""

    def test_init_creates_collection_if_not_exists(self) -> None:
        """Test that init creates the collection if it does not exist."""
        mock_client = MagicMock()
        mock_client.get_collections.return_value.collections = []

        with patch(
            "app.rag.vector_store.QdrantClient", return_value=mock_client
        ), patch("app.rag.vector_store.settings") as mock_settings:
            mock_settings.QDRANT_URL = "http://localhost:6333"
            mock_settings.QDRANT_COLLECTION = "test_collection"
            store = QdrantVectorStore()
            # Trigger lazy initialization
            _ = store.client

        mock_client.create_collection.assert_called_once()
        call_kwargs = mock_client.create_collection.call_args.kwargs
        assert call_kwargs["collection_name"] == "test_collection"

    def test_init_skips_create_if_collection_exists(self) -> None:
        """Test that init skips creation if collection already exists."""
        mock_collection = MagicMock()
        mock_collection.name = "test_collection"
        mock_client = MagicMock()
        mock_client.get_collections.return_value.collections = [mock_collection]

        with patch(
            "app.rag.vector_store.QdrantClient", return_value=mock_client
        ), patch("app.rag.vector_store.settings") as mock_settings:
            mock_settings.QDRANT_URL = "http://localhost:6333"
            mock_settings.QDRANT_COLLECTION = "test_collection"
            store = QdrantVectorStore()
            # Trigger lazy initialization
            _ = store.client

        mock_client.create_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_documents(self) -> None:
        """Test that add_documents upserts points into Qdrant."""
        mock_client = MagicMock()
        mock_client.get_collections.return_value.collections = []

        with patch(
            "app.rag.vector_store.QdrantClient", return_value=mock_client
        ), patch("app.rag.vector_store.settings") as mock_settings:
            mock_settings.QDRANT_URL = "http://localhost:6333"
            mock_settings.QDRANT_COLLECTION = "test_collection"
            store = QdrantVectorStore()
            # Trigger lazy initialization
            _ = store.client

        docs: List[Dict[str, Any]] = [
            {
                "id": "doc-1",
                "text": "hello world",
                "vector": [0.1, 0.2, 0.3],
                "metadata": {"source": "test"},
            }
        ]
        await store.add_documents(docs)

        mock_client.upsert.assert_called_once()
        call_kwargs = mock_client.upsert.call_args.kwargs
        assert call_kwargs["collection_name"] == "test_collection"
        assert len(call_kwargs["points"]) == 1
        assert call_kwargs["points"][0].id == "doc-1"

    @pytest.mark.asyncio
    async def test_search_returns_results(self) -> None:
        """Test that search returns formatted results."""
        mock_result = MagicMock()
        mock_result.id = "doc-1"
        mock_result.score = 0.95
        mock_result.payload = {"text": "hello world", "metadata": {"source": "test"}}

        mock_client = MagicMock()
        mock_client.get_collections.return_value.collections = []
        mock_client.search.return_value = [mock_result]

        with patch(
            "app.rag.vector_store.QdrantClient", return_value=mock_client
        ), patch("app.rag.vector_store.settings") as mock_settings:
            mock_settings.QDRANT_URL = "http://localhost:6333"
            mock_settings.QDRANT_COLLECTION = "test_collection"
            store = QdrantVectorStore()
            # Trigger lazy initialization
            _ = store.client

        results = await store.search([0.1, 0.2, 0.3], top_k=3)

        mock_client.search.assert_called_once()
        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["limit"] == 3

        assert len(results) == 1
        assert results[0]["id"] == "doc-1"
        assert results[0]["score"] == 0.95
        assert results[0]["text"] == "hello world"
        assert results[0]["metadata"] == {"source": "test"}


class TestDocumentIngestor:
    """Tests for DocumentIngestor."""

    def test_chunk_text_with_short_paragraphs(self) -> None:
        """Test chunking with paragraphs shorter than chunk size."""
        with patch("app.rag.vector_store.QdrantClient"):
            ingestor = DocumentIngestor()
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = ingestor.chunk_text(text)

        assert len(chunks) == 3
        assert chunks[0] == "Paragraph one."
        assert chunks[1] == "Paragraph two."
        assert chunks[2] == "Paragraph three."

    def test_chunk_text_with_long_paragraph(self) -> None:
        """Test chunking falls back to fixed-size for long paragraphs."""
        with patch("app.rag.vector_store.QdrantClient"):
            ingestor = DocumentIngestor(chunk_size=20, chunk_overlap=5)
        text = "A" * 50
        chunks = ingestor.chunk_text(text)

        assert len(chunks) > 1
        # Each chunk should be at most chunk_size
        assert all(len(c) <= 20 for c in chunks)
        # Overlap should exist between consecutive chunks
        if len(chunks) > 1:
            assert chunks[0][15:20] == chunks[1][0:5]

    def test_chunk_text_empty_string(self) -> None:
        """Test chunking empty string returns empty list."""
        with patch("app.rag.vector_store.QdrantClient"):
            ingestor = DocumentIngestor()
        chunks = ingestor.chunk_text("")
        assert chunks == []

    @pytest.mark.asyncio
    async def test_ingest_text(self) -> None:
        """Test ingest_text chunks, embeds, and stores documents."""
        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_texts = AsyncMock(
            return_value=[[0.1, 0.2], [0.3, 0.4]]
        )

        mock_vector_store = MagicMock()
        mock_vector_store.add_documents = AsyncMock()

        ingestor = DocumentIngestor(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
        )

        doc_id = await ingestor.ingest_text(
            "First paragraph.\n\nSecond paragraph.", metadata={"source": "test"}
        )

        assert isinstance(doc_id, str)
        assert len(doc_id) > 0
        mock_embedding_service.embed_texts.assert_called_once()
        mock_vector_store.add_documents.assert_called_once()

        call_args = mock_vector_store.add_documents.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0]["text"] == "First paragraph."
        assert call_args[1]["text"] == "Second paragraph."
        assert call_args[0]["metadata"]["source"] == "test"

    @pytest.mark.asyncio
    async def test_ingest_file(self, tmp_path: Any) -> None:
        """Test ingest_file reads and ingests file contents."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("File content here.", encoding="utf-8")

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_texts = AsyncMock(return_value=[[0.1, 0.2]])

        mock_vector_store = MagicMock()
        mock_vector_store.add_documents = AsyncMock()

        ingestor = DocumentIngestor(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
        )

        doc_id = await ingestor.ingest_file(str(file_path))

        assert isinstance(doc_id, str)
        mock_embedding_service.embed_texts.assert_called_once()
        mock_vector_store.add_documents.assert_called_once()

        call_args = mock_vector_store.add_documents.call_args[0][0]
        assert call_args[0]["text"] == "File content here."
        assert call_args[0]["metadata"]["filename"] == "test.txt"

    @pytest.mark.asyncio
    async def test_ingest_file_not_found(self) -> None:
        """Test ingest_file raises FileNotFoundError for missing files."""
        with patch("app.rag.vector_store.QdrantClient"):
            ingestor = DocumentIngestor()
        with pytest.raises(FileNotFoundError):
            await ingestor.ingest_file("/nonexistent/path/file.txt")


class TestRAGRetriever:
    """Tests for RAGRetriever."""

    @pytest.mark.asyncio
    async def test_retrieve_returns_results(self) -> None:
        """Test retrieve embeds query and returns search results."""
        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_text = AsyncMock(return_value=[0.1, 0.2])

        mock_vector_store = MagicMock()
        mock_vector_store.search = AsyncMock(
            return_value=[
                {"id": "doc-1", "score": 0.95, "text": "result 1", "metadata": {}}
            ]
        )

        retriever = RAGRetriever(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
        )

        results = await retriever.retrieve("test query", top_k=3)

        mock_embedding_service.embed_text.assert_called_once_with("test query")
        mock_vector_store.search.assert_called_once_with([0.1, 0.2], top_k=3)

        assert len(results) == 1
        assert results[0]["text"] == "result 1"

    @pytest.mark.asyncio
    async def test_retrieve_returns_empty_on_error(self) -> None:
        """Test retrieve returns empty list on embedding error."""
        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_text = AsyncMock(
            side_effect=RuntimeError("embedding failed")
        )

        mock_vector_store = MagicMock()

        retriever = RAGRetriever(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
        )

        results = await retriever.retrieve("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_augment_prompt_with_context(self) -> None:
        """Test augment_prompt formats context correctly."""
        with patch("app.rag.vector_store.QdrantClient"):
            retriever = RAGRetriever()
        context = [
            {"id": "doc-1", "score": 0.9, "text": "Context one", "metadata": {}},
            {"id": "doc-2", "score": 0.8, "text": "Context two", "metadata": {}},
        ]

        prompt = await retriever.augment_prompt("What is AI?", context)

        assert prompt.startswith("Context:")
        assert "1. Context one" in prompt
        assert "2. Context two" in prompt
        assert "Question: What is AI?" in prompt
        assert "Answer:" in prompt

    @pytest.mark.asyncio
    async def test_augment_prompt_without_context(self) -> None:
        """Test augment_prompt returns original query when context is empty."""
        with patch("app.rag.vector_store.QdrantClient"):
            retriever = RAGRetriever()
        prompt = await retriever.augment_prompt("What is AI?", [])

        assert prompt == "What is AI?"
