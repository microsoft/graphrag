# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for standard logging functionality."""

import logging
import tempfile
from pathlib import Path

from graphrag.logger.standard_logging import configure_logging


def test_standard_logging():
    """Test that standard logging works."""
    logger = logging.getLogger("graphrag.test")
    assert logger.name == "graphrag.test"


def test_file_logging():
    """Test that logging to a file works."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "test.log"

        # Configure logging to file
        configure_logging(log_file=log_file)

        # Get a logger and log some messages
        logger = logging.getLogger("graphrag.test")
        test_message = "Test file logging message"
        logger.info(test_message)

        # Check that the log file exists and contains our message
        assert log_file.exists()
        with open(log_file) as f:
            content = f.read()
            assert test_message in content

        # Close all file handlers to ensure proper cleanup on Windows
        graphrag_logger = logging.getLogger("graphrag")
        for handler in graphrag_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                graphrag_logger.removeHandler(handler)


def test_logger_hierarchy():
    """Test that logger hierarchy works correctly."""
    # Reset logging to default state
    configure_logging()

    root_logger = logging.getLogger("graphrag")
    child_logger = logging.getLogger("graphrag.child")

    # Setting level on root should affect children
    root_logger.setLevel(logging.ERROR)
    assert child_logger.getEffectiveLevel() == logging.ERROR

    # Clean up after test
    root_logger.handlers.clear()
