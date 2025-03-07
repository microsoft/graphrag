# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Logging utilities. A unified way for enabling logging."""

import logging
from pathlib import Path

from graphrag.config.enums import ReportingType
from graphrag.config.models.graph_rag_config import GraphRagConfig


def enable_logging(log_filepath: str | Path, verbose: bool = False) -> None:
    """Enable logging to a file.

    Parameters
    ----------
    log_filepath : str | Path
        The path to the log file.
    verbose : bool, default=False
        Whether to log debug messages.
    """
    log_filepath = Path(log_filepath)
    log_filepath.parent.mkdir(parents=True, exist_ok=True)
    log_filepath.touch(exist_ok=True)

    logging.basicConfig(
        filename=log_filepath,
        filemode="a",
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG if verbose else logging.INFO,
    )


def enable_logging_with_config(
    config: GraphRagConfig, verbose: bool = False, filename: str = "indexing-engine.log"
) -> tuple[bool, str]:
    """Enable logging to a file based on the config.

    Parameters
    ----------
    config : GraphRagConfig
        The configuration.
    timestamp_value : str
        The timestamp value representing the directory to place the log files.
    verbose : bool, default=False
        Whether to log debug messages.

    Returns
    -------
    tuple[bool, str]
        A tuple of a boolean indicating if logging was enabled and the path to the log file.
        (False, "") if logging was not enabled.
        (True, str) if logging was enabled.
    """
    if config.reporting.type == ReportingType.file:
        log_path = Path(config.reporting.base_dir) / filename
        enable_logging(log_path, verbose)
        return (True, str(log_path))
    return (False, "")
