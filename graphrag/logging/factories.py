# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating loggers."""

from graphrag.logging.base import ProgressReporter
from graphrag.logging.null_progress import NullProgressReporter
from graphrag.logging.print_progress import PrintProgressReporter
from graphrag.logging.rich_progress import RichProgressReporter
from graphrag.logging.types import ReporterType


def create_progress_reporter(
    reporter_type: ReporterType = ReporterType.NONE,
) -> ProgressReporter:
    """Load a progress reporter.

    Parameters
    ----------
    reporter_type : {"rich", "print", "none"}, default=rich
        The type of progress reporter to load.

    Returns
    -------
    ProgressReporter
    """
    match reporter_type:
        case ReporterType.RICH:
            return RichProgressReporter("GraphRAG Indexer ")
        case ReporterType.PRINT:
            return PrintProgressReporter("GraphRAG Indexer ")
        case ReporterType.NONE:
            return NullProgressReporter()
        case _:
            msg = f"Invalid progress reporter type: {reporter_type}"
            raise ValueError(msg)
