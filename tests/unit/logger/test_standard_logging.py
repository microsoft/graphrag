# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for standard logging functionality."""

import logging
import tempfile
from pathlib import Path

from graphrag.config.enums import ReportingType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.models.reporting_config import ReportingConfig
from graphrag.logger.standard_logging import init_loggers
from tests.unit.config.utils import get_default_graphrag_config


def test_standard_logging():
    """Test that standard logging works."""
    logger = logging.getLogger("graphrag.test")
    assert logger.name == "graphrag.test"


def test_file_logging():
    """Test that logging to a file works."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "test.log"

        # Configure logging to file using init_loggers
        init_loggers(log_file=log_file)

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
    # Reset logging to default state using init_loggers
    init_loggers()

    root_logger = logging.getLogger("graphrag")
    child_logger = logging.getLogger("graphrag.child")

    # Setting level on root should affect children
    root_logger.setLevel(logging.ERROR)
    assert child_logger.getEffectiveLevel() == logging.ERROR

    # Clean up after test
    root_logger.handlers.clear()


def test_init_loggers_console_enabled():
    """Test that init_loggers works with console enabled."""
    # Call init_loggers with console enabled (CLI mode)
    init_loggers(enable_console=True, log_level="INFO")

    logger = logging.getLogger("graphrag")

    # Should have both a console handler and a file handler (default config)
    console_handlers = [
        h for h in logger.handlers if isinstance(h, logging.StreamHandler)
    ]
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(console_handlers) > 0
    assert len(file_handlers) > 0  # Due to default file config

    # Clean up
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
    logger.handlers.clear()


def test_init_loggers_default_config():
    """Test that init_loggers uses default file config when none provided."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Call init_loggers with no config (should default to file logging)
        init_loggers(root_dir=temp_dir, log_level="INFO")

        logger = logging.getLogger("graphrag")

        # Should have a file handler due to default config
        file_handlers = [
            h for h in logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) > 0

        # Test logging works
        test_message = "Test default config message"
        logger.info(test_message)

        # Check that the log file was created with default structure
        log_file = Path(temp_dir) / "logs" / "logs.txt"
        assert log_file.exists()

        with open(log_file) as f:
            content = f.read()
            assert test_message in content

        # Clean up
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        logger.handlers.clear()


def test_init_loggers_file_config():
    """Test that init_loggers works with file configuration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = get_default_graphrag_config(root_dir=temp_dir)
        config.reporting = ReportingConfig(type=ReportingType.file, base_dir="logs")

        # Call init_loggers with file config
        init_loggers(config=config, root_dir=temp_dir, log_level="INFO")

        logger = logging.getLogger("graphrag")

        # Should have a file handler
        file_handlers = [
            h for h in logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) > 0

        # Test logging works
        test_message = "Test init_loggers file message"
        logger.info(test_message)

        # Check that the log file was created
        log_file = Path(temp_dir) / "logs" / "logs.txt"
        assert log_file.exists()

        with open(log_file) as f:
            content = f.read()
            assert test_message in content

        # Clean up
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        logger.handlers.clear()


def test_init_loggers_console_config():
    """Test that init_loggers works with console configuration."""
    config = get_default_graphrag_config()
    config.reporting = ReportingConfig(type=ReportingType.console)

    # Call init_loggers with console config but no enable_console
    init_loggers(config=config, log_level="INFO", enable_console=False)

    logger = logging.getLogger("graphrag")

    # Should have a console handler from the config
    console_handlers = [
        h for h in logger.handlers if isinstance(h, logging.StreamHandler)
    ]
    assert len(console_handlers) > 0

    # Clean up
    logger.handlers.clear()


def test_init_loggers_both_console():
    """Test that init_loggers doesn't duplicate console handlers."""
    config = get_default_graphrag_config()
    config.reporting = ReportingConfig(type=ReportingType.console)

    # Call init_loggers with both console config and enable_console=True
    init_loggers(config=config, log_level="INFO", enable_console=True)

    logger = logging.getLogger("graphrag")

    # Should have only one console handler (no duplicates)
    console_handlers = [
        h for h in logger.handlers if isinstance(h, logging.StreamHandler)
    ]
    assert len(console_handlers) == 1

    # Clean up
    logger.handlers.clear()
