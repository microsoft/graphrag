# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from unittest import mock
from unittest.mock import MagicMock

import pytest

from graphrag.index.operations.chunk_text.typing import TextChunk
from graphrag.index.text_splitting.text_splitting import (
    NoopTextSplitter,
    Tokenizer,
    TokenTextSplitter,
    split_multiple_texts_on_tokens,
    split_single_text_on_tokens,
    split_text_on_tokens,
)


def test_noop_text_splitter() -> None:
    splitter = NoopTextSplitter()

    assert list(splitter.split_text("some text")) == ["some text"]
    assert list(splitter.split_text(["some", "text"])) == ["some", "text"]


class MockTokenizer:
    def encode(self, text):
        return [ord(char) for char in text]

    def decode(self, token_ids):
        return "".join(chr(id) for id in token_ids)


def test_split_text_str_empty():
    splitter = TokenTextSplitter(chunk_size=5, chunk_overlap=2)
    result = splitter.split_text("")

    assert result == []


def test_split_text_str_bool():
    splitter = TokenTextSplitter(chunk_size=5, chunk_overlap=2)
    result = splitter.split_text(None)  # type: ignore

    assert result == []


def test_split_text_str_int():
    splitter = TokenTextSplitter(chunk_size=5, chunk_overlap=2)
    with pytest.raises(TypeError):
        splitter.split_text(123)  # type: ignore


@mock.patch("graphrag.index.text_splitting.text_splitting.split_single_text_on_tokens")
def test_split_text_large_input(mock_split):
    large_text = "a" * 10_000
    mock_split.return_value = ["chunk"] * 2_000
    splitter = TokenTextSplitter(chunk_size=5, chunk_overlap=2)

    result = splitter.split_text(large_text)

    assert len(result) == 2_000, "Large input was not split correctly"
    mock_split.assert_called_once()


@mock.patch("graphrag.index.text_splitting.text_splitting.split_single_text_on_tokens")
@mock.patch("graphrag.index.text_splitting.text_splitting.Tokenizer")
@mock.patch("tiktoken.get_encoding")
def test_token_text_splitter(mock_get_encoding, mock_tokenizer, mock_split_text):
    text = "chunk1 chunk2 chunk3"
    expected_chunks = ["chunk1", "chunk2", "chunk3"]

    mocked_tokenizer = MagicMock()
    mock_tokenizer.return_value = mocked_tokenizer
    mock_split_text.return_value = expected_chunks

    mock_get_encoding.return_value = MagicMock(tokens_per_chunk=5, chunk_overlap=2)

    splitter = TokenTextSplitter(
        encoding_name="mock_encoding",
    )

    splitter.split_text(["chunk1", "chunk2", "chunk3"])

    mock_split_text.assert_called_once_with(text=text, tokenizer=mocked_tokenizer)


@mock.patch("tiktoken.get_encoding")
def test_encode_basic(mock_get_encoding):
    mock_encoder = MagicMock()
    mock_encoder.encode.return_value = [1, 2, 3]
    mock_get_encoding.return_value = mock_encoder

    splitter = TokenTextSplitter(encoding_name="mock_encoding")
    result = splitter.encode("abc def")

    assert result == [1, 2, 3], "Encoding failed to return expected tokens"
    mock_encoder.encode.assert_called_once_with(
        "abc def", allowed_special=set(), disallowed_special="all"
    )


@mock.patch("tiktoken.get_encoding")
def test_num_tokens_empty_input(mock_get_encoding):
    mock_encoder = MagicMock()
    mock_encoder.encode.return_value = []
    mock_get_encoding.return_value = mock_encoder

    splitter = TokenTextSplitter(encoding_name="mock_encoding")
    result = splitter.num_tokens("")

    assert result == 0, "Token count for empty input should be 0"


@mock.patch("tiktoken.encoding_for_model")
def test_model_name(mock_get_encoding):
    mock_encoder = MagicMock()
    mock_encoder.encode.return_value = [1, 2, 3]
    mock_get_encoding.return_value = mock_encoder

    splitter = TokenTextSplitter(model_name="mock_model")
    result = splitter.encode("abc def")

    assert result == [1, 2, 3], "Encoding failed to return expected tokens"
    mock_encoder.encode.assert_called_once_with(
        "abc def", allowed_special=set(), disallowed_special="all"
    )


@mock.patch("tiktoken.encoding_for_model", side_effect=KeyError)
@mock.patch("tiktoken.get_encoding")
def test_model_name_exception(mock_get_encoding, mock_encoding_for_model):
    mock_get_encoding.return_value = mock.MagicMock()

    TokenTextSplitter(model_name="mock_model", encoding_name="mock_encoding")

    mock_get_encoding.assert_called_once_with("mock_encoding")
    mock_encoding_for_model.assert_called_once_with("mock_model")


@mock.patch(
    "graphrag.index.text_splitting.text_splitting.split_multiple_texts_on_tokens"
)
def test_split_multiple_text_on_tokens_tick(mock_split):
    text = ["This is a test text, meaning to be taken seriously by this test only."]
    mock_split.return_value = ["chunk"] * 2
    tokenizer = MagicMock()
    progress_ticket = MagicMock()
    result = split_text_on_tokens(text, tokenizer, progress_ticket)
    assert len(result) == 2, "Large input was not split correctly"

    mock_split.assert_called_once_with(text, tokenizer, progress_ticket)


@mock.patch(
    "graphrag.index.text_splitting.text_splitting.split_multiple_texts_on_tokens"
)
def test_split_multiple_text_on_tokens_no_tick(mock_split):
    text = ["This is a test text, meaning to be taken seriously by this test only."]
    mock_split.return_value = ["chunk"] * 2
    tokenizer = MagicMock()
    result = split_text_on_tokens(text, tokenizer)
    assert len(result) == 2, "Large input was not split correctly"
    mock_split.assert_called_once_with(text, tokenizer, None)


@mock.patch("graphrag.index.text_splitting.text_splitting.split_single_text_on_tokens")
def test_split_single_text_on_tokens_no_tick(mock_split):
    text = "This is a test text, meaning to be taken seriously by this test only."
    mock_split.return_value = ["chunk"] * 2
    tokenizer = MagicMock()
    result = split_text_on_tokens(text, tokenizer)
    assert len(result) == 2, "Large input was not split correctly"
    mock_split.assert_called_once_with(text, tokenizer)


def test_split_single_text_on_tokens():
    text = "This is a test text, meaning to be taken seriously by this test only."
    mocked_tokenizer = MockTokenizer()
    tokenizer = Tokenizer(
        chunk_overlap=5,
        tokens_per_chunk=10,
        decode=mocked_tokenizer.decode,
        encode=lambda text: mocked_tokenizer.encode(text),
    )

    expected_splits = [
        "This is a ",
        "is a test ",
        "test text,",
        "text, mean",
        " meaning t",
        "ing to be ",
        "o be taken",
        "taken seri",
        " seriously",
        "ously by t",
        " by this t",
        "his test o",
        "est only.",
        "nly.",
    ]

    result = split_single_text_on_tokens(text=text, tokenizer=tokenizer)
    assert result == expected_splits

def test_split_multiple_texts_on_tokens_no_tick():
    texts = [
        "This is a test text, meaning to be taken seriously by this test only.",
        "This is th second text, meaning to be taken seriously by this test only.",
    ]

    mocked_tokenizer = MockTokenizer()
    tokenizer = Tokenizer(
        chunk_overlap=5,
        tokens_per_chunk=10,
        decode=mocked_tokenizer.decode,
        encode=lambda text: mocked_tokenizer.encode(text),
    )

    result = split_multiple_texts_on_tokens(texts, tokenizer, tick=None)
    assert result == [
        TextChunk(text_chunk="This is a ", source_doc_indices=[0], n_tokens=10),
        TextChunk(text_chunk="is a test ", source_doc_indices=[0], n_tokens=10),
        TextChunk(text_chunk="test text,", source_doc_indices=[0], n_tokens=10),
        TextChunk(text_chunk="text, mean", source_doc_indices=[0], n_tokens=10),
        TextChunk(text_chunk=" meaning t", source_doc_indices=[0], n_tokens=10),
        TextChunk(text_chunk="ing to be ", source_doc_indices=[0], n_tokens=10),
        TextChunk(text_chunk="o be taken", source_doc_indices=[0], n_tokens=10),
        TextChunk(text_chunk="taken seri", source_doc_indices=[0], n_tokens=10),
        TextChunk(text_chunk=" seriously", source_doc_indices=[0], n_tokens=10),
        TextChunk(text_chunk="ously by t", source_doc_indices=[0], n_tokens=10),
        TextChunk(text_chunk=" by this t", source_doc_indices=[0], n_tokens=10),
        TextChunk(text_chunk="his test o", source_doc_indices=[0], n_tokens=10),
        TextChunk(text_chunk="est only.T", source_doc_indices=[0, 1], n_tokens=10),
        TextChunk(text_chunk="nly.This i", source_doc_indices=[0, 1], n_tokens=10),
        TextChunk(text_chunk="his is th ", source_doc_indices=[1], n_tokens=10),
        TextChunk(text_chunk="s th secon", source_doc_indices=[1], n_tokens=10),
        TextChunk(text_chunk="second tex", source_doc_indices=[1], n_tokens=10),
        TextChunk(text_chunk="d text, me", source_doc_indices=[1], n_tokens=10),
        TextChunk(text_chunk="t, meaning", source_doc_indices=[1], n_tokens=10),
        TextChunk(text_chunk="aning to b", source_doc_indices=[1], n_tokens=10),
        TextChunk(text_chunk=" to be tak", source_doc_indices=[1], n_tokens=10),
        TextChunk(text_chunk="e taken se", source_doc_indices=[1], n_tokens=10),
        TextChunk(text_chunk="en serious", source_doc_indices=[1], n_tokens=10),
        TextChunk(text_chunk="riously by", source_doc_indices=[1], n_tokens=10),
        TextChunk(text_chunk="ly by this", source_doc_indices=[1], n_tokens=10),
        TextChunk(text_chunk=" this test", source_doc_indices=[1], n_tokens=10),
        TextChunk(text_chunk=" test only", source_doc_indices=[1], n_tokens=10),
        TextChunk(text_chunk=" only.", source_doc_indices=[1], n_tokens=6),
        TextChunk(text_chunk=".", source_doc_indices=[1], n_tokens=1),
    ]
    assert len(result) == 29, "Large input was not split correctly"


def test_split_multiple_texts_on_tokens_tick():
    texts = [
        "This is a test text, meaning to be taken seriously by this test only.",
        "This is th second text, meaning to be taken seriously by this test only.",
    ]

    mocked_tokenizer = MockTokenizer()
    mock_tick = MagicMock()
    tokenizer = Tokenizer(
        chunk_overlap=5,
        tokens_per_chunk=10,
        decode=mocked_tokenizer.decode,
        encode=lambda text: mocked_tokenizer.encode(text),
    )

    split_multiple_texts_on_tokens(texts, tokenizer, tick=mock_tick)
    mock_tick.assert_called()
