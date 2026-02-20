# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""Unit tests for the streaming embed_text operation."""

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from graphrag.callbacks.noop_workflow_callbacks import (
    NoopWorkflowCallbacks,
)
from graphrag.index.operations.embed_text.embed_text import embed_text
from graphrag.index.operations.embed_text.run_embed_text import (
    TextEmbeddingResult,
)
from graphrag_storage.tables.table import Table


class FakeInputTable(Table):
    """In-memory table that yields rows via async iteration."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        """Store the rows to be yielded."""
        self._rows = rows

    def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        """Return an async iterator yielding each stored row."""
        return self._iter()

    async def _iter(self) -> AsyncIterator[dict[str, Any]]:
        """Yield rows one at a time."""
        for row in self._rows:
            yield dict(row)

    async def length(self) -> int:
        """Return the number of rows."""
        return len(self._rows)

    async def has(self, row_id: str) -> bool:
        """Check if a row with the given ID exists."""
        return any(r.get("id") == row_id for r in self._rows)

    async def write(self, row: dict[str, Any]) -> None:
        """No-op write (input table is read-only)."""

    async def close(self) -> None:
        """No-op close."""


class FakeOutputTable(Table):
    """Collects rows written via write() for assertion."""

    def __init__(self) -> None:
        """Initialize empty row collection."""
        self.rows: list[dict[str, Any]] = []

    def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        """Yield collected rows."""
        return self._iter()

    async def _iter(self) -> AsyncIterator[dict[str, Any]]:
        """Yield rows one at a time."""
        for row in self.rows:
            yield row

    async def length(self) -> int:
        """Return the number of written rows."""
        return len(self.rows)

    async def has(self, row_id: str) -> bool:
        """Check if a row with the given ID was written."""
        return any(r.get("id") == row_id for r in self.rows)

    async def write(self, row: dict[str, Any]) -> None:
        """Append a row to the collection."""
        self.rows.append(row)

    async def close(self) -> None:
        """No-op close."""


def _make_mock_vector_store():
    """Create a mock vector store with create_index and load_documents."""
    store = MagicMock()
    store.create_index = MagicMock()
    store.load_documents = MagicMock()
    return store


def _make_mock_model(embedding_values: list[float]):
    """Create a mock model that returns fixed embeddings."""
    model = MagicMock()
    model.tokenizer = MagicMock()
    return model, embedding_values


def _make_embedding_result(count: int, values: list[float]) -> TextEmbeddingResult:
    """Build a TextEmbeddingResult with count copies of values."""
    return TextEmbeddingResult(embeddings=[list(values) for _ in range(count)])


@pytest.mark.asyncio
async def test_embed_text_basic():
    """Verify basic embedding: rows flow through to vector store and output table."""
    rows = [
        {"id": "a", "text": "hello world"},
        {"id": "b", "text": "foo bar"},
        {"id": "c", "text": "baz qux"},
    ]
    input_table = FakeInputTable(rows)
    output_table = FakeOutputTable()
    vector_store = _make_mock_vector_store()
    embedding_values = [1.0, 2.0, 3.0]

    with patch(
        "graphrag.index.operations.embed_text.embed_text.run_embed_text",
        new_callable=AsyncMock,
    ) as mock_run:
        mock_run.return_value = _make_embedding_result(3, embedding_values)

        count = await embed_text(
            input_table=input_table,
            callbacks=NoopWorkflowCallbacks(),
            model=MagicMock(),
            tokenizer=MagicMock(),
            embed_column="text",
            batch_size=10,
            batch_max_tokens=8191,
            num_threads=1,
            vector_store=vector_store,
            output_table=output_table,
        )

    assert count == 3
    assert len(output_table.rows) == 3
    assert output_table.rows[0]["id"] == "a"
    assert output_table.rows[0]["embedding"] == embedding_values
    assert output_table.rows[2]["id"] == "c"

    vector_store.create_index.assert_called_once()
    vector_store.load_documents.assert_called_once()
    docs = vector_store.load_documents.call_args[0][0]
    assert len(docs) == 3
    assert docs[0].id == "a"
    assert docs[1].id == "b"


@pytest.mark.asyncio
async def test_embed_text_batching():
    """Verify rows are flushed in batches when batch_size < total rows."""
    rows = [{"id": str(i), "text": f"text {i}"} for i in range(5)]
    input_table = FakeInputTable(rows)
    vector_store = _make_mock_vector_store()

    with patch(
        "graphrag.index.operations.embed_text.embed_text.run_embed_text",
        new_callable=AsyncMock,
    ) as mock_run:
        mock_run.side_effect = [
            _make_embedding_result(2, [1.0]),
            _make_embedding_result(2, [2.0]),
            _make_embedding_result(1, [3.0]),
        ]

        count = await embed_text(
            input_table=input_table,
            callbacks=NoopWorkflowCallbacks(),
            model=MagicMock(),
            tokenizer=MagicMock(),
            embed_column="text",
            batch_size=2,
            batch_max_tokens=8191,
            num_threads=1,
            vector_store=vector_store,
        )

    assert count == 5
    assert mock_run.call_count == 3
    assert vector_store.load_documents.call_count == 3


@pytest.mark.asyncio
async def test_embed_text_pretransformed_rows():
    """Verify rows pre-transformed by table layer are embedded correctly."""
    rows = [
        {
            "id": "1",
            "title": "Alpha",
            "description": "First",
            "combined": "Alpha:First",
        },
        {
            "id": "2",
            "title": "Beta",
            "description": "Second",
            "combined": "Beta:Second",
        },
    ]
    input_table = FakeInputTable(rows)
    output_table = FakeOutputTable()
    vector_store = _make_mock_vector_store()

    with patch(
        "graphrag.index.operations.embed_text.embed_text.run_embed_text",
        new_callable=AsyncMock,
    ) as mock_run:
        mock_run.return_value = _make_embedding_result(2, [0.5])

        count = await embed_text(
            input_table=input_table,
            callbacks=NoopWorkflowCallbacks(),
            model=MagicMock(),
            tokenizer=MagicMock(),
            embed_column="combined",
            batch_size=10,
            batch_max_tokens=8191,
            num_threads=1,
            vector_store=vector_store,
            output_table=output_table,
        )

    assert count == 2
    texts_arg = mock_run.call_args[0][0]
    assert texts_arg == ["Alpha:First", "Beta:Second"]


@pytest.mark.asyncio
async def test_embed_text_none_values_filled():
    """Verify None embed_column values are replaced with empty string."""
    rows = [
        {"id": "1", "text": None},
        {"id": "2", "text": "real text"},
    ]
    input_table = FakeInputTable(rows)
    vector_store = _make_mock_vector_store()

    with patch(
        "graphrag.index.operations.embed_text.embed_text.run_embed_text",
        new_callable=AsyncMock,
    ) as mock_run:
        mock_run.return_value = _make_embedding_result(2, [1.0])

        count = await embed_text(
            input_table=input_table,
            callbacks=NoopWorkflowCallbacks(),
            model=MagicMock(),
            tokenizer=MagicMock(),
            embed_column="text",
            batch_size=10,
            batch_max_tokens=8191,
            num_threads=1,
            vector_store=vector_store,
        )

    assert count == 2
    texts_arg = mock_run.call_args[0][0]
    assert texts_arg == ["", "real text"]


@pytest.mark.asyncio
async def test_embed_text_no_output_table():
    """Verify embedding works without an output table (no snapshot)."""
    rows = [{"id": "x", "text": "data"}]
    input_table = FakeInputTable(rows)
    vector_store = _make_mock_vector_store()

    with patch(
        "graphrag.index.operations.embed_text.embed_text.run_embed_text",
        new_callable=AsyncMock,
    ) as mock_run:
        mock_run.return_value = _make_embedding_result(1, [9.0])

        count = await embed_text(
            input_table=input_table,
            callbacks=NoopWorkflowCallbacks(),
            model=MagicMock(),
            tokenizer=MagicMock(),
            embed_column="text",
            batch_size=10,
            batch_max_tokens=8191,
            num_threads=1,
            vector_store=vector_store,
            output_table=None,
        )

    assert count == 1
    vector_store.load_documents.assert_called_once()


@pytest.mark.asyncio
async def test_embed_text_empty_input():
    """Verify zero rows returns zero count with no calls."""
    input_table = FakeInputTable([])
    vector_store = _make_mock_vector_store()

    with patch(
        "graphrag.index.operations.embed_text.embed_text.run_embed_text",
        new_callable=AsyncMock,
    ) as mock_run:
        count = await embed_text(
            input_table=input_table,
            callbacks=NoopWorkflowCallbacks(),
            model=MagicMock(),
            tokenizer=MagicMock(),
            embed_column="text",
            batch_size=10,
            batch_max_tokens=8191,
            num_threads=1,
            vector_store=vector_store,
        )

    assert count == 0
    mock_run.assert_not_called()
    vector_store.load_documents.assert_not_called()


@pytest.mark.asyncio
async def test_embed_text_numpy_array_vectors():
    """Verify np.ndarray embeddings are converted to plain lists."""
    rows = [
        {"id": "a", "text": "hello"},
        {"id": "b", "text": "world"},
    ]
    input_table = FakeInputTable(rows)
    output_table = FakeOutputTable()
    vector_store = _make_mock_vector_store()

    numpy_embeddings: list[list[float] | None] = [
        np.array([1.0, 2.0]).tolist(),
        np.array([3.0, 4.0]).tolist(),
    ]

    with patch(
        "graphrag.index.operations.embed_text.embed_text.run_embed_text",
        new_callable=AsyncMock,
    ) as mock_run:
        # Simulate run_embed_text returning np.ndarray objects at runtime
        # by replacing the result embeddings after construction.
        result = TextEmbeddingResult(embeddings=numpy_embeddings)
        result.embeddings = [np.array([1.0, 2.0]), np.array([3.0, 4.0])]  # type: ignore[list-item]
        mock_run.return_value = result

        count = await embed_text(
            input_table=input_table,
            callbacks=NoopWorkflowCallbacks(),
            model=MagicMock(),
            tokenizer=MagicMock(),
            embed_column="text",
            batch_size=10,
            batch_max_tokens=8191,
            num_threads=1,
            vector_store=vector_store,
            output_table=output_table,
        )

    assert count == 2

    docs = vector_store.load_documents.call_args[0][0]
    assert docs[0].vector == [1.0, 2.0]
    assert docs[1].vector == [3.0, 4.0]
    assert type(docs[0].vector) is list
    assert type(docs[1].vector) is list

    assert output_table.rows[0]["embedding"] == [1.0, 2.0]
    assert type(output_table.rows[0]["embedding"]) is list


@pytest.mark.asyncio
async def test_embed_text_partial_none_embeddings():
    """Verify rows with None embeddings are skipped in store and output."""
    rows = [
        {"id": "a", "text": "good"},
        {"id": "b", "text": "failed"},
        {"id": "c", "text": "also good"},
    ]
    input_table = FakeInputTable(rows)
    output_table = FakeOutputTable()
    vector_store = _make_mock_vector_store()

    mixed_embeddings = [[1.0, 2.0], None, [3.0, 4.0]]

    with patch(
        "graphrag.index.operations.embed_text.embed_text.run_embed_text",
        new_callable=AsyncMock,
    ) as mock_run:
        mock_run.return_value = TextEmbeddingResult(embeddings=mixed_embeddings)

        count = await embed_text(
            input_table=input_table,
            callbacks=NoopWorkflowCallbacks(),
            model=MagicMock(),
            tokenizer=MagicMock(),
            embed_column="text",
            batch_size=10,
            batch_max_tokens=8191,
            num_threads=1,
            vector_store=vector_store,
            output_table=output_table,
        )

    assert count == 3

    docs = vector_store.load_documents.call_args[0][0]
    assert len(docs) == 2
    assert docs[0].id == "a"
    assert docs[1].id == "c"

    assert len(output_table.rows) == 2
    assert output_table.rows[0]["id"] == "a"
    assert output_table.rows[1]["id"] == "c"
