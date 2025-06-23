# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Standard logging configuration for the graphrag package.

This module provides a standardized way to configure Python's built-in
logging system for use within the graphrag package.

Usage:
    # Configuration should be done once at the start of your application:
    from graphrag.logger.standard_logging import init_loggers
    init_loggers(log_file="/path/to/app.log")

    # Then throughout your code:
    import logging
    logger = logging.getLogger(__name__)  # Use standard logging

    # Use standard logging methods:
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical error message")

Notes
-----
    The logging system is hierarchical. Loggers are organized in a tree structure,
    with the root logger named 'graphrag'. All loggers created with names starting
    with 'graphrag.' will be children of this root logger. This allows for consistent
    configuration of all graphrag-related logs throughout the application.

    All progress logging now uses this standard logging system for consistency.
"""

import logging
import sys
from pathlib import Path

from graphrag.config.enums import ReportingType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.models.reporting_config import ReportingConfig

LOG_FORMAT = "%(asctime)s.%(msecs)04d - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def init_loggers(
    config: GraphRagConfig | None = None,
    root_dir: str | None = None,
    verbose: bool = False,
    log_file: str | Path | None = None,
) -> None:
    """Initialize logging handlers for graphrag based on configuration.

    This function merges the functionality of configure_logging() and create_pipeline_logger()
    to provide a unified way to set up logging for the graphrag package.

    Parameters
    ----------
    config : GraphRagConfig | None, default=None
        The GraphRAG configuration. If None, defaults to file-based reporting.
    root_dir : str | None, default=None
        The root directory for file-based logging.
    verbose : bool, default=False
        Whether to enable verbose (DEBUG) logging.
    log_file : Optional[Union[str, Path]], default=None
        Path to a specific log file. If provided, takes precedence over config.
    """
    # import BlobWorkflowLogger here to avoid circular imports
    from graphrag.logger.blob_workflow_logger import BlobWorkflowLogger

    # extract reporting config from GraphRagConfig if provided
    reporting_config: ReportingConfig
    if log_file:
        # if log_file is provided directly, override config to use file-based logging
        log_path = Path(log_file)
        reporting_config = ReportingConfig(
            type=ReportingType.file,
            base_dir=str(log_path.parent),
        )
    elif config is not None:
        # use the reporting configuration from GraphRagConfig
        reporting_config = config.reporting
    else:
        # default to file-based logging if no config provided
        reporting_config = ReportingConfig(base_dir="logs", type=ReportingType.file)

    logger = logging.getLogger("graphrag")
    log_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(log_level)

    # clear any existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        # Close file handlers properly before removing them
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        logger.handlers.clear()

    # create formatter with custom format
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    init_console_logger(verbose)

    # add more handlers based on configuration
    handler: logging.Handler
    match reporting_config.type:
        case ReportingType.file:
            if log_file:
                # use the specific log file provided
                log_file_path = Path(log_file)
                log_file_path.parent.mkdir(parents=True, exist_ok=True)
                handler = logging.FileHandler(str(log_file_path), mode="a")
            else:
                # use the config-based file path
                log_dir = Path(root_dir or "") / (reporting_config.base_dir or "")
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file_path = log_dir / "logs.txt"
                handler = logging.FileHandler(str(log_file_path), mode="a")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        case ReportingType.blob:
            handler = BlobWorkflowLogger(
                reporting_config.connection_string,
                reporting_config.container_name,
                base_dir=reporting_config.base_dir,
                storage_account_blob_url=reporting_config.storage_account_blob_url,
            )
            logger.addHandler(handler)
        case _:
            logger.error("Unknown reporting type '%s'.", reporting_config.type)


def init_console_logger(verbose: bool = False) -> None:
    """Initialize a console logger if not already present.

    This function sets up a logger that outputs log messages to STDOUT.

    Parameters
    ----------
    verbose : bool, default=False
        Whether to enable verbose (DEBUG) logging.
    """
    logger = logging.getLogger("graphrag")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    has_console_handler = any(
        isinstance(h, logging.StreamHandler) for h in logger.handlers
    )
    if not has_console_handler:
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
