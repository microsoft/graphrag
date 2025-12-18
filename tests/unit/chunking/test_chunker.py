# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from unittest.mock import Mock, patch

from graphrag.chunking.bootstrap import bootstrap
from graphrag.chunking.chunker_factory import create_chunker
from graphrag.chunking.token_chunker import (
    split_text_on_tokens,
)
from graphrag.config.enums import ChunkStrategyType
from graphrag.config.models.chunking_config import ChunkingConfig
from graphrag.tokenizer.get_tokenizer import get_tokenizer


class MockTokenizer:
    def encode(self, text):
        return [ord(char) for char in text]

    def decode(self, token_ids):
        return "".join(chr(id) for id in token_ids)


tokenizer = get_tokenizer()


class TestRunSentences:
    def setup_method(self, method):
        bootstrap()

    def test_basic_functionality(self):
        """Test basic sentence splitting without metadata"""
        input = "This is a test. Another sentence."
        chunker = create_chunker(ChunkingConfig(strategy=ChunkStrategyType.sentence))
        chunks = chunker.chunk(input)

        assert len(chunks) == 2
        assert chunks[0] == "This is a test."
        assert chunks[1] == "Another sentence."

    def test_multiple_documents(self):
        """Test processing multiple input documents"""
        input = ["First. Document.", "Second. Doc."]
        chunker = create_chunker(ChunkingConfig(strategy=ChunkStrategyType.sentence))
        chunks = [chunk for doc in input for chunk in chunker.chunk(doc)]
        assert len(chunks) == 4

    def test_mixed_whitespace_handling(self):
        """Test input with irregular whitespace"""
        input = "   Sentence with spaces. Another one!   "
        chunker = create_chunker(ChunkingConfig(strategy=ChunkStrategyType.sentence))
        chunks = chunker.chunk(input)
        assert chunks[0] == "   Sentence with spaces."
        assert chunks[1] == "Another one!"


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
            strategy=ChunkStrategyType.tokens,
        )

        chunker = create_chunker(config, tokenizer=tokenizer)
        chunks = chunker.chunk(input)

        assert len(chunks) > 0


def test_split_text_str_empty():
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


def test_split_text_on_tokens_no_overlap():
    text = "This is a test text, meaning to be taken seriously by this test only."
    tok = get_tokenizer(encoding_model="cl100k_base")

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

    result = split_text_on_tokens(
        text=text,
        chunk_size=2,
        chunk_overlap=1,
        decode=tok.decode,
        encode=tok.encode,
    )
    assert result == expected_splits


@patch("tiktoken.get_encoding")
def test_get_encoding_fn_encode(mock_get_encoding):
    # Create a mock encoding object with encode and decode methods
    mock_encoding = Mock()
    mock_encoding.encode = Mock(return_value=[1, 2, 3])
    mock_encoding.decode = Mock(return_value="decoded text")

    # Configure the mock_get_encoding to return the mock encoding object
    mock_get_encoding.return_value = mock_encoding

    # Call the function to get encode and decode functions
    tokenizer = get_tokenizer(encoding_model="mock_encoding")

    # Test the encode function
    encoded_text = tokenizer.encode("test text")
    assert encoded_text == [1, 2, 3]
    mock_encoding.encode.assert_called_once_with("test text")


@patch("tiktoken.get_encoding")
def test_get_encoding_fn_decode(mock_get_encoding):
    # Create a mock encoding object with encode and decode methods
    mock_encoding = Mock()
    mock_encoding.encode = Mock(return_value=[1, 2, 3])
    mock_encoding.decode = Mock(return_value="decoded text")

    # Configure the mock_get_encoding to return the mock encoding object
    mock_get_encoding.return_value = mock_encoding

    # Call the function to get encode and decode functions
    tokenizer = get_tokenizer(encoding_model="mock_encoding")

    decoded_text = tokenizer.decode([1, 2, 3])
    assert decoded_text == "decoded text"
    mock_encoding.decode.assert_called_once_with([1, 2, 3])
