# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for standard logging functionality."""

import logging
import tempfile
from pathlib import Path

from graphrag.logger.standard_logging import DEFAULT_LOG_FILENAME, init_loggers
from tests.unit.config.utils import get_default_graphrag_config


def test_standard_logging():
    """Test that standard logging works."""
    logger = logging.getLogger("graphrag.test")
    assert logger.name == "graphrag.test"


def test_logger_hierarchy():
    """Test that logger hierarchy works correctly."""
    # reset logging to default state using init_loggers
    config = get_default_graphrag_config()
    init_loggers(config)

    root_logger = logging.getLogger("graphrag")
    child_logger = logging.getLogger("graphrag.child")

    # setting level on root should affect children
    root_logger.setLevel(logging.ERROR)
    assert child_logger.getEffectiveLevel() == logging.ERROR

    # clean up after test
    root_logger.handlers.clear()


def test_init_loggers_file_config():
    """Test that init_loggers works with file configuration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = get_default_graphrag_config(root_dir=temp_dir)

        # call init_loggers with file config
        init_loggers(config=config)

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
        log_file = Path(temp_dir) / "logs" / DEFAULT_LOG_FILENAME
        assert log_file.exists()

        with open(log_file) as f:
            content = f.read()
            assert test_message in content

        # clean up
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        logger.handlers.clear()


def test_init_loggers_file_verbose():
    """Test that init_loggers works with verbose flag."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = get_default_graphrag_config(root_dir=temp_dir)

        # call init_loggers with file config
        init_loggers(config=config, verbose=True)

        logger = logging.getLogger("graphrag")

        # test that logging works
        test_message = "Test init_loggers file message"
        logger.debug(test_message)

        # check that the log file was created
        log_file = Path(temp_dir) / "logs" / DEFAULT_LOG_FILENAME

        with open(log_file) as f:
            content = f.read()
            assert test_message in content

        # clean up
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        logger.handlers.clear()


def test_init_loggers_custom_filename():
    """Test that init_loggers works with custom filename."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = get_default_graphrag_config(root_dir=temp_dir)

        # call init_loggers with file config
        init_loggers(config=config, filename="custom-log.log")

        logger = logging.getLogger("graphrag")

        # check that the log file was created
        log_file = Path(temp_dir) / "logs" / "custom-log.log"
        assert log_file.exists()

        # clean up
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        logger.handlers.clear()
