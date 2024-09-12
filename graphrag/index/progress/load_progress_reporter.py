# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Load a progress reporter."""

from .rich import RichProgressReporter
from .types import NullProgressReporter, PrintProgressReporter, ProgressReporter


def load_progress_reporter(reporter_type: str = "none") -> ProgressReporter:
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
        case "rich":
            return RichProgressReporter("GraphRAG Indexer ")
        case "print":
            return PrintProgressReporter("GraphRAG Indexer ")
        case "none":
            return NullProgressReporter()
        case _:
            msg = f"Invalid progress reporter type: {reporter_type}"
            raise ValueError(msg)
