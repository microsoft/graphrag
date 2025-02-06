# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


from unittest import mock
from unittest.mock import ANY, MagicMock, Mock

import pandas as pd
import pytest

from graphrag.config.enums import ChunkStrategyType
from graphrag.config.models.chunking_config import ChunkingConfig
from graphrag.index.operations.chunk_text.chunk_text import (
    _get_num_total,
    chunk_text,
    load_strategy,
    run_strategy,
)
from graphrag.index.operations.chunk_text.typing import (
    TextChunk,
)


def test_get_num_total_default():
    output = pd.DataFrame({"column": ["a", "b", "c"]})

    total = _get_num_total(output, "column")
    assert total == 3


def test_get_num_total_array():
    output = pd.DataFrame({"column": [["a", "b", "c"], ["x", "y"]]})

    total = _get_num_total(output, "column")
    assert total == 5


def test_load_strategy_tokens():
    strategy_type = ChunkStrategyType.tokens

    strategy_loaded = load_strategy(strategy_type)

    assert strategy_loaded.__name__ == "run_tokens"


def test_load_strategy_sentence():
    strategy_type = ChunkStrategyType.sentence

    strategy_loaded = load_strategy(strategy_type)

    assert strategy_loaded.__name__ == "run_sentences"


def test_load_strategy_none():
    strategy_type = ChunkStrategyType

    with pytest.raises(
        ValueError, match="Unknown strategy: <enum 'ChunkStrategyType'>"
    ):
        load_strategy(strategy_type)  # type: ignore


def test_run_strategy_str():
    input = "text test for run strategy"
    config = Mock()
    tick = Mock()
    strategy_mocked = Mock()

    strategy_mocked.return_value = [
        TextChunk(
            text_chunk="text test for run strategy",
            source_doc_indices=[0],
        )
    ]

    runned = run_strategy(strategy_mocked, input, config, tick)
    assert runned == ["text test for run strategy"]


def test_run_strategy_arr_str():
    input = ["text test for run strategy", "use for strategy"]
    config = Mock()
    tick = Mock()
    strategy_mocked = Mock()

    strategy_mocked.return_value = [
        TextChunk(
            text_chunk="text test for run strategy", source_doc_indices=[0], n_tokens=5
        ),
        TextChunk(text_chunk="use for strategy", source_doc_indices=[1], n_tokens=3),
    ]

    expected = [
        "text test for run strategy",
        "use for strategy",
    ]

    runned = run_strategy(strategy_mocked, input, config, tick)
    assert runned == expected


def test_run_strategy_arr_tuple():
    input = [("text test for run strategy", "3"), ("use for strategy", "5")]
    config = Mock()
    tick = Mock()
    strategy_mocked = Mock()

    strategy_mocked.return_value = [
        TextChunk(
            text_chunk="text test for run strategy", source_doc_indices=[0], n_tokens=5
        ),
        TextChunk(text_chunk="use for strategy", source_doc_indices=[1], n_tokens=3),
    ]

    expected = [
        (
            ["text test for run strategy"],
            "text test for run strategy",
            5,
        ),
        (
            ["use for strategy"],
            "use for strategy",
            3,
        ),
    ]

    runned = run_strategy(strategy_mocked, input, config, tick)
    assert runned == expected


def test_run_strategy_arr_tuple_same_doc():
    input = [("text test for run strategy", "3"), ("use for strategy", "5")]
    config = Mock()
    tick = Mock()
    strategy_mocked = Mock()

    strategy_mocked.return_value = [
        TextChunk(
            text_chunk="text test for run strategy", source_doc_indices=[0], n_tokens=5
        ),
        TextChunk(text_chunk="use for strategy", source_doc_indices=[0], n_tokens=3),
    ]

    expected = [
        (
            ["text test for run strategy"],
            "text test for run strategy",
            5,
        ),
        (
            ["text test for run strategy"],
            "use for strategy",
            3,
        ),
    ]

    runned = run_strategy(strategy_mocked, input, config, tick)
    assert runned == expected


def test_run_strategy_metadata():
    input = "All work and no play makes Jack a dull boy"
    config = Mock()
    tick = Mock()
    strategy_mocked = Mock()
    metadata = {"type": "book"}

    strategy_mocked.return_value = [
        TextChunk(
            text_chunk="All work and no play makes ", source_doc_indices=[0], n_tokens=5
        ),
        TextChunk(text_chunk="Jack a dull boy", source_doc_indices=[0], n_tokens=3),
    ]

    expected = [
        "type: book.\nAll work and no play makes ",
        "type: book.\nJack a dull boy",
    ]

    runned = run_strategy(strategy_mocked, input, config, tick, metadata)
    assert runned == expected


def test_run_strategy_two_metadata():
    input = "All work and no play makes Jack a dull boy"
    config = Mock()
    tick = Mock()
    strategy_mocked = Mock()
    metadata = {"type": "book", "author": "Stephen King"}

    strategy_mocked.return_value = [
        TextChunk(
            text_chunk="All work and no play makes ", source_doc_indices=[0], n_tokens=5
        ),
        TextChunk(text_chunk="Jack a dull boy", source_doc_indices=[0], n_tokens=3),
    ]

    expected = [
        "type: book.\nauthor: Stephen King.\nAll work and no play makes ",
        "type: book.\nauthor: Stephen King.\nJack a dull boy",
    ]

    runned = run_strategy(strategy_mocked, input, config, tick, metadata)
    assert runned == expected


def test_run_strategy_metadata_count_tokens():
    input = "All work and no play makes Jack a dull boy"
    config = ChunkingConfig()
    config.size = 20
    tick = Mock()
    strategy_mocked = MagicMock()
    metadata = {"type": "book"}

    new_config = config
    new_config.size = 16

    strategy_mocked.return_value = [
        TextChunk(
            text_chunk="All work and no play makes ",
            source_doc_indices=[0],
            n_tokens=20,
        ),
        TextChunk(text_chunk="Jack a dull boy", source_doc_indices=[0], n_tokens=3),
    ]

    run_strategy(strategy_mocked, input, config, tick, metadata, True)
    strategy_mocked.assert_called_with([input], new_config, tick)


def test_run_strategy_metadata_count_tokens_large_metadata():
    input = "All work and no play makes Jack a dull boy"
    config = ChunkingConfig()
    config.size = 5
    tick = Mock()
    strategy_mocked = MagicMock()
    metadata = {"type": "book", "author": "Stephen King"}

    strategy_mocked.return_value = [
        TextChunk(
            text_chunk="All work and no play makes ",
            source_doc_indices=[0],
            n_tokens=20,
        ),
        TextChunk(text_chunk="Jack a dull boy", source_doc_indices=[0], n_tokens=3),
    ]

    error_msg = "Metadata tokens exceed the maximum tokens per chunk. Please increase the tokens per chunk."
    with pytest.raises(ValueError, match=error_msg):
        run_strategy(strategy_mocked, input, config, tick, metadata, True)


@mock.patch("graphrag.index.operations.chunk_text.chunk_text.load_strategy")
@mock.patch("graphrag.index.operations.chunk_text.chunk_text.run_strategy")
@mock.patch("graphrag.logger.progress.ProgressTicker")
def test_chunk_text(mock_progress_ticker, mock_run_strategy, mock_load_strategy):
    input_data = pd.DataFrame({"name": ["The Shining"]})
    column = "name"
    size = 10
    overlap = 2
    encoding_model = "model"
    strategy = ChunkStrategyType.sentence
    callbacks = Mock()

    mock_load_strategy.return_value = Mock()
    mock_progress_ticker.return_value = Mock()

    chunk_text(input_data, column, size, overlap, encoding_model, strategy, callbacks)

    mock_run_strategy.assert_called_with(
        mock_load_strategy(), "The Shining", ANY, mock_progress_ticker(), None, False
    )


@mock.patch("graphrag.index.operations.chunk_text.chunk_text.load_strategy")
@mock.patch("graphrag.index.operations.chunk_text.chunk_text.run_strategy")
@mock.patch("graphrag.logger.progress.ProgressTicker")
def test_chunk_text_count_tokens_with_metadata(
    mock_progress_ticker, mock_run_strategy, mock_load_strategy
):
    input_data = pd.DataFrame({"name": ["The Shining"]})
    column = "name"
    size = 10
    overlap = 2
    encoding_model = "model"
    strategy = ChunkStrategyType.sentence
    callbacks = Mock()

    mock_load_strategy.return_value = Mock()
    mock_progress_ticker.return_value = Mock()

    chunk_text(
        input_data,
        column,
        size,
        overlap,
        encoding_model,
        strategy,
        callbacks,
        count_tokens_with_metadata=True,
    )

    mock_run_strategy.assert_called_with(
        mock_load_strategy(), "The Shining", ANY, mock_progress_ticker(), None, True
    )


@mock.patch("graphrag.index.operations.chunk_text.chunk_text.load_strategy")
@mock.patch("graphrag.index.operations.chunk_text.chunk_text.run_strategy")
@mock.patch("graphrag.logger.progress.ProgressTicker")
def test_chunk_text_prepend_metadata(
    mock_progress_ticker, mock_run_strategy, mock_load_strategy
):
    input_data = pd.DataFrame({
        "name": ["The Shining"],
        "metadata": ["{'type': 'book'}"],
    })
    column = "name"
    size = 10
    overlap = 2
    encoding_model = "model"
    strategy = ChunkStrategyType.sentence
    callbacks = Mock()

    mock_load_strategy.return_value = Mock()
    mock_progress_ticker.return_value = Mock()

    chunk_text(
        input_data,
        column,
        size,
        overlap,
        encoding_model,
        strategy,
        callbacks,
        prepend_metadata=True,
    )

    mock_run_strategy.assert_called_with(
        mock_load_strategy(),
        "The Shining",
        ANY,
        mock_progress_ticker(),
        "{'type': 'book'}",
        False,
    )
