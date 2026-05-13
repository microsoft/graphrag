# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for BlobWorkflowLogger blob rotation logic."""

import json
from unittest.mock import MagicMock, patch

import pytest

from graphrag.logger.blob_workflow_logger import BlobWorkflowLogger


@pytest.fixture
def mock_blob_service():
    """Create a mock BlobServiceClient and related objects."""
    with patch(
        "graphrag.logger.blob_workflow_logger.BlobServiceClient"
    ) as mock_bsc_cls:
        mock_blob_client = MagicMock()
        mock_blob_client.exists.return_value = False

        mock_bsc = MagicMock()
        mock_bsc.get_blob_client.return_value = mock_blob_client

        mock_bsc_cls.return_value = mock_bsc

        yield mock_bsc, mock_blob_client


@pytest.fixture
def mock_credential():
    """Mock DefaultAzureCredential."""
    with patch(
        "graphrag.logger.blob_workflow_logger.DefaultAzureCredential"
    ) as mock_cred:
        yield mock_cred


def test_rotate_blob_does_not_reinitialize_handler(
    mock_blob_service, mock_credential
):
    """Test that blob rotation does not call __init__ on the handler.

    This verifies the fix for issue #2170 where calling self.__init__()
    during rotation caused 'cannot release un-acquired lock' errors.
    """
    mock_bsc, mock_blob_client = mock_blob_service

    logger = BlobWorkflowLogger(
        connection_string=None,
        container_name="test-container",
        blob_name="test.logs.json",
        base_dir="logs",
        account_url="https://test.blob.core.windows.net",
    )

    # Simulate reaching max block count
    logger._num_blocks = logger._max_block_count

    # Store reference to the original lock to verify it's not replaced
    original_lock = logger.lock

    # Write a log entry, which should trigger rotation
    logger._write_log({"type": "log", "data": "test message"})

    # Verify the lock was NOT replaced (i.e., __init__ was not called)
    assert logger.lock is original_lock

    # Verify block counter was reset (rotation happened)
    # After rotation (reset to 0) + 1 write = 1
    assert logger._num_blocks == 1

    # Verify a new blob client was created during rotation
    assert mock_bsc.get_blob_client.call_count > 1


def test_rotate_blob_creates_new_blob_name(mock_blob_service, mock_credential):
    """Test that rotation generates a new blob name."""
    mock_bsc, mock_blob_client = mock_blob_service

    logger = BlobWorkflowLogger(
        connection_string=None,
        container_name="test-container",
        blob_name="test.logs.json",
        base_dir="logs",
        account_url="https://test.blob.core.windows.net",
    )

    original_blob_name = logger._blob_name

    # Trigger rotation
    logger._rotate_blob()

    # New blob name should be different (auto-generated with timestamp)
    assert logger._blob_name != original_blob_name
    assert logger._num_blocks == 0
