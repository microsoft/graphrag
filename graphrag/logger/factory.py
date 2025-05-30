# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating loggers."""

import logging
from typing import ClassVar

from graphrag.logger.standard_logging import get_logger
from graphrag.logger.types import LoggerType


class LoggerFactory:
    """A factory class for loggers."""

    logger_types: ClassVar[dict[str, type]] = {}

    @classmethod
    def register(cls, logger_type: str, logger: type):
        """Register a custom logger implementation."""
        cls.logger_types[logger_type] = logger

    @classmethod
    def create_logger(
        cls, logger_type: LoggerType | str, kwargs: dict | None = None
    ) -> logging.Logger:
        """Create a logger based on the provided type."""
        if kwargs is None:
            kwargs = {}

        # Check if a custom logger type was registered
        if isinstance(logger_type, str) and logger_type in cls.logger_types:
            logger_class = cls.logger_types[logger_type]
            return logger_class(**kwargs)

        # Return a standard Python logger
        # The visual differences (rich, print) are handled by the logging configuration
        logger_name = kwargs.get("name", "graphrag.progress")
        return get_logger(logger_name)
