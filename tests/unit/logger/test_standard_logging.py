# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for standard logging functionality."""

import logging
import tempfile
from pathlib import Path

from graphrag.logger.standard_logging import configure_logging, get_logger


def test_logger_name_formatting():
    """Test the logger name gets formatted correctly."""
    assert get_logger("test").name == "graphrag.test"
    assert get_logger("graphrag.test").name == "graphrag.test"
    assert get_logger("__main__").name == "graphrag.main"


def test_file_logging():
    """Test that logging to a file works."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "test.log"

        # Configure logging to file
        configure_logging(log_file=log_file)

        # Get a logger and log some messages
        logger = get_logger("test")
        test_message = "Test file logging message"
        logger.info(test_message)

        # Check that the log file exists and contains our message
        assert log_file.exists()
        with open(log_file) as f:
            content = f.read()
            assert test_message in content


def test_logger_hierarchy():
    """Test that logger hierarchy works correctly."""
    # Reset logging to default state
    configure_logging()

    root_logger = get_logger("graphrag")
    child_logger = get_logger("graphrag.child")

    # Setting level on root should affect children
    root_logger.setLevel(logging.ERROR)
    assert child_logger.getEffectiveLevel() == logging.ERROR
