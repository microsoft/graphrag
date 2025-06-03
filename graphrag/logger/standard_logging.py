# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Standard logging configuration for the graphrag package.

This module provides a standardized way to configure Python's built-in
logging system for use within the graphrag package.

Usage:
    # Configuration should be done once at the start of your application:
    from graphrag.logger.standard_logging import init_loggers
    init_loggers(log_level="INFO", log_file="/path/to/app.log")

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


def init_loggers(
    config: ReportingConfig | None = None,
    root_dir: str | None = None,
    log_level: int | str = logging.INFO,
    enable_console: bool = False,
    log_file: str | Path | None = None,
    log_format: str = "%(asctime)s.%(msecs)04d - %(levelname)s - %(name)s - %(message)s",
    date_format: str = "%Y-%m-%d %H:%M:%S",
) -> None:
    """Initialize logging handlers for graphrag based on configuration.

    This function merges the functionality of configure_logging and create_pipeline_logger
    to provide a unified way to set up logging for the graphrag package.

    Parameters
    ----------
    config : ReportingConfig | None, default=None
        The reporting configuration. If None, defaults to file-based reporting.
    root_dir : str | None, default=None
        The root directory for file-based logging.
    log_level : Union[int, str], default=logging.INFO
        The logging level to use. Can be a string or integer.
    enable_console : bool, default=False
        Whether to add a console handler. Should be True only when called from CLI.
    log_file : Optional[Union[str, Path]], default=None
        Path to a specific log file. If provided, takes precedence over config.
    log_format : str, default="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        The format for log messages.
    date_format : str, default="%Y-%m-%d %H:%M:%S"
        The format for dates in the log messages.
    """
    # Import BlobWorkflowLogger here to avoid circular imports
    from graphrag.logger.blob_workflow_logger import BlobWorkflowLogger

    # If log_file is provided directly, override config to use file-based logging
    if log_file:
        log_path = Path(log_file)
        config = ReportingConfig(
            type=ReportingType.file,
            base_dir=str(log_path.parent),
        )
    elif config is None:
        # Default to file-based logging if no config provided (maintains backward compatibility)
        config = ReportingConfig(base_dir="logs", type=ReportingType.file)

    # Convert string log level to numeric value if needed
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)

    # Get the root logger for graphrag
    logger = logging.getLogger("graphrag")
    logger.setLevel(log_level)

    # Clear any existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        # Close file handlers properly before removing them
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        logger.handlers.clear()

    # Create formatter with custom format
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    # Add console handler if requested (typically for CLI usage)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add handlers based on configuration
    handler: logging.Handler
    match config.type:
        case ReportingType.file:
            if log_file:
                # Use the specific log file provided
                log_file_path = Path(log_file)
                log_file_path.parent.mkdir(parents=True, exist_ok=True)
                handler = logging.FileHandler(str(log_file_path), mode="a")
            else:
                # Use the config-based file path
                log_dir = Path(root_dir or "") / (config.base_dir or "")
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file_path = log_dir / "logs.txt"
                handler = logging.FileHandler(str(log_file_path), mode="a")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        case ReportingType.console:
            # Only add console handler if not already added
            if not enable_console:
                handler = logging.StreamHandler(sys.stdout)
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        case ReportingType.blob:
            handler = BlobWorkflowLogger(
                config.connection_string,
                config.container_name,
                base_dir=config.base_dir,
                storage_account_blob_url=config.storage_account_blob_url,
            )
            logger.addHandler(handler)

    # Prevent propagation to root logger to avoid duplicate logging
    logger.propagate = False
