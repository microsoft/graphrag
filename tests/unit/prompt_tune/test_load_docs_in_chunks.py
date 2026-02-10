# Copyright (C) 2025 Microsoft
# Licensed under the MIT License

"""Unit tests for load_docs_in_chunks function."""

import logging
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from graphrag.prompt_tune.loader.input import load_docs_in_chunks
from graphrag.prompt_tune.types import DocSelectionType


@dataclass
class MockTextDocument:
    """Mock TextDocument for testing."""

    id: str
    text: str
    title: str
    creation_date: str
    raw_data: dict[str, Any] | None = None


class MockTokenizer:
    """Mock tokenizer for testing."""

    def encode(self, text: str) -> list[int]:
        """Encode text to tokens (simple char-based)."""
        return [ord(c) for c in text]

    def decode(self, tokens: list[int]) -> str:
        """Decode tokens to text."""
        return "".join(chr(t) for t in tokens)


@dataclass
class MockChunk:
    """Mock chunk result."""

    text: str


class MockChunker:
    """Mock chunker for testing."""

    def chunk(self, text: str, transform: Any = None) -> list[MockChunk]:
        """Split text into sentence-like chunks."""
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        return [MockChunk(text=s + ".") for s in sentences]


class MockEmbeddingModel:
    """Mock embedding model for testing."""

    def __init__(self):
        """Initialize with mock tokenizer."""
        self.tokenizer = MockTokenizer()


@pytest.fixture
def mock_config():
    """Create a mock GraphRagConfig."""
    config = MagicMock()
    config.embed_text.embedding_model_id = "test-model"
    config.embed_text.batch_size = 10
    config.embed_text.batch_max_tokens = 1000
    config.concurrent_requests = 1
    config.get_embedding_model_config.return_value = MagicMock()
    return config


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return logging.getLogger("test")


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        MockTextDocument(
            id="doc1",
            text="First sentence. Second sentence. Third sentence.",
            title="Doc 1",
            creation_date="2025-01-01",
        ),
        MockTextDocument(
            id="doc2",
            text="Another document. With content.",
            title="Doc 2",
            creation_date="2025-01-02",
        ),
    ]


class TestLoadDocsInChunks:
    """Tests for load_docs_in_chunks function."""

    @pytest.mark.asyncio
    async def test_top_selection_returns_limited_chunks(
        self, mock_config, mock_logger, sample_documents
    ):
        """Test TOP selection method returns the first N chunks."""
        mock_reader = AsyncMock()
        mock_reader.read_files.return_value = sample_documents

        with (
            patch(
                "graphrag.prompt_tune.loader.input.create_embedding",
                return_value=MockEmbeddingModel(),
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_storage",
                return_value=MagicMock(),
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_input_reader",
                return_value=mock_reader,
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_chunker",
                return_value=MockChunker(),
            ),
        ):
            result = await load_docs_in_chunks(
                config=mock_config,
                select_method=DocSelectionType.TOP,
                limit=2,
                logger=mock_logger,
            )

        assert len(result) == 2
        assert result[0] == "First sentence."
        assert result[1] == "Second sentence."

    @pytest.mark.asyncio
    async def test_random_selection_returns_correct_count(
        self, mock_config, mock_logger, sample_documents
    ):
        """Test RANDOM selection method returns the correct number of chunks."""
        mock_reader = AsyncMock()
        mock_reader.read_files.return_value = sample_documents

        with (
            patch(
                "graphrag.prompt_tune.loader.input.create_embedding",
                return_value=MockEmbeddingModel(),
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_storage",
                return_value=MagicMock(),
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_input_reader",
                return_value=mock_reader,
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_chunker",
                return_value=MockChunker(),
            ),
        ):
            result = await load_docs_in_chunks(
                config=mock_config,
                select_method=DocSelectionType.RANDOM,
                limit=3,
                logger=mock_logger,
            )

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_escapes_braces_in_output(self, mock_config, mock_logger):
        """Test that curly braces are escaped for str.format() compatibility."""
        docs_with_braces = [
            MockTextDocument(
                id="doc1",
                text="Some {latex} content.",
                title="Doc 1",
                creation_date="2025-01-01",
            ),
        ]

        mock_reader = AsyncMock()
        mock_reader.read_files.return_value = docs_with_braces

        with (
            patch(
                "graphrag.prompt_tune.loader.input.create_embedding",
                return_value=MockEmbeddingModel(),
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_storage",
                return_value=MagicMock(),
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_input_reader",
                return_value=mock_reader,
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_chunker",
                return_value=MockChunker(),
            ),
        ):
            result = await load_docs_in_chunks(
                config=mock_config,
                select_method=DocSelectionType.TOP,
                limit=1,
                logger=mock_logger,
            )

        assert len(result) == 1
        assert "{{latex}}" in result[0]

    @pytest.mark.asyncio
    async def test_limit_out_of_range_uses_default(
        self, mock_config, mock_logger, sample_documents
    ):
        """Test that invalid limit falls back to default LIMIT."""
        mock_reader = AsyncMock()
        mock_reader.read_files.return_value = sample_documents

        with (
            patch(
                "graphrag.prompt_tune.loader.input.create_embedding",
                return_value=MockEmbeddingModel(),
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_storage",
                return_value=MagicMock(),
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_input_reader",
                return_value=mock_reader,
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_chunker",
                return_value=MockChunker(),
            ),
            patch(
                "graphrag.prompt_tune.loader.input.LIMIT",
                3,
            ),
        ):
            result = await load_docs_in_chunks(
                config=mock_config,
                select_method=DocSelectionType.TOP,
                limit=-1,
                logger=mock_logger,
            )

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_chunks_all_documents(
        self, mock_config, mock_logger, sample_documents
    ):
        """Test that all documents are chunked correctly."""
        mock_reader = AsyncMock()
        mock_reader.read_files.return_value = sample_documents

        with (
            patch(
                "graphrag.prompt_tune.loader.input.create_embedding",
                return_value=MockEmbeddingModel(),
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_storage",
                return_value=MagicMock(),
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_input_reader",
                return_value=mock_reader,
            ),
            patch(
                "graphrag.prompt_tune.loader.input.create_chunker",
                return_value=MockChunker(),
            ),
        ):
            result = await load_docs_in_chunks(
                config=mock_config,
                select_method=DocSelectionType.TOP,
                limit=5,
                logger=mock_logger,
            )

        assert len(result) == 5
        assert "First sentence." in result
        assert "Another document." in result
