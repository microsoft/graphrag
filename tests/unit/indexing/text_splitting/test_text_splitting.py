# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from unittest import mock
from unittest.mock import MagicMock

import pytest
import tiktoken

from graphrag.index.text_splitting.text_splitting import (
    NoopTextSplitter,
    Tokenizer,
    TokenTextSplitter,
    split_multiple_texts_on_tokens,
    split_single_text_on_tokens,
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
def test_token_text_splitter(mock_tokenizer, mock_split_text):
    text = "chunk1 chunk2 chunk3"
    expected_chunks = ["chunk1", "chunk2", "chunk3"]

    mocked_tokenizer = MagicMock()
    mock_tokenizer.return_value = mocked_tokenizer
    mock_split_text.return_value = expected_chunks

    splitter = TokenTextSplitter()

    splitter.split_text(["chunk1", "chunk2", "chunk3"])

    mock_split_text.assert_called_once_with(text=text, tokenizer=mocked_tokenizer)


def test_encode_basic():
    splitter = TokenTextSplitter()
    result = splitter.encode("abc def")

    assert result == [13997, 711], "Encoding failed to return expected tokens"


def test_num_tokens_empty_input():
    splitter = TokenTextSplitter()
    result = splitter.num_tokens("")

    assert result == 0, "Token count for empty input should be 0"


def test_model_name():
    splitter = TokenTextSplitter(model_name="gpt-4o")
    result = splitter.encode("abc def")

    assert result == [26682, 1056], "Encoding failed to return expected tokens"


@mock.patch("tiktoken.encoding_for_model", side_effect=KeyError)
@mock.patch("tiktoken.get_encoding")
def test_model_name_exception(mock_get_encoding, mock_encoding_for_model):
    mock_get_encoding.return_value = mock.MagicMock()

    TokenTextSplitter(model_name="mock_model", encoding_name="mock_encoding")

    mock_get_encoding.assert_called_once_with("mock_encoding")
    mock_encoding_for_model.assert_called_once_with("mock_model")


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
        "taken seri",  # cspell:disable-line
        " seriously",
        "ously by t",  # cspell:disable-line
        " by this t",
        "his test o",
        "est only.",
    ]

    result = split_single_text_on_tokens(text=text, tokenizer=tokenizer)
    assert result == expected_splits


def test_split_multiple_texts_on_tokens():
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


def test_split_single_text_on_tokens_no_overlap():
    text = "This is a test text, meaning to be taken seriously by this test only."
    enc = tiktoken.get_encoding("cl100k_base")

    def encode(text: str) -> list[int]:
        if not isinstance(text, str):
            text = f"{text}"
        return enc.encode(text)

    def decode(tokens: list[int]) -> str:
        return enc.decode(tokens)

    tokenizer = Tokenizer(
        chunk_overlap=1,
        tokens_per_chunk=2,
        decode=decode,
        encode=lambda text: encode(text),
    )

    expected_splits = [
        "This is",
        " is a",
        " a test",
        " test text",
        " text,",
        ", meaning",
        " meaning to",
        " to be",
        " be taken",  # cspell:disable-line
        " taken seriously",  # cspell:disable-line
        " seriously by",
        " by this",  # cspell:disable-line
        " this test",
        " test only",
        " only.",
    ]

    result = split_single_text_on_tokens(text=text, tokenizer=tokenizer)
    assert result == expected_splits
