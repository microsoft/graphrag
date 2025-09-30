# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating a logger."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from graphrag.config.enums import ReportingType

if TYPE_CHECKING:
    from collections.abc import Callable

LOG_FORMAT = "%(asctime)s.%(msecs)04d - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class LoggerFactory:
    """A factory class for logger implementations.

    Includes a method for users to register a custom logger implementation.

    Configuration arguments are passed to each logger implementation as kwargs
    for individual enforcement of required/optional arguments.

    Note that because we rely on the built-in Python logging architecture, this factory does not return an instance,
    it merely configures the logger to your specified storage location.
    """

    _registry: ClassVar[dict[str, Callable[..., logging.Handler]]] = {}

    @classmethod
    def register(
        cls, reporting_type: str, creator: Callable[..., logging.Handler]
    ) -> None:
        """Register a custom logger implementation.

        Args:
            reporting_type: The type identifier for the logger.
            creator: A class or callable that initializes logging.
        """
        cls._registry[reporting_type] = creator

    @classmethod
    def create_logger(cls, reporting_type: str, kwargs: dict) -> logging.Handler:
        """Create a logger from the provided type.

        Args:
            reporting_type: The type of logger to create.
            logger: The logger instance for the application.
            kwargs: Additional keyword arguments for the constructor.

        Returns
        -------
            A logger instance.

        Raises
        ------
            ValueError: If the logger type is not registered.
        """
        if reporting_type not in cls._registry:
            msg = f"Unknown reporting type: {reporting_type}"
            raise ValueError(msg)

        return cls._registry[reporting_type](**kwargs)

    @classmethod
    def get_logger_types(cls) -> list[str]:
        """Get the registered logger implementations."""
        return list(cls._registry.keys())

    @classmethod
    def is_supported_type(cls, reporting_type: str) -> bool:
        """Check if the given logger type is supported."""
        return reporting_type in cls._registry


# --- register built-in logger implementations ---
def create_file_logger(**kwargs) -> logging.Handler:
    """Create a file-based logger."""
    root_dir = kwargs["root_dir"]
    base_dir = kwargs["base_dir"]
    filename = kwargs["filename"]
    log_dir = Path(root_dir) / base_dir
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
        storage_account_blob_url=kwargs["storage_account_blob_url"],
    )


# --- register built-in implementations ---
LoggerFactory.register(ReportingType.file.value, create_file_logger)
LoggerFactory.register(ReportingType.blob.value, create_blob_logger)
