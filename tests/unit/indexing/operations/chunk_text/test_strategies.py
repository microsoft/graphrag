# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from unittest.mock import Mock, patch

from graphrag.config.models.chunking_config import ChunkingConfig
from graphrag.index.operations.chunk_text.bootstrap import bootstrap
from graphrag.index.operations.chunk_text.strategies import (
    get_encoding_fn,
    run_sentences,
    run_tokens,
)
from graphrag.index.operations.chunk_text.typing import TextChunk


class TestRunSentences:
    def setup_method(self, method):
        bootstrap()

    def test_basic_functionality(self):
        """Test basic sentence splitting without metadata"""
        input = ["This is a test. Another sentence."]
        tick = Mock()
        chunks = list(run_sentences(input, ChunkingConfig(), tick))

        assert len(chunks) == 2
        assert chunks[0].text_chunk == "This is a test."
        assert chunks[1].text_chunk == "Another sentence."
        assert all(c.source_doc_indices == [0] for c in chunks)
        tick.assert_called_once_with(1)

    def test_multiple_documents(self):
        """Test processing multiple input documents"""
        input = ["First. Document.", "Second. Doc."]
        tick = Mock()
        chunks = list(run_sentences(input, ChunkingConfig(), tick))

        assert len(chunks) == 4
        assert chunks[0].source_doc_indices == [0]
        assert chunks[2].source_doc_indices == [1]
        assert tick.call_count == 2

    def test_mixed_whitespace_handling(self):
        """Test input with irregular whitespace"""
        input = ["   Sentence with spaces.  Another one!   "]
        chunks = list(run_sentences(input, ChunkingConfig(), Mock()))
        assert chunks[0].text_chunk == "   Sentence with spaces."
        assert chunks[1].text_chunk == "Another one!"


class TestRunTokens:
    @patch("tiktoken.get_encoding")
    def test_basic_functionality(self, mock_get_encoding):
        mock_encoder = Mock()
        mock_encoder.encode.side_effect = lambda x: list(x.encode())
        mock_encoder.decode.side_effect = lambda x: bytes(x).decode()
        mock_get_encoding.return_value = mock_encoder

        # Input and config
        input = [
            "Marley was dead: to begin with. There is no doubt whatever about that. The register of his burial was signed by the clergyman, the clerk, the undertaker, and the chief mourner. Scrooge signed it. And Scrooge's name was good upon 'Change, for anything he chose to put his hand to."
        ]
        config = ChunkingConfig(size=5, overlap=1, encoding_model="fake-encoding")
        tick = Mock()

        # Run the function
        chunks = list(run_tokens(input, config, tick))

        # Verify output
        assert len(chunks) > 0
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)
        tick.assert_called_once_with(1)

    @patch("tiktoken.get_encoding")
    def test_non_string_input(self, mock_get_encoding):
        """Test handling of non-string input (e.g., numbers)."""
        mock_encoder = Mock()
        mock_encoder.encode.side_effect = lambda x: list(str(x).encode())
        mock_encoder.decode.side_effect = lambda x: bytes(x).decode()
        mock_get_encoding.return_value = mock_encoder

        input = [123]  # Non-string input
        config = ChunkingConfig(size=5, overlap=1, encoding_model="fake-encoding")
        tick = Mock()

        chunks = list(run_tokens(input, config, tick))  # type: ignore

        # Verify non-string input is handled
        assert len(chunks) > 0
        assert "123" in chunks[0].text_chunk


@patch("tiktoken.get_encoding")
def test_get_encoding_fn_encode(mock_get_encoding):
    # Create a mock encoding object with encode and decode methods
    mock_encoding = Mock()
    mock_encoding.encode = Mock(return_value=[1, 2, 3])
    mock_encoding.decode = Mock(return_value="decoded text")

    # Configure the mock_get_encoding to return the mock encoding object
    mock_get_encoding.return_value = mock_encoding

    # Call the function to get encode and decode functions
    encode, _ = get_encoding_fn("mock_encoding")

    # Test the encode function
    encoded_text = encode("test text")
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
    _, decode = get_encoding_fn("mock_encoding")

    decoded_text = decode([1, 2, 3])
    assert decoded_text == "decoded text"
    mock_encoding.decode.assert_called_once_with([1, 2, 3])
