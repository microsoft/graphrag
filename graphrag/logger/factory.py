# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating loggers."""

from typing import ClassVar

from graphrag.logger.base import ProgressLogger
from graphrag.logger.null_progress import NullProgressLogger
from graphrag.logger.print_progress import PrintProgressLogger
from graphrag.logger.rich_progress import RichProgressLogger
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
    ) -> ProgressLogger:
        """Create a logger based on the provided type."""
        if kwargs is None:
            kwargs = {}
        match logger_type:
            case LoggerType.RICH:
                return RichProgressLogger("GraphRAG Indexer ")
            case LoggerType.PRINT:
                return PrintProgressLogger("GraphRAG Indexer ")
            case LoggerType.NONE:
                return NullProgressLogger()
            case _:
                if logger_type in cls.logger_types:
                    return cls.logger_types[logger_type](**kwargs)
                # default to null logger if no other logger is found
                return NullProgressLogger()
