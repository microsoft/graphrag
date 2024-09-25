# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Load a progress reporter."""

from .null_progress import NullProgressLogger
from .print_progress import PrintProgressLogger
from .rich_progress import RichProgressLogger
from .types import (
    LoggerType,
    ProgressLogger,
)


def load_progress_logger(
    reporter_type: LoggerType = LoggerType.NONE,
) -> ProgressLogger:
    """Load a progress reporter.

    Parameters
    ----------
    reporter_type : {"rich", "print", "none"}, default=rich
        The type of progress reporter to load.

    Returns
    -------
    ProgressLogger
    """
    match reporter_type:
        case LoggerType.RICH:
            return RichProgressLogger("GraphRAG Indexer ")
        case LoggerType.PRINT:
            return PrintProgressLogger("GraphRAG Indexer ")
        case LoggerType.NONE:
            return NullProgressLogger()
        case _:
            msg = f"Invalid progress reporter type: {reporter_type}"
            raise ValueError(msg)
