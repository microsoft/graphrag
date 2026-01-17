# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating a logger."""

from __future__ import annotations

import logging
from pathlib import Path

from graphrag_common.factory import Factory

from graphrag.config.enums import ReportingType

LOG_FORMAT = "%(asctime)s.%(msecs)04d - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class LoggerFactory(Factory[logging.Handler]):
    """A factory class for logger implementations.

    Includes a method for users to register a custom logger implementation.

    Configuration arguments are passed to each logger implementation as kwargs
    for individual enforcement of required/optional arguments.

    Note that because we rely on the built-in Python logging architecture, this factory does not return an instance,
    it merely configures the logger to your specified storage location.
    """


# --- register built-in logger implementations ---
def create_file_logger(**kwargs) -> logging.Handler:
    """Create a file-based logger."""
    base_dir = kwargs["base_dir"]
    filename = kwargs["filename"]
    log_dir = Path(base_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / filename

    handler = logging.FileHandler(str(log_file_path), mode="a")

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
    handler.setFormatter(formatter)

    return handler


def create_blob_logger(**kwargs) -> logging.Handler:
    """Create a blob storage-based logger."""
    from graphrag.logger.blob_workflow_logger import BlobWorkflowLogger

    return BlobWorkflowLogger(
        connection_string=kwargs["connection_string"],
        container_name=kwargs["container_name"],
        base_dir=kwargs["base_dir"],
        account_url=kwargs["account_url"],
    )


# --- register built-in implementations ---
logger_factory = LoggerFactory()
logger_factory.register(ReportingType.file.value, create_file_logger)
logger_factory.register(ReportingType.blob.value, create_blob_logger)
