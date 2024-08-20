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
    if reporter_type == "rich":
        return RichProgressReporter("GraphRAG Indexer ")
    if reporter_type == "print":
        return PrintProgressReporter("GraphRAG Indexer ")
    if reporter_type == "none":
        return NullProgressReporter()

    msg = f"Invalid progress reporter type: {reporter_type}"
    raise ValueError(msg)
