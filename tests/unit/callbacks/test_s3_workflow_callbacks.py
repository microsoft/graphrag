# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Unit tests for the S3WorkflowCallbacks class."""

import json
from datetime import timezone
from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from graphrag.callbacks.s3_workflow_callbacks import (
    LogType,
    S3WorkflowCallbacks,
    _get_log_file_name,
)


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
def s3_bucket(s3_mock, bucket_name):
    """Create a test S3 bucket."""
    s3_mock.create_bucket(Bucket=bucket_name)
    return bucket_name


@pytest.fixture
def s3_callbacks(s3_bucket):
    """Create a test S3WorkflowCallbacks instance."""
    return S3WorkflowCallbacks(
        bucket_name=s3_bucket,
        base_dir="test-logs",
        log_file_name="test-log.json",
        encoding="utf-8"
    )


@pytest.fixture
def s3_callbacks_with_credentials(s3_bucket):
    """Create a test S3WorkflowCallbacks instance with AWS credentials."""
    return S3WorkflowCallbacks(
        bucket_name=s3_bucket,
        base_dir="test-logs",
        log_file_name="test-log.json",
        encoding="utf-8",
        aws_access_key_id="test-access-key",
        aws_secret_access_key="test-secret-key",
        region_name="us-west-2",
        endpoint_url="https://custom-endpoint.example.com"
    )


def test_init_with_no_bucket_name():
    """Test initialization with no bucket name."""
    with pytest.raises(ValueError, match="No bucket name provided for S3 storage"):
        S3WorkflowCallbacks(bucket_name=None)


def test_init_with_default_log_file_name(s3_bucket):
    """Test initialization with default log file name."""
    with patch("graphrag.callbacks.s3_workflow_callbacks._get_log_file_name") as mock_get_log_file_name:
        mock_get_log_file_name.return_value = "default-log.json"
        callbacks = S3WorkflowCallbacks(bucket_name=s3_bucket)
        assert callbacks._log_file_prefix == "default-log.json"  # noqa: SLF001


def test_get_log_file_name():
    """Test the _get_log_file_name function."""
    with patch("graphrag.callbacks.s3_workflow_callbacks.datetime") as mock_datetime:
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2025-03-22-10:00:00:000000"
        mock_datetime.now.return_value = mock_now
        
        result = _get_log_file_name()
        
        assert result == "report/2025-03-22-10:00:00:000000.logs.json"
        mock_datetime.now.assert_called_once_with(tz=timezone.utc)


def test_log_message(s3_callbacks, s3_mock, bucket_name):
    """Test the _log_message method."""
    with patch("graphrag.callbacks.s3_workflow_callbacks.datetime") as mock_datetime:
        mock_now = MagicMock()
        mock_now.isoformat.return_value = "2025-03-22T10:00:00+00:00"
        mock_datetime.now.return_value = mock_now
        
        s3_callbacks._log_message(   # noqa: SLF001
            log_type=LogType.LOG,
            message="Test message",
            log_level=20,  # INFO
            details={"key": "value"}
        )
        
        # Check that the log was written to S3
        response = s3_mock.list_objects_v2(Bucket=bucket_name, Prefix="test-logs/test-log.json")
        assert "Contents" in response
        assert len(response["Contents"]) == 1
        
        # Get the log content
        key = response["Contents"][0]["Key"]
        obj = s3_mock.get_object(Bucket=bucket_name, Key=key)
        content = obj["Body"].read().decode("utf-8")
        log_entry = json.loads(content)
        
        # Check the log entry
        assert log_entry["type"] == "log"
        assert log_entry["data"] == "Test message"
        assert log_entry["details"] == {"key": "value"}
        assert log_entry["timestamp"] == "2025-03-22T10:00:00+00:00"


@pytest.mark.parametrize(
    ("log_method", "log_type", "message", "expected_type", "extra_args"),
    [
        (
            "error",
            LogType.ERROR,
            "Error occurred",
            "error",
            {
                "cause": ValueError("Test error"),
                "stack": "Traceback: test stack trace",
                "details": {"key": "value"}
            }
        ),
        (
            "error",
            LogType.ERROR,
            "Error without cause",
            "error",
            {"details": {"key": "value"}}
        ),
        (
            "warning",
            LogType.WARNING,
            "Warning message",
            "warning",
            {"details": {"key": "value"}}
        ),
        (
            "log",
            LogType.LOG,
            "Info message",
            "log",
            {"details": {"key": "value"}}
        ),
    ],
)
def test_log_methods(s3_callbacks, s3_mock, bucket_name, log_method, log_type, message, expected_type, extra_args):
    """Test the error, warning, and log methods using parametrization."""
    with patch("graphrag.callbacks.s3_workflow_callbacks.datetime") as mock_datetime:
        mock_now = MagicMock()
        mock_now.isoformat.return_value = "2025-03-22T10:00:00+00:00"
        mock_datetime.now.return_value = mock_now
        
        # Call the appropriate method with the provided arguments
        method = getattr(s3_callbacks, log_method)
        method(message=message, **extra_args)
        
        # Check that the log was written to S3
        response = s3_mock.list_objects_v2(Bucket=bucket_name, Prefix="test-logs/test-log.json")
        assert "Contents" in response
        
        # Get the log content
        key = response["Contents"][0]["Key"]
        obj = s3_mock.get_object(Bucket=bucket_name, Key=key)
        content = obj["Body"].read().decode("utf-8")
        log_entry = json.loads(content)
        
        # Check the log entry
        assert log_entry["type"] == expected_type
        assert log_entry["data"] == message
        assert log_entry["timestamp"] == "2025-03-22T10:00:00+00:00"
        
        # Check details if provided
        if "details" in extra_args:
            assert log_entry["details"] == extra_args["details"]
        
        # Check error-specific fields
        if log_method == "error" and "cause" in extra_args:
            assert log_entry["cause"] == str(extra_args["cause"])
        
        if log_method == "error" and "stack" in extra_args:
            assert log_entry["stack"] == extra_args["stack"]


def test_write_log_client_error(s3_callbacks):
    """Test handling of client errors in _write_log method."""
    # First, access the property to ensure the client is created
    _ = s3_callbacks._s3_client  # noqa: SLF001
    
    # Now patch boto3.client to return a mock for subsequent calls
    with patch("graphrag.callbacks.s3_workflow_callbacks.boto3") as mock_boto3:
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "InternalError", "Message": "Test error"}}
        mock_client.put_object.side_effect = ClientError(error_response, "PutObject")
        mock_boto3.client.return_value = mock_client
        
        # Force recreation of the client by setting the private attribute to None
        # We need to use name mangling to access the private attribute
        s3_callbacks._S3WorkflowCallbacks__s3_client = None  # noqa: SLF001
        
        with patch("graphrag.callbacks.s3_workflow_callbacks.logger") as mock_logger:
            # This should not raise an exception due to no-op behavior
            s3_callbacks._write_log({"type": "log", "data": "Test message"})   # noqa: SLF001
            
            # Check that the error was logged
            mock_logger.exception.assert_called_once()


def test_log_rotation(s3_callbacks, s3_mock, bucket_name):
    """Test log file rotation when block count exceeds the limit."""
    # Set a low max block count for testing
    s3_callbacks._max_block_count = 2  # noqa: SLF001
    
    # Write logs to trigger rotation
    s3_callbacks.log("Log message 1")
    s3_callbacks.log("Log message 2")
    
    # This should trigger rotation
    with patch("graphrag.callbacks.s3_workflow_callbacks._get_log_file_name") as mock_get_log_file_name:
        mock_get_log_file_name.return_value = "new-log.json"
        with patch("graphrag.callbacks.s3_workflow_callbacks.logger") as mock_logger:
            s3_callbacks.log("Log message 3")
            
            # Check that rotation was logged
            mock_logger.info.assert_called_with(
                "Created new log file due to block count limit: %s", "new-log.json"
            )
    
    # Check that the block counter was reset
    assert s3_callbacks._num_blocks == 1  # noqa: SLF001
    
    # Check that the log file prefix was updated
    assert s3_callbacks._log_file_prefix == "test-logs/new-log.json"  # noqa: SLF001

def test_multiple_logs_without_rotation(s3_callbacks, s3_mock, bucket_name):
    """Test writing multiple logs without triggering rotation."""
    # Set a higher max block count to avoid rotation
    s3_callbacks._max_block_count = 10  # noqa: SLF001
    
    # Write multiple logs
    for i in range(5):
        s3_callbacks.log(f"Log message {i}")
    
    # Check that all logs were written to S3
    response = s3_mock.list_objects_v2(Bucket=bucket_name, Prefix="test-logs/test-log.json")
    assert "Contents" in response
    assert len(response["Contents"]) == 5
    
    # Check that the block counter was incremented correctly
    assert s3_callbacks._num_blocks == 5  # noqa: SLF001


def test_init_with_aws_credentials():
    """Test initialization with AWS credentials."""
    with patch("graphrag.callbacks.s3_workflow_callbacks.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Create instance with credentials
        callbacks = S3WorkflowCallbacks(
            bucket_name="test-bucket",
            aws_access_key_id="test-access-key",
            aws_secret_access_key="test-secret-key",
            region_name="us-west-2"
        )
        
        # Verify credentials are stored but client is not created yet
        assert callbacks._aws_access_key_id == "test-access-key"  # noqa: SLF001
        assert callbacks._aws_secret_access_key == "test-secret-key"  # noqa: SLF001
        assert callbacks._region_name == "us-west-2"  # noqa: SLF001
        assert mock_boto3.client.call_count == 0
        
        # Access the client to trigger lazy loading
        _ = callbacks._s3_client  # noqa: SLF001
        
        # Verify boto3.client was called with the correct arguments
        mock_boto3.client.assert_called_once_with(
            "s3",
            aws_access_key_id="test-access-key",
            aws_secret_access_key="test-secret-key",
            region_name="us-west-2"
        )


def test_init_with_endpoint_url():
    """Test initialization with endpoint URL."""
    with patch("graphrag.callbacks.s3_workflow_callbacks.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Create instance with endpoint URL
        callbacks = S3WorkflowCallbacks(
            bucket_name="test-bucket",
            endpoint_url="https://custom-endpoint.example.com"
        )
        
        # Verify endpoint_url is stored but client is not created yet
        assert callbacks._endpoint_url == "https://custom-endpoint.example.com"  # noqa: SLF001
        assert mock_boto3.client.call_count == 0
        
        # Access the client to trigger lazy loading
        _ = callbacks._s3_client  # noqa: SLF001
        
        # Verify boto3.client was called with the correct arguments
        mock_boto3.client.assert_called_once_with(
            "s3",
            endpoint_url="https://custom-endpoint.example.com"
        )


def test_init_with_aws_credentials_and_endpoint_url():
    """Test initialization with both AWS credentials and endpoint URL."""
    with patch("graphrag.callbacks.s3_workflow_callbacks.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Create instance with both credentials and endpoint URL
        callbacks = S3WorkflowCallbacks(
            bucket_name="test-bucket",
            aws_access_key_id="test-access-key",
            aws_secret_access_key="test-secret-key",
            region_name="us-west-2",
            endpoint_url="https://custom-endpoint.example.com"
        )
        
        # Verify credentials and endpoint_url are stored but client is not created yet
        assert callbacks._aws_access_key_id == "test-access-key"  # noqa: SLF001
        assert callbacks._aws_secret_access_key == "test-secret-key"  # noqa: SLF001
        assert callbacks._region_name == "us-west-2"  # noqa: SLF001
        assert callbacks._endpoint_url == "https://custom-endpoint.example.com"  # noqa: SLF001
        assert mock_boto3.client.call_count == 0
        
        # Access the client to trigger lazy loading
        _ = callbacks._s3_client  # noqa: SLF001
        
        # Verify boto3.client was called with the correct arguments
        mock_boto3.client.assert_called_once_with(
            "s3",
            endpoint_url="https://custom-endpoint.example.com",
            aws_access_key_id="test-access-key",
            aws_secret_access_key="test-secret-key",
            region_name="us-west-2"
        )


def test_init_with_partial_aws_credentials():
    """Test initialization with partial AWS credentials (should not use them)."""
    with patch("graphrag.callbacks.s3_workflow_callbacks.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Create instance with only access key but no secret key
        callbacks = S3WorkflowCallbacks(
            bucket_name="test-bucket",
            aws_access_key_id="test-access-key",
            region_name="us-west-2"
        )
        
        # Verify credentials are stored but client is not created yet
        assert callbacks._aws_access_key_id == "test-access-key"  # noqa: SLF001
        assert callbacks._aws_secret_access_key is None  # noqa: SLF001
        assert callbacks._region_name == "us-west-2"  # noqa: SLF001
        assert mock_boto3.client.call_count == 0
        
        # Access the client to trigger lazy loading
        _ = callbacks._s3_client  # noqa: SLF001
        
        # Verify boto3.client was called without credentials
        mock_boto3.client.assert_called_once_with(
            "s3",
            region_name="us-west-2"
        )


def test_init_with_empty_endpoint_url():
    """Test initialization with empty endpoint URL (should not use it)."""
    with patch("graphrag.callbacks.s3_workflow_callbacks.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Create instance with empty endpoint URL
        callbacks = S3WorkflowCallbacks(
            bucket_name="test-bucket",
            endpoint_url=""
        )
        
        # Verify endpoint_url is stored but client is not created yet
        assert callbacks._endpoint_url == ""  # noqa: SLF001
        assert mock_boto3.client.call_count == 0
        
        # Access the client to trigger lazy loading
        _ = callbacks._s3_client  # noqa: SLF001
        
        # Verify boto3.client was called without endpoint_url
        mock_boto3.client.assert_called_once_with("s3")


def test_init_with_whitespace_endpoint_url():
    """Test initialization with whitespace endpoint URL (should not use it)."""
    with patch("graphrag.callbacks.s3_workflow_callbacks.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Create instance with whitespace endpoint URL
        callbacks = S3WorkflowCallbacks(
            bucket_name="test-bucket",
            endpoint_url="   "
        )
        
        # Verify endpoint_url is stored but client is not created yet
        assert callbacks._endpoint_url == "   "  # noqa: SLF001
        assert mock_boto3.client.call_count == 0
        
        # Access the client to trigger lazy loading
        _ = callbacks._s3_client  # noqa: SLF001
        
        # Verify boto3.client was called without endpoint_url
        mock_boto3.client.assert_called_once_with("s3")


def test_lazy_loading_s3_client():
    """Test that the S3 client is lazily loaded only when accessed."""
    with patch("graphrag.callbacks.s3_workflow_callbacks.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Create instance
        callbacks = S3WorkflowCallbacks(bucket_name="test-bucket")
        
        # Verify client is not created during initialization
        assert mock_boto3.client.call_count == 0
        
        # We can't directly access the private attribute due to name mangling
        # Instead, we'll verify the client is created only when the property is accessed
        
        # First access to the property should create the client
        client1 = callbacks._s3_client  # noqa: SLF001
        assert mock_boto3.client.call_count == 1
        assert client1 is mock_client
        
        # Second access should reuse the existing client
        client2 = callbacks._s3_client  # noqa: SLF001
        assert mock_boto3.client.call_count == 1  # Still only called once
        assert client2 is client1  # Same instance
