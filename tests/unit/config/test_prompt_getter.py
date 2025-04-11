# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Unit tests for the PromptGetter classes."""

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from graphrag.config.prompt_getter import (
    LocalPromptGetter,
    PromptGetter,
    S3PromptGetter,
    create_prompt_getter,
    get_prompt_content,
)


@pytest.fixture
def s3_mock() -> Generator[Any, None, None]:
    """Set up a mock S3 service."""
    with mock_aws():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def bucket_name() -> str:
    """Return a test bucket name."""
    return "test-bucket"


@pytest.fixture
def s3_bucket(s3_mock: Any, bucket_name: str) -> str:
    """Create a test S3 bucket."""
    s3_mock.create_bucket(Bucket=bucket_name)
    return bucket_name


@pytest.fixture
def s3_prompt_content() -> str:
    """Return test prompt content for S3."""
    return "This is a test prompt from S3."


@pytest.fixture
def s3_prompt_path(bucket_name: str) -> str:
    """Return a test S3 prompt path."""
    return f"s3://{bucket_name}/prompts/test-prompt.txt"


@pytest.fixture
def s3_prompt(s3_mock: Any, bucket_name: str, s3_prompt_content: str) -> None:
    """Create a test prompt in S3."""
    s3_mock.put_object(
        Bucket=bucket_name,
        Key="prompts/test-prompt.txt",
        Body=s3_prompt_content.encode("utf-8"),
    )


@pytest.fixture
def local_root_dir() -> str:
    """Return the path to the test directory containing prompt files."""
    return str(Path(__file__).parent)


@pytest.mark.parametrize(
    ("prompt_file", "expected_content"),
    [
        ("prompt-a.txt", "Hello, World! A"),
        ("prompt-b.txt", "Hello, World! B"),
        ("prompt-c.txt", "Hello, World! C"),
        ("prompt-d.txt", "Hello, World! D"),
    ],
)
def test_local_prompt_getter_get_prompt(
    local_root_dir: str, prompt_file: str, expected_content: str
) -> None:
    """Test retrieving a prompt from the local filesystem."""
    # Arrange
    getter = LocalPromptGetter()

    # Act
    result = getter.get_prompt(prompt_file, root_dir=local_root_dir)

    # Assert
    assert result == expected_content


def test_local_prompt_getter_raises_error_when_root_dir_is_none() -> None:
    """Test that LocalPromptGetter raises an error when root_dir is None."""
    # Arrange
    getter = LocalPromptGetter()

    # Act & Assert
    with pytest.raises(ValueError, match=r".*root_dir.*must be defined.*"):
        getter.get_prompt("prompt-a.txt", root_dir=None)


@pytest.mark.parametrize(
    ("encoding", "expected_exception"),
    [
        ("utf-8", None),
        ("latin-1", None),
        ("invalid-encoding", LookupError),
    ],
)
def test_local_prompt_getter_with_different_encodings(
    local_root_dir: str, encoding: str, expected_exception: type | None
) -> None:
    """Test LocalPromptGetter with different encodings."""
    # Arrange
    getter = LocalPromptGetter()

    # Act & Assert
    if expected_exception:
        with pytest.raises(expected_exception):
            getter.get_prompt("prompt-a.txt", root_dir=local_root_dir, encoding=encoding)
    else:
        result = getter.get_prompt("prompt-a.txt", root_dir=local_root_dir, encoding=encoding)
        assert result == "Hello, World! A"


def test_s3_prompt_getter_get_prompt(
    s3_mock: Any, s3_bucket: str, s3_prompt: None, s3_prompt_path: str, s3_prompt_content: str
) -> None:
    """Test retrieving a prompt from S3."""
    # Arrange
    getter = S3PromptGetter()

    # Act
    result = getter.get_prompt(s3_prompt_path)

    # Assert
    assert result == s3_prompt_content


def test_s3_prompt_getter_raises_error_for_invalid_bucket() -> None:
    """Test that S3PromptGetter raises an error for an invalid bucket name."""
    # Arrange
    getter = S3PromptGetter()
    invalid_path = "s3:///invalid-path"  # Missing bucket name

    # Act & Assert
    with pytest.raises(ValueError, match=r".*`bucket_name` could not be extracted.*"):
        getter.get_prompt(invalid_path)


@pytest.mark.parametrize(
    ("encoding", "content", "expected_content"),
    [
        ("utf-8", "Test UTF-8 content", "Test UTF-8 content"),
        ("latin-1", "Test Latin-1 content äöü", "Test Latin-1 content äöü"),
    ],
)
def test_s3_prompt_getter_with_different_encodings(
    s3_mock: Any,
    s3_bucket: str,
    encoding: str,
    content: str,
    expected_content: str,
) -> None:
    """Test S3PromptGetter with different encodings."""
    # Arrange
    getter = S3PromptGetter()
    path = f"s3://{s3_bucket}/prompts/encoding-test.txt"
    
    # Create the test object with the specified encoding
    s3_mock.put_object(
        Bucket=s3_bucket,
        Key="prompts/encoding-test.txt",
        Body=content.encode(encoding),
    )

    # Act
    result = getter.get_prompt(path, encoding=encoding)

    # Assert
    assert result == expected_content


def test_s3_prompt_getter_client_error(s3_mock: Any) -> None:
    """Test handling of client errors in S3PromptGetter."""
    # Arrange
    getter = S3PromptGetter()
    path = "s3://non-existent-bucket/test.txt"

    # Act & Assert
    with pytest.raises(ClientError):
        getter.get_prompt(path)


def test_s3_prompt_getter_with_endpoint_url() -> None:
    """Test S3PromptGetter initialization with a custom endpoint URL."""
    # Arrange
    endpoint_url = "http://localhost:9000"
    
    # Act
    with patch("boto3.client") as mock_boto3_client:
        _ = S3PromptGetter(endpoint_url=endpoint_url)
        
        # Assert
        mock_boto3_client.assert_called_once_with("s3", endpoint_url=endpoint_url)


def test_create_prompt_getter_local() -> None:
    """Test creating a LocalPromptGetter."""
    # Arrange
    filepath = "local/path/to/prompt.txt"

    # Act
    getter = create_prompt_getter(filepath)

    # Assert
    assert isinstance(getter, LocalPromptGetter)


def test_create_prompt_getter_s3() -> None:
    """Test creating an S3PromptGetter."""
    # Arrange
    filepath = "s3://bucket/path/to/prompt.txt"

    # Act
    getter = create_prompt_getter(filepath)

    # Assert
    assert isinstance(getter, S3PromptGetter)


def test_create_prompt_getter_s3_with_endpoint_url() -> None:
    """Test creating an S3PromptGetter with a custom endpoint URL."""
    # Arrange
    filepath = "s3://bucket/path/to/prompt.txt"
    endpoint_url = "http://localhost:9000"

    # Act
    getter = create_prompt_getter(filepath, endpoint_url=endpoint_url)

    # Assert
    assert isinstance(getter, S3PromptGetter)


def test_create_prompt_getter_none() -> None:
    """Test creating a PromptGetter with None filepath."""
    # Arrange
    filepath = None

    # Act
    getter = create_prompt_getter(filepath)

    # Assert
    assert isinstance(getter, LocalPromptGetter)


@pytest.mark.parametrize(
    ("prompt_path", "root_dir", "expected_result"),
    [
        (None, "root_dir", None),
        ("prompt-a.txt", None, "Hello, World! A"),
    ],
)
def test_get_prompt_content(
    local_root_dir: str,
    prompt_path: str | None,
    root_dir: str | None,
    expected_result: str | None,
) -> None:
    """Test get_prompt_content function."""
    # Arrange
    if root_dir == "root_dir":
        root_dir = local_root_dir

    # Act
    with patch("graphrag.config.prompt_getter.create_prompt_getter") as mock_create:
        if prompt_path == "prompt-a.txt":
            mock_getter = MagicMock(spec=PromptGetter)
            mock_getter.get_prompt.return_value = "Hello, World! A"
            mock_create.return_value = mock_getter
        
        result = get_prompt_content(prompt_path, root_dir)

    # Assert
    assert result == expected_result
    if prompt_path:
        mock_create.assert_called_once_with(prompt_path, endpoint_url=None)


def test_get_prompt_content_with_s3(
    s3_mock: Any, s3_bucket: str, s3_prompt: None, s3_prompt_path: str, s3_prompt_content: str
) -> None:
    """Test get_prompt_content with an S3 path."""
    # Act
    result = get_prompt_content(s3_prompt_path, None, endpoint_url=None)

    # Assert
    assert result == s3_prompt_content


def test_get_prompt_content_with_endpoint_url() -> None:
    """Test get_prompt_content with a custom endpoint URL."""
    # Arrange
    prompt_path = "s3://bucket/path/to/prompt.txt"
    root_dir = None
    endpoint_url = "http://localhost:9000"
    
    # Act
    with patch("graphrag.config.prompt_getter.create_prompt_getter") as mock_create:
        mock_getter = MagicMock(spec=PromptGetter)
        mock_getter.get_prompt.return_value = "Test content"
        mock_create.return_value = mock_getter
        
        result = get_prompt_content(prompt_path, root_dir, endpoint_url=endpoint_url)
    
    # Assert
    mock_create.assert_called_once_with(prompt_path, endpoint_url=endpoint_url)
    mock_getter.get_prompt.assert_called_once_with(prompt_path, root_dir)
    assert result == "Test content"


@pytest.mark.parametrize(
    "endpoint_url",
    [None, ""],
)
def test_s3_prompt_getter_with_none_or_empty_endpoint_url(endpoint_url: str | None) -> None:
    """Test that when endpoint_url is None or empty, it uses AWS services by default."""
    # Arrange & Act
    with patch("boto3.client") as mock_client:
        S3PromptGetter(endpoint_url=endpoint_url)
        
        # Assert
        mock_client.assert_called_once()
        call_kwargs = mock_client.call_args.kwargs
        # Both None and empty string should result in endpoint_url=None
        assert call_kwargs["endpoint_url"] is None


@pytest.mark.parametrize(
    "endpoint_url",
    [None, ""],
)
def test_create_prompt_getter_s3_with_none_or_empty_endpoint_url(endpoint_url: str | None) -> None:
    """Test that when endpoint_url is None or empty in create_prompt_getter, it uses AWS services by default."""
    # Arrange
    filepath = "s3://bucket/path/to/prompt.txt"
    
    # Act
    with patch("boto3.client") as mock_client:
        getter = create_prompt_getter(filepath, endpoint_url=endpoint_url)
        
        # Assert
        assert isinstance(getter, S3PromptGetter)
        mock_client.assert_called_once()
        call_kwargs = mock_client.call_args.kwargs
        # Both None and empty string should result in endpoint_url=None
        assert call_kwargs["endpoint_url"] is None


@pytest.mark.parametrize(
    "endpoint_url",
    [None, ""],
)
def test_get_prompt_content_with_none_or_empty_endpoint_url(endpoint_url: str | None) -> None:
    """Test that when endpoint_url is None or empty in get_prompt_content, it uses AWS services by default."""
    # Arrange
    prompt_path = "s3://bucket/path/to/prompt.txt"
    root_dir = None
    
    # Act
    with patch("graphrag.config.prompt_getter.create_prompt_getter") as mock_create:
        mock_getter = MagicMock(spec=PromptGetter)
        mock_getter.get_prompt.return_value = "Test content"
        mock_create.return_value = mock_getter
        
        result = get_prompt_content(prompt_path, root_dir, endpoint_url=endpoint_url)
    
    # Assert
    mock_create.assert_called_once_with(prompt_path, endpoint_url=endpoint_url)
    mock_getter.get_prompt.assert_called_once_with(prompt_path, root_dir)
    assert result == "Test content"
