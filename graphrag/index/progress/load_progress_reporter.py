# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Load a progress reporter."""

from .rich import RichProgressReporter
from .types import (
    NullProgressReporter,
    PrintProgressReporter,
    ProgressReporter,
    ReporterType,
)


def load_progress_reporter(
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
