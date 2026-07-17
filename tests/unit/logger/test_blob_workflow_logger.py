# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Unit tests for the BlobWorkflowLogger."""

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


def _make_logger() -> BlobWorkflowLogger:
    return BlobWorkflowLogger(
        connection_string=None,
        container_name="test-container",
        blob_name="test.logs.json",
        base_dir="logs",
        account_url="https://test.blob.core.windows.net",
    )


def test_init_requires_container_name(mock_credential):
    """Test that a missing container name raises a ValueError."""
    with pytest.raises(ValueError, match="No container name provided"):
        BlobWorkflowLogger(
            connection_string=None,
            container_name=None,
            account_url="https://test.blob.core.windows.net",
        )


def test_init_requires_connection_or_account_url():
    """Test that missing both connection string and account url raises."""
    with pytest.raises(ValueError, match="No storage account blob url provided"):
        BlobWorkflowLogger(
            connection_string=None,
            container_name="test-container",
        )


def test_init_creates_append_blob(mock_blob_service, mock_credential):
    """Test that a new append blob is created on initialization."""
    _mock_bsc, mock_blob_client = mock_blob_service

    logger = _make_logger()

    mock_blob_client.create_append_blob.assert_called_once()
    assert logger._num_blocks == 0  # noqa: SLF001
    assert logger._base_dir == "logs"  # noqa: SLF001


def test_init_uses_provided_blob_name(mock_blob_service, mock_credential):
    """Test that the provided blob name is honored and nested under base_dir."""
    logger = _make_logger()

    assert logger._blob_name == "logs/test.logs.json"  # noqa: SLF001


def test_rotate_blob_does_not_reinitialize_handler(mock_blob_service, mock_credential):
    """Test that blob rotation does not call __init__ on the handler.

    This verifies the fix for issue #2170 where calling self.__init__()
    during rotation caused 'cannot release un-acquired lock' errors.
    """
    mock_bsc, _mock_blob_client = mock_blob_service

    logger = _make_logger()

    # Simulate reaching max block count
    logger._num_blocks = logger._max_block_count  # noqa: SLF001

    # Store reference to the original lock to verify it's not replaced
    original_lock = logger.lock

    # Write a log entry, which should trigger rotation
    logger._write_log({"type": "log", "data": "test message"})  # noqa: SLF001

    # Verify the lock was NOT replaced (i.e., __init__ was not called)
    assert logger.lock is original_lock

    # Verify block counter was reset (rotation happened)
    # After rotation (reset to 0) + 1 write = 1
    assert logger._num_blocks == 1  # noqa: SLF001

    # Verify a new blob client was created during rotation
    assert mock_bsc.get_blob_client.call_count > 1


def test_rotate_blob_creates_new_blob_name(mock_blob_service, mock_credential):
    """Test that rotation generates a new blob name."""
    _mock_bsc, _mock_blob_client = mock_blob_service

    logger = _make_logger()

    original_blob_name = logger._blob_name  # noqa: SLF001

    # Trigger rotation
    logger._rotate_blob()  # noqa: SLF001

    # New blob name should be different (auto-generated with timestamp)
    assert logger._blob_name != original_blob_name  # noqa: SLF001
    assert logger._num_blocks == 0  # noqa: SLF001


def test_write_log_appends_block(mock_blob_service, mock_credential):
    """Test that writing a log appends an encoded block and increments count."""
    _mock_bsc, mock_blob_client = mock_blob_service

    logger = _make_logger()

    logger._write_log({"type": "log", "data": "hello"})  # noqa: SLF001

    mock_blob_client.append_block.assert_called_once()
    (payload,), _kwargs = mock_blob_client.append_block.call_args
    decoded = json.loads(payload.decode("utf-8"))
    assert decoded == {"type": "log", "data": "hello"}
    assert logger._num_blocks == 1  # noqa: SLF001


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (logging_level, expected)
        for logging_level, expected in [
            (40, "error"),  # logging.ERROR
            (30, "warning"),  # logging.WARNING
            (20, "log"),  # logging.INFO
            (10, "log"),  # logging.DEBUG
        ]
    ],
)
def test_get_log_type(mock_blob_service, mock_credential, level, expected):
    """Test that log levels map to the correct log type string."""
    logger = _make_logger()

    assert logger._get_log_type(level) == expected  # noqa: SLF001
