# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Unit tests for the S3PipelineStorage class."""

import re
from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from graphrag.logger.base import ProgressLogger
from graphrag.storage.s3_pipeline_storage import S3PipelineStorage, create_s3_storage


@pytest.fixture
def s3_mock():
    """Set up a mock S3 service."""
    with mock_aws():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def bucket_name():
    """Return a test bucket name."""
    return "test-bucket"


@pytest.fixture
def test_prefix():
    """Return a test prefix."""
    return "test-prefix"


@pytest.fixture
def s3_bucket(s3_mock, bucket_name):
    """Create a test S3 bucket."""
    s3_mock.create_bucket(Bucket=bucket_name)
    return bucket_name


@pytest.fixture
def s3_storage(s3_bucket, test_prefix):
    """Create a test S3PipelineStorage instance."""
    return S3PipelineStorage(
        bucket_name=s3_bucket,
        prefix=test_prefix,
        encoding="utf-8",
        region_name="us-east-1",
    )


@pytest.mark.parametrize(
    ("prefix", "key", "expected"),
    [
        ("test-prefix", "test-key", "test-prefix/test-key"),
        ("test-prefix/", "test-key", "test-prefix/test-key"),
        ("test-prefix", "/test-key", "test-prefix/test-key"),
        ("", "test-key", "test-key"),
        (None, "test-key", "test-key"),
    ],
)
def test_get_full_key(s3_bucket, prefix, key, expected):
    """Test the _get_full_key method."""
    storage = S3PipelineStorage(bucket_name=s3_bucket, prefix=prefix)
    result = storage._get_full_key(key)  # noqa: SLF001
    assert result == expected


@pytest.mark.parametrize(
    ("prefix", "key", "expected"),
    [
        ("test-prefix", "test-prefix/test-key", "test-key"),
        ("test-prefix/", "test-prefix/test-key", "test-key"),
        ("", "test-key", "test-key"),
        (None, "test-key", "test-key"),
        ("test-prefix", "different-prefix/test-key", "different-prefix/test-key"),
    ],
)
def test_strip_prefix(s3_bucket, prefix, key, expected):
    """Test the _strip_prefix method."""
    storage = S3PipelineStorage(bucket_name=s3_bucket, prefix=prefix)
    result = storage._strip_prefix(key)  # noqa: SLF001
    assert result == expected


@pytest.mark.asyncio
async def test_get_nonexistent_key(s3_storage):
    """Test getting a nonexistent key."""
    result = await s3_storage.get("nonexistent-key")
    assert result is None


@pytest.mark.asyncio
async def test_set_and_get_string(s3_storage):
    """Test setting and getting a string value."""
    key = "test-key"
    value = "test-value"
    
    await s3_storage.set(key, value)
    result = await s3_storage.get(key)
    
    assert result == value


@pytest.mark.asyncio
async def test_set_and_get_bytes(s3_storage):
    """Test setting and getting a bytes value."""
    key = "test-key-bytes"
    value = b"test-value-bytes"
    
    await s3_storage.set(key, value)
    result = await s3_storage.get(key, as_bytes=True)
    
    assert result == value


@pytest.mark.asyncio
async def test_get_as_bytes(s3_storage):
    """Test getting a string value as bytes."""
    key = "test-key"
    value = "test-value"
    
    await s3_storage.set(key, value)
    result = await s3_storage.get(key, as_bytes=True)
    
    assert result == value.encode("utf-8")


@pytest.mark.asyncio
async def test_get_with_custom_encoding(s3_storage):
    """Test getting a value with a custom encoding."""
    key = "test-key-encoding"
    value = "test-value-encoding-äöü"
    custom_encoding = "latin-1"
    
    await s3_storage.set(key, value, encoding=custom_encoding)
    result = await s3_storage.get(key, encoding=custom_encoding)
    
    assert result == value


@pytest.mark.asyncio
async def test_has_existing_key(s3_storage):
    """Test checking if an existing key exists."""
    key = "test-key-exists"
    await s3_storage.set(key, "test-value")
    
    result = await s3_storage.has(key)
    
    assert result is True


@pytest.mark.asyncio
async def test_has_nonexistent_key(s3_storage):
    """Test checking if a nonexistent key exists."""
    result = await s3_storage.has("nonexistent-key")
    
    assert result is False


@pytest.mark.asyncio
async def test_delete_key(s3_storage):
    """Test deleting a key."""
    key = "test-key-delete"
    await s3_storage.set(key, "test-value")
    
    await s3_storage.delete(key)
    
    result = await s3_storage.has(key)
    assert result is False


@pytest.mark.asyncio
async def test_clear(s3_storage, s3_mock, bucket_name, test_prefix):
    """Test clearing all keys with the configured prefix."""
    # Add some objects with the test prefix
    await s3_storage.set("key1", "value1")
    await s3_storage.set("key2", "value2")
    
    # Add an object with a different prefix
    different_prefix = "different-prefix"
    different_storage = S3PipelineStorage(bucket_name=bucket_name, prefix=different_prefix)
    await different_storage.set("key3", "value3")
    
    # Clear the test storage
    await s3_storage.clear()
    
    # Check that objects with test prefix are gone
    assert not await s3_storage.has("key1")
    assert not await s3_storage.has("key2")
    
    # Check that object with different prefix still exists
    assert await different_storage.has("key3")


def test_child_storage(s3_storage, bucket_name, test_prefix):
    """Test creating a child storage."""
    child_name = "child"
    child_storage = s3_storage.child(child_name)
    
    assert isinstance(child_storage, S3PipelineStorage)
    assert child_storage._bucket_name == bucket_name  # noqa: SLF001
    assert child_storage._prefix == f"{test_prefix}/{child_name}"  # noqa: SLF001


def test_child_storage_with_none(s3_storage):
    """Test creating a child storage with None name."""
    child_storage = s3_storage.child(None)
    
    assert child_storage is s3_storage


def test_keys(s3_storage, s3_mock, bucket_name, test_prefix):
    """Test listing all keys."""
    # Add some objects
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/key1", Body=b"value1")
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/key2", Body=b"value2")
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/subdir/key3", Body=b"value3")
    
    # Add an object with a different prefix
    s3_mock.put_object(Bucket=bucket_name, Key="different-prefix/key4", Body=b"value4")
    
    keys = s3_storage.keys()
    
    assert sorted(keys) == ["key1", "key2", "subdir/key3"]


@pytest.mark.asyncio
async def test_get_creation_date(s3_storage, s3_mock, bucket_name, test_prefix):
    """Test getting the creation date for a key."""
    key = "test-key-date"
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/{key}", Body=b"value")
    
    with patch("graphrag.storage.s3_pipeline_storage.get_timestamp_formatted_with_local_tz") as mock_format:
        mock_format.return_value = "2025-03-20 09:00:00 -0400"
        result = await s3_storage.get_creation_date(key)
    
    assert result == "2025-03-20 09:00:00 -0400"


@pytest.mark.asyncio
async def test_get_creation_date_nonexistent(s3_storage):
    """Test getting the creation date for a nonexistent key."""
    with pytest.raises(FileNotFoundError):
        await s3_storage.get_creation_date("nonexistent-key")


def test_find(s3_storage, s3_mock, bucket_name, test_prefix):
    """Test finding files with a pattern."""
    # Add some test objects
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/file1.txt", Body=b"content1")
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/file2.txt", Body=b"content2")
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/subdir/file3.txt", Body=b"content3")
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/other.json", Body=b"{}")
    
    # Create a pattern to match .txt files
    pattern = re.compile(r"(?P<filename>file\d+)\.txt$")
    
    # Find matching files
    results = list(s3_storage.find(pattern))
    
    # Check results
    assert len(results) == 3
    assert ("file1.txt", {"filename": "file1"}) in results
    assert ("file2.txt", {"filename": "file2"}) in results
    assert ("subdir/file3.txt", {"filename": "file3"}) in results


def test_find_with_base_dir(s3_storage, s3_mock, bucket_name, test_prefix):
    """Test finding files with a base directory."""
    # Add some test objects
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/file1.txt", Body=b"content1")
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/subdir/file2.txt", Body=b"content2")
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/subdir/file3.txt", Body=b"content3")
    
    # Create a pattern to match .txt files
    pattern = re.compile(r"(?P<filename>file\d+)\.txt$")
    
    # Find matching files in the subdir
    results = list(s3_storage.find(pattern, base_dir="subdir"))
    
    # Check results
    assert len(results) == 2
    assert ("subdir/file2.txt", {"filename": "file2"}) in results
    assert ("subdir/file3.txt", {"filename": "file3"}) in results


def test_find_with_file_filter(s3_storage, s3_mock, bucket_name, test_prefix):
    """Test finding files with a file filter."""
    # Add some test objects
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/file1.txt", Body=b"content1")
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/file2.txt", Body=b"content2")
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/file3.txt", Body=b"content3")
    
    # Create a pattern to match .txt files
    pattern = re.compile(r"(?P<filename>file\d+)\.txt$")
    
    # Create a filter to match only file2
    file_filter = {"filename": r"file[23]"}
    
    # Find matching files
    results = list(s3_storage.find(pattern, file_filter=file_filter))
    
    # Check results
    assert len(results) == 2
    assert ("file2.txt", {"filename": "file2"}) in results
    assert ("file3.txt", {"filename": "file3"}) in results


def test_find_with_max_count(s3_storage, s3_mock, bucket_name, test_prefix):
    """Test finding files with a maximum count."""
    # Add some test objects
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/file1.txt", Body=b"content1")
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/file2.txt", Body=b"content2")
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/file3.txt", Body=b"content3")
    
    # Create a pattern to match .txt files
    pattern = re.compile(r"(?P<filename>file\d+)\.txt$")
    
    # Find matching files with a max count of 2
    results = list(s3_storage.find(pattern, max_count=2))
    
    # Check results
    assert len(results) == 2


def test_find_with_progress(s3_storage, s3_mock, bucket_name, test_prefix):
    """Test finding files with progress reporting."""
    # Add some test objects
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/file1.txt", Body=b"content1")
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/file2.txt", Body=b"content2")
    s3_mock.put_object(Bucket=bucket_name, Key=f"{test_prefix}/other.json", Body=b"{}")
    
    # Create a pattern to match .txt files
    pattern = re.compile(r"(?P<filename>file\d+)\.txt$")
    
    # Create a mock progress logger
    progress_logger = MagicMock(spec=ProgressLogger)
    
    # Find matching files with progress reporting
    list(s3_storage.find(pattern, progress=progress_logger))
    
    # Check that progress was reported
    assert progress_logger.call_count > 0


def test_create_progress_status(s3_storage):
    """Test creating a progress status."""
    progress = s3_storage._create_progress_status(5, 3, 10)  # noqa: SLF001
    
    assert progress.total_items == 10
    assert progress.completed_items == 8
    assert progress.description == "5 files loaded (3 filtered)"


def test_create_s3_storage(bucket_name):
    """Test creating an S3 storage using the factory function."""
    storage = create_s3_storage(
        bucket_name=bucket_name,
        prefix="test-prefix",
        encoding="latin-1",
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret",
        region_name="us-west-2",
    )
    
    assert isinstance(storage, S3PipelineStorage)
    assert storage._bucket_name == bucket_name  # noqa: SLF001
    assert storage._prefix == "test-prefix"  # noqa: SLF001
    assert storage._encoding == "latin-1"  # noqa: SLF001


@pytest.mark.asyncio
async def test_get_client_error(s3_storage):
    """Test handling of client errors in get method."""
    key = "test-key-error"
    
    # Mock the get_object method to raise a ClientError
    with patch.object(s3_storage._s3, "get_object") as mock_get_object:  # noqa: SLF001
        error_response = {"Error": {"Code": "InternalError", "Message": "Test error"}}
        mock_get_object.side_effect = ClientError(error_response, "GetObject")
        
        with pytest.raises(ClientError):
            await s3_storage.get(key)


@pytest.mark.asyncio
async def test_has_client_error(s3_storage):
    """Test handling of client errors in has method."""
    key = "test-key-error"
    
    # Mock the head_object method to raise a ClientError
    with patch.object(s3_storage._s3, "head_object") as mock_head_object:  # noqa: SLF001
        error_response = {"Error": {"Code": "InternalError", "Message": "Test error"}}
        mock_head_object.side_effect = ClientError(error_response, "HeadObject")
        
        with pytest.raises(ClientError):
            await s3_storage.has(key)


@pytest.mark.asyncio
async def test_clear_empty(s3_storage):
    """Test clearing an empty storage."""
    # Should not raise any exceptions
    await s3_storage.clear()


@pytest.mark.asyncio
async def test_clear_large_bucket(s3_storage, s3_mock, bucket_name, test_prefix):
    """Test clearing a bucket with more than 1000 objects."""
    # Mock the paginator to simulate a large bucket
    with patch.object(s3_storage._s3, "get_paginator") as mock_get_paginator:  # noqa: SLF001
        mock_paginator = MagicMock()
        mock_get_paginator.return_value = mock_paginator
        
        # Create two pages of results
        page1 = {"Contents": [{"Key": f"{test_prefix}/key{i}"} for i in range(1000)]}
        page2 = {"Contents": [{"Key": f"{test_prefix}/key{i}"} for i in range(1000, 1500)]}
        mock_paginator.paginate.return_value = [page1, page2]
        
        # Mock delete_objects to verify it's called correctly
        with patch.object(s3_storage._s3, "delete_objects") as mock_delete_objects:  # noqa: SLF001
            await s3_storage.clear()
            
            # Should be called twice, once for each batch of 1000 objects
            assert mock_delete_objects.call_count == 2


@pytest.mark.asyncio
async def test_warning_on_clear_without_prefix(s3_bucket, caplog):
    """Test that a warning is logged when clearing without a prefix."""
    storage = S3PipelineStorage(bucket_name=s3_bucket, prefix="")
    
    with patch.object(storage._s3, "delete_objects"):  # noqa: SLF001
        await storage.clear()
    
    assert "Clearing entire S3 bucket as no prefix was specified" in caplog.text
