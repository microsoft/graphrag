# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from unittest import mock

import pytest
import tiktoken
from graphrag.index.text_splitting.text_splitting import (
    TokenTextSplitter,
    split_single_text_on_tokens,
)


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
def test_token_text_splitter(mock_split_text):
    expected_chunks = ["chunk1", "chunk2", "chunk3"]

    mock_split_text.return_value = expected_chunks

    splitter = TokenTextSplitter(chunk_size=5, chunk_overlap=2)

    splitter.split_text(["chunk1", "chunk2", "chunk3"])

    mock_split_text.assert_called_once()


def test_split_single_text_on_tokens():
    text = "This is a test text, meaning to be taken seriously by this test only."
    mocked_tokenizer = MockTokenizer()
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

    result = split_single_text_on_tokens(
        text=text,
        chunk_overlap=5,
        tokens_per_chunk=10,
        decode=mocked_tokenizer.decode,
        encode=lambda text: mocked_tokenizer.encode(text),
    )
    assert result == expected_splits


def test_split_single_text_on_tokens_no_overlap():
    text = "This is a test text, meaning to be taken seriously by this test only."
    enc = tiktoken.get_encoding("cl100k_base")

    def encode(text: str) -> list[int]:
        if not isinstance(text, str):
            text = f"{text}"
        return enc.encode(text)

    def decode(tokens: list[int]) -> str:
        return enc.decode(tokens)

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

    result = split_single_text_on_tokens(
        text=text,
        chunk_overlap=1,
        tokens_per_chunk=2,
        decode=decode,
        encode=lambda text: encode(text),
    )
    assert result == expected_splits
