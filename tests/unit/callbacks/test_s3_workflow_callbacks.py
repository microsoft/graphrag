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
    with patch.object(s3_callbacks, "_s3_client") as mock_s3_client:
        error_response = {"Error": {"Code": "InternalError", "Message": "Test error"}}
        mock_s3_client.put_object.side_effect = ClientError(error_response, "PutObject")
        
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
