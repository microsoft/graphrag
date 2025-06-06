# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for standard logging functionality."""

import logging
import tempfile
from pathlib import Path

from graphrag.config.enums import ReportingType
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

        # configure logging to file using init_loggers
        init_loggers(log_file=log_file)

        # get a logger and log some messages
        logger = logging.getLogger("graphrag.test")
        test_message = "Test file logging message"
        logger.info(test_message)

        # check that the log file exists and contains our message
        assert log_file.exists()
        with open(log_file) as f:
            content = f.read()
            assert test_message in content

        # close all file handlers to ensure proper cleanup on Windows
        graphrag_logger = logging.getLogger("graphrag")
        for handler in graphrag_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                graphrag_logger.removeHandler(handler)


def test_logger_hierarchy():
    """Test that logger hierarchy works correctly."""
    # reset logging to default state using init_loggers
    init_loggers()

    root_logger = logging.getLogger("graphrag")
    child_logger = logging.getLogger("graphrag.child")

    # setting level on root should affect children
    root_logger.setLevel(logging.ERROR)
    assert child_logger.getEffectiveLevel() == logging.ERROR

    # clean up after test
    root_logger.handlers.clear()


def test_init_loggers_console_enabled():
    """Test that init_loggers works with console handler."""
    init_loggers()

    logger = logging.getLogger("graphrag")

    # should have both a console handler and a file handler (default config)
    console_handlers = [
        h
        for h in logger.handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
    ]
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(console_handlers) > 0
    assert len(file_handlers) > 0  # Due to default file config

    # clean up
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
    logger.handlers.clear()


def test_init_loggers_default_config():
    """Test that init_loggers uses default file config when none provided."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # call init_loggers with no config (should default to file logging)
        init_loggers(root_dir=temp_dir)

        logger = logging.getLogger("graphrag")

        # Should have a file handler due to default config
        file_handlers = [
            h for h in logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) > 0

        # test that logging works
        test_message = "Test default config message"
        logger.info(test_message)

        # check that the log file was created with default structure
        log_file = Path(temp_dir) / "logs" / "logs.txt"
        assert log_file.exists()

        with open(log_file) as f:
            content = f.read()
            assert test_message in content

        # clean up
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        logger.handlers.clear()


def test_init_loggers_file_config():
    """Test that init_loggers works with file configuration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = get_default_graphrag_config(root_dir=temp_dir)
        config.reporting = ReportingConfig(type=ReportingType.file, base_dir="logs")

        # call init_loggers with file config
        init_loggers(config=config, root_dir=temp_dir)

        logger = logging.getLogger("graphrag")

        # should have a file handler
        file_handlers = [
            h for h in logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) > 0

        # test that logging works
        test_message = "Test init_loggers file message"
        logger.info(test_message)

        # check that the log file was created
        log_file = Path(temp_dir) / "logs" / "logs.txt"
        assert log_file.exists()

        with open(log_file) as f:
            content = f.read()
            assert test_message in content

        # clean up
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        logger.handlers.clear()


def test_init_loggers_console_config():
    """Test that init_loggers works with console configuration."""
    config = get_default_graphrag_config()

    # call init_loggers with config
    init_loggers(config=config)

    logger = logging.getLogger("graphrag")

    # should have a console handler from the config
    console_handlers = [
        h
        for h in logger.handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
    ]
    assert len(console_handlers) > 0

    # clean up
    logger.handlers.clear()


def test_init_loggers_both_console():
    """Test that init_loggers doesn't duplicate console handlers."""
    config = get_default_graphrag_config()

    # call init_loggers with config
    init_loggers(config=config)

    logger = logging.getLogger("graphrag")

    # should have only one console handler (no duplicates)
    console_handlers = [
        h
        for h in logger.handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
    ]
    assert len(console_handlers) == 1

    # clean up
    logger.handlers.clear()
