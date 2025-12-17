# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from unittest.mock import Mock, patch

from graphrag.chunking.bootstrap import bootstrap
from graphrag.chunking.chunker import create_chunker
from graphrag.config.enums import ChunkStrategyType
from graphrag.config.models.chunking_config import ChunkingConfig
from graphrag.tokenizer.get_tokenizer import get_tokenizer


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

        chunker = create_chunker(config)
        chunks = chunker.chunk(input)

        assert len(chunks) > 0


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
