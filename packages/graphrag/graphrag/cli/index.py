# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of the index subcommand."""

import asyncio
import logging
import sys
import warnings
from pathlib import Path

from graphrag_cache.cache_type import CacheType

import graphrag.api as api
from graphrag.callbacks.console_workflow_callbacks import ConsoleWorkflowCallbacks
from graphrag.config.enums import IndexingMethod
from graphrag.config.load_config import load_config
from graphrag.index.validate_config import validate_config_names
from graphrag.utils.cli import redact

# Ignore warnings from numba
warnings.filterwarnings("ignore", message=".*NumbaDeprecationWarning.*")

logger = logging.getLogger(__name__)


def _register_signal_handlers():
    import signal

    def handle_signal(signum, _):
        # Handle the signal here
        logger.debug(f"Received signal {signum}, exiting...")  # noqa: G004
        for task in asyncio.all_tasks():
            task.cancel()
        logger.debug("All tasks cancelled. Exiting...")

    # Register signal handlers for SIGINT and SIGHUP
    signal.signal(signal.SIGINT, handle_signal)

    if sys.platform != "win32":
        signal.signal(signal.SIGHUP, handle_signal)


def index_cli(
    root_dir: Path,
    method: IndexingMethod,
    verbose: bool,
    cache: bool,
    dry_run: bool,
    skip_validation: bool,
):
    """Run the pipeline with the given config."""
    config = load_config(root_dir=root_dir)
    _run_index(
        config=config,
        method=method,
        is_update_run=False,
        verbose=verbose,
        cache=cache,
        dry_run=dry_run,
        skip_validation=skip_validation,
    )


def update_cli(
    root_dir: Path,
    method: IndexingMethod,
    verbose: bool,
    cache: bool,
    skip_validation: bool,
):
    """Run the pipeline with the given config."""
    config = load_config(
        root_dir=root_dir,
    )

    _run_index(
        config=config,
        method=method,
        is_update_run=True,
        verbose=verbose,
        cache=cache,
        dry_run=False,
        skip_validation=skip_validation,
    )


def _run_index(
    config,
    method,
    is_update_run,
    verbose,
    cache,
    dry_run,
    skip_validation,
):
    # Configure the root logger with the specified log level
    from graphrag.logger.standard_logging import init_loggers

    # Initialize loggers and reporting config
    init_loggers(
        config=config,
        verbose=verbose,
    )

    if not cache:
        config.cache.type = CacheType.Noop

    if not skip_validation:
        validate_config_names(config)

    logger.info("Starting pipeline run. %s", dry_run)
    logger.info(
        "Using default configuration: %s",
        redact(config.model_dump()),
    )

    if dry_run:
        logger.info("Dry run complete, exiting...", True)
        sys.exit(0)

    _register_signal_handlers()

    outputs = asyncio.run(
        api.build_index(
            config=config,
            method=method,
            is_update_run=is_update_run,
            callbacks=[ConsoleWorkflowCallbacks(verbose=verbose)],
            verbose=verbose,
        )
    )
    encountered_errors = any(output.error is not None for output in outputs)

    sys.exit(1 if encountered_errors else 0)
