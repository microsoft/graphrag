# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Logging utilities and implementations."""

from .console import ConsoleLogger  # noqa: I001
from .load_progress_logger import load_progress_logger
from .null_progress import NullProgressLogger
from .print_progress import PrintProgressLogger
from .rich_progress import RichProgressLogger
from .types import (
    ProgressLogger,
    LoggerType,
    StatusLogger,
)

# must import callbacks after ProgressLogger to prevent circular import
from .load_pipeline_logger import load_pipeline_logger
from .callbacks import (
    BlobWorkflowCallbacks,
    ConsoleWorkflowCallbacks,
    FileWorkflowCallbacks,
    ProgressWorkflowCallbacks,
)

__all__ = [  # noqa: RUF022
    # Progress Reporters
    "ConsoleLogger",
    "NullProgressLogger",
    "PrintProgressLogger",
    "ProgressLogger",
    "LoggerType",
    "RichProgressLogger",
    "StatusLogger",
    "load_progress_logger",
    # Callback reporters
    "BlobWorkflowCallbacks",
    "ConsoleWorkflowCallbacks",
    "FileWorkflowCallbacks",
    "ProgressWorkflowCallbacks",
    "load_pipeline_logger",
]
