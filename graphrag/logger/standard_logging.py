# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Standard logging configuration for the graphrag package.

This module provides a standardized way to configure Python's built-in
logging system for use within the graphrag package.

Usage:
    # Configuration should be done once at the start of your application:
    from graphrag.logger.standard_logging import configure_logging
    configure_logging(log_level="INFO", log_file="/path/to/app.log")

    # Then throughout your code:
    from graphrag.logger.standard_logging import get_logger
    logger = get_logger(__name__)  # Typically pass __name__ to get module-specific logger

    # Use standard logging methods:
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical error message")

Notes
-----
    The logging system is hierarchical. Loggers are organized in a tree structure,
    with the root logger named 'graphrag'. All loggers created by get_logger() will
    be children of this root logger. This allows for consistent configuration of all
    graphrag-related logs throughout the application.

    All progress logging now uses this standard logging system for consistency.
"""

import logging
import sys
from pathlib import Path


def configure_logging(
    log_level: int | str = logging.INFO,
    log_file: str | Path | None = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    date_format: str = "%Y-%m-%d %H:%M:%S",
) -> None:
    """Configure the Python logging module for graphrag.

    This function sets up a root logger for the 'graphrag' package
    with handlers for console output and optionally file output.

    Parameters
    ----------
    log_level : Union[int, str], default=logging.INFO
        The logging level to use. Can be a string or integer.
    log_file : Optional[Union[str, Path]], default=None
        Path to a log file. If None, logs will only go to console.
    log_format : str, default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        The format for log messages.
    date_format : str, default="%Y-%m-%d %H:%M:%S"
        The format for dates in the log messages.
    """
    # Convert string log level to numeric value if needed
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)

    # Get the root logger for graphrag
    logger = logging.getLogger("graphrag")
    logger.setLevel(log_level)

    # Clear any existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger to avoid duplicate logging
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    This function returns a logger that is a child of the 'graphrag' logger.

    Parameters
    ----------
    name : str
        The name of the logger, usually __name__

    Returns
    -------
    logging.Logger
        A logger instance
    """
    # Ensure the name has 'graphrag' prefix for proper hierarchy
    if not name.startswith("graphrag.") and name != "graphrag":
        if name == "__main__":
            name = "graphrag.main"
        else:
            name = f"graphrag.{name}"

    return logging.getLogger(name)
