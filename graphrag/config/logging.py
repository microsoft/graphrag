# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Logging utilities. A unified way for enabling logging."""

import logging
from pathlib import Path

from graphrag.config.enums import ReportingType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.logger.standard_logging import init_loggers


def enable_logging(log_filepath: str | Path, verbose: bool = False) -> None:
    """Enable logging to a file.

    Parameters
    ----------
    log_filepath : str | Path
        The path to the log file.
    verbose : bool, default=False
        Whether to log debug messages.
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    # Use init_loggers with the specific log file and custom formatting
    init_loggers(
        log_level=log_level,
        log_file=log_filepath,
        log_format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        date_format="%H:%M:%S",
        enable_console=False,
    )


def enable_logging_with_config(
    config: GraphRagConfig, verbose: bool = False, filename: str = "indexing-engine.log"
) -> tuple[bool, str]:
    """Enable logging to a file based on the config.

    Parameters
    ----------
    config : GraphRagConfig
        The configuration.
    verbose : bool, default=False
        Whether to log debug messages.
    filename : str, default="indexing-engine.log"
        The name of the log file.

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
