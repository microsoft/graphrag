# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from typing import Any
from unittest.mock import Mock, patch

from graphrag.tokenizer.get_tokenizer import get_tokenizer
from graphrag_chunking.bootstrap_nltk import bootstrap
from graphrag_chunking.chunk_strategy_type import ChunkerType
from graphrag_chunking.chunker_factory import create_chunker
from graphrag_chunking.chunking_config import ChunkingConfig
from graphrag_chunking.token_chunker import (
    split_text_on_tokens,
)
from graphrag_llm.tokenizer import Tokenizer


class MockTokenizer(Tokenizer):
    def __init__(self, **kwargs: Any) -> None:
        """Initialize the LiteLLM Tokenizer."""

    def encode(self, text) -> list[int]:
        return [ord(char) for char in text]

    def decode(self, tokens) -> str:
        return "".join(chr(id) for id in tokens)


class TestRunSentences:
    def setup_method(self, method):
        bootstrap()

    def test_basic_functionality(self):
        """Test basic sentence splitting"""
        input = "This is a test. Another sentence. And a third one!"
        chunker = create_chunker(ChunkingConfig(type=ChunkerType.Sentence))
        chunks = chunker.chunk(input)

        assert len(chunks) == 3
        assert chunks[0].text == "This is a test."
        assert chunks[0].index == 0
        assert chunks[0].start_char == 0
        assert chunks[0].end_char == 14

        assert chunks[1].text == "Another sentence."
        assert chunks[1].index == 1
        assert chunks[1].start_char == 16
        assert chunks[1].end_char == 32

        assert chunks[2].text == "And a third one!"
        assert chunks[2].index == 2
        assert chunks[2].start_char == 34
        assert chunks[2].end_char == 49

    def test_mixed_whitespace_handling(self):
        """Test input with irregular whitespace"""
        input = "   Sentence with spaces. Another one!   "
        chunker = create_chunker(ChunkingConfig(type=ChunkerType.Sentence))
        chunks = chunker.chunk(input)

        assert len(chunks) == 2
        assert chunks[0].text == "Sentence with spaces."
        assert chunks[0].index == 0
        assert chunks[0].start_char == 3
        assert chunks[0].end_char == 23

        assert chunks[1].text == "Another one!"
        assert chunks[1].index == 1
        assert chunks[1].start_char == 25
        assert chunks[1].end_char == 36


class TestRunTokens:
    @patch("tiktoken.get_encoding")
    def test_basic_functionality(self, mock_get_encoding):
        mock_encoder = Mock()
        mock_encoder.encode.side_effect = lambda x: list(x.encode())
        mock_encoder.decode.side_effect = lambda x: bytes(x).decode()
        mock_get_encoding.return_value = mock_encoder

        input = "Marley was dead: to begin with. There is no doubt whatever about that. The register of his burial was signed by the clergyman, the clerk, the undertaker, and the chief mourner. Scrooge signed it. And Scrooge's name was good upon 'Change, for anything he chose to put his hand to."

        config = ChunkingConfig(
            size=5,
            overlap=1,
            encoding_model="fake-encoding",
            type=ChunkerType.Tokens,
        )

        chunker = create_chunker(config, mock_encoder.encode, mock_encoder.decode)
        chunks = chunker.chunk(input)

        assert len(chunks) > 0


def test_split_text_str_empty():
    tokenizer = get_tokenizer()
    result = split_text_on_tokens(
        "",
        chunk_size=5,
        chunk_overlap=2,
        encode=tokenizer.encode,
        decode=tokenizer.decode,
    )
    assert result == []


def test_split_text_on_tokens():
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

    result = split_text_on_tokens(
        text=text,
        chunk_overlap=5,
        chunk_size=10,
        decode=mocked_tokenizer.decode,
        encode=lambda text: mocked_tokenizer.encode(text),
    )
    assert result == expected_splits


def test_split_text_on_tokens_one_overlap():
    text = "This is a test text, meaning to be taken seriously by this test only."
    tokenizer = get_tokenizer(encoding_model="o200k_base")

    expected_splits = [
        "This is",
        " is a",
        " a test",
        " test text",
        " text,",
        ", meaning",
        " meaning to",
        " to be",
        " be taken",
        " taken seriously",
        " seriously by",
        " by this",
        " this test",
        " test only",
        " only.",
    ]

    result = split_text_on_tokens(
        text=text,
        chunk_size=2,
        chunk_overlap=1,
        decode=tokenizer.decode,
        encode=tokenizer.encode,
    )
    assert result == expected_splits


def test_split_text_on_tokens_no_overlap():
    text = "This is a test text, meaning to be taken seriously by this test only."
    tokenizer = get_tokenizer(encoding_model="o200k_base")

    expected_splits = [
        "This is a",
        " test text,",
        " meaning to be",
        " taken seriously by",
        " this test only",
        ".",
    ]

    result = split_text_on_tokens(
        text=text,
        chunk_size=3,
        chunk_overlap=0,
        decode=tokenizer.decode,
        encode=tokenizer.encode,
    )

    assert result == expected_splits
