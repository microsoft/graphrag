# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""LoggerFactory Tests.

These tests will test the LoggerFactory class and the creation of each reporting type that is natively supported.
"""

import logging

import pytest

from graphrag.config.enums import ReportingType
from graphrag.logger.blob_workflow_logger import BlobWorkflowLogger
from graphrag.logger.factory import LoggerFactory

# cspell:disable-next-line well-known-key
WELL_KNOWN_BLOB_STORAGE_KEY = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
# cspell:disable-next-line well-known-key
WELL_KNOWN_COSMOS_CONNECTION_STRING = "AccountEndpoint=https://127.0.0.1:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="


@pytest.mark.skip(reason="Blob storage emulator is not available in this environment")
def test_create_blob_logger():
    kwargs = {
        "type": "blob",
        "connection_string": WELL_KNOWN_BLOB_STORAGE_KEY,
        "base_dir": "testbasedir",
        "container_name": "testcontainer",
    }
    logger = LoggerFactory.create_logger(ReportingType.blob.value, kwargs)
    assert isinstance(logger, BlobWorkflowLogger)


def test_register_and_create_custom_logger():
    """Test registering and creating a custom logger type."""
    from unittest.mock import MagicMock

    custom_logger_class = MagicMock(spec=logging.Handler)
    instance = MagicMock()
    instance.initialized = True
    custom_logger_class.return_value = instance

    LoggerFactory.register("custom", lambda **kwargs: custom_logger_class(**kwargs))
    logger = LoggerFactory.create_logger("custom", {})

    assert custom_logger_class.called
    assert logger is instance
    # Access the attribute we set on our mock
    assert logger.initialized is True  # type: ignore # Attribute only exists on our mock

    # Check if it's in the list of registered logger types
    assert "custom" in LoggerFactory.get_logger_types()
    assert LoggerFactory.is_supported_type("custom")


def test_get_logger_types():
    logger_types = LoggerFactory.get_logger_types()
    # Check that built-in types are registered
    assert ReportingType.file.value in logger_types
    assert ReportingType.blob.value in logger_types


def test_create_unknown_logger():
    with pytest.raises(ValueError, match="Unknown reporting type: unknown"):
        LoggerFactory.create_logger("unknown", {})
