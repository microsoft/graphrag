# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Logging utilities. A unified way for enabling logging."""

import logging
from pathlib import Path
import re

from .enums import ReportingType
from .models.graph_rag_config import GraphRagConfig


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
    config: GraphRagConfig,
    log_name: str,
    verbose: bool = False
) -> tuple[bool, str]:
    """Enable logging to a file based on the config.

    Parameters
    ----------
    config : GraphRagConfig
        The configuration.
    log_name : str
        Name of the log engine, eg. 'indexing-engine', 'query-local-engine', 'query-global-engine'
    verbose : bool, default=False
        Whether to log debug messages.
    pattern_or_timestamp_value : re.Pattern[str] | str, default=re.compile(r"^\d{8}-\d{6}$")
        The pattern to use to match the timestamp directories or the timestamp value to use.
        If a string is provided, the path will be resolved with the given string value.
        Otherwise, the path will be resolved with the latest available timestamp directory
        that matches the given pattern.

    Returns
    -------
    tuple[bool, str]
        A tuple of a boolean indicating if logging was enabled and the path to the log file.
        (False, "") if logging was not enabled.
        (True, str) if logging was enabled.
    """
    if config.reporting.type == ReportingType.file:
        log_path = Path(config.reporting.base_dir) / f"{log_name}.log"
        enable_logging(log_path, verbose)
        return (True, str(log_path))
    return (False, "")
