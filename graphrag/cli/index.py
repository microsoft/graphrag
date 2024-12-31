# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of the index subcommand."""

import asyncio
import logging
import sys
import time
import warnings
from pathlib import Path

import graphrag.api as api
from graphrag.config.enums import CacheType
from graphrag.config.load_config import load_config
from graphrag.config.logging import enable_logging_with_config
from graphrag.config.resolve_path import resolve_paths
from graphrag.index.validate_config import validate_config_names
from graphrag.logger.base import ProgressLogger
from graphrag.logger.factory import LoggerFactory, LoggerType
from graphrag.utils.cli import redact

# Ignore warnings from numba
warnings.filterwarnings("ignore", message=".*NumbaDeprecationWarning.*")

log = logging.getLogger(__name__)


def _logger(logger: ProgressLogger):
    def info(msg: str, verbose: bool = False):
        log.info(msg)
        if verbose:
            logger.info(msg)

    def error(msg: str, verbose: bool = False):
        log.error(msg)
        if verbose:
            logger.error(msg)

    def success(msg: str, verbose: bool = False):
        log.info(msg)
        if verbose:
            logger.success(msg)

    return info, error, success


def _register_signal_handlers(logger: ProgressLogger):
    import signal

    def handle_signal(signum, _):
        # Handle the signal here
        logger.info(f"Received signal {signum}, exiting...")  # noqa: G004
        logger.dispose()
        for task in asyncio.all_tasks():
            task.cancel()
        logger.info("All tasks cancelled. Exiting...")

    # Register signal handlers for SIGINT and SIGHUP
    signal.signal(signal.SIGINT, handle_signal)

    if sys.platform != "win32":
        signal.signal(signal.SIGHUP, handle_signal)


def index_cli(
    root_dir: Path,
    verbose: bool,
    resume: str | None,
    memprofile: bool,
    cache: bool,
    logger: LoggerType,
    config_filepath: Path | None,
    dry_run: bool,
    skip_validation: bool,
    output_dir: Path | None,
):
    """Run the pipeline with the given config."""
    config = load_config(root_dir, config_filepath)

    _run_index(
        config=config,
        verbose=verbose,
        resume=resume,
        memprofile=memprofile,
        cache=cache,
        logger=logger,
        dry_run=dry_run,
        skip_validation=skip_validation,
        output_dir=output_dir,
    )


def update_cli(
    root_dir: Path,
    verbose: bool,
    memprofile: bool,
    cache: bool,
    logger: LoggerType,
    config_filepath: Path | None,
    skip_validation: bool,
    output_dir: Path | None,
):
    """Run the pipeline with the given config."""
    config = load_config(root_dir, config_filepath)

    # Check if update storage exist, if not configure it with default values
    if not config.update_index_storage:
        from graphrag.config.defaults import STORAGE_TYPE, UPDATE_STORAGE_BASE_DIR
        from graphrag.config.models.storage_config import StorageConfig

        config.update_index_storage = StorageConfig(
            type=STORAGE_TYPE,
            base_dir=UPDATE_STORAGE_BASE_DIR,
        )

    _run_index(
        config=config,
        verbose=verbose,
        resume=False,
        memprofile=memprofile,
        cache=cache,
        logger=logger,
        dry_run=False,
        skip_validation=skip_validation,
        output_dir=output_dir,
    )


def _run_index(
    config,
    verbose,
    resume,
    memprofile,
    cache,
    logger,
    dry_run,
    skip_validation,
    output_dir,
):
    progress_logger = LoggerFactory().create_logger(logger)
    info, error, success = _logger(progress_logger)
    run_id = resume or time.strftime("%Y%m%d-%H%M%S")

    config.storage.base_dir = str(output_dir) if output_dir else config.storage.base_dir
    config.reporting.base_dir = (
        str(output_dir) if output_dir else config.reporting.base_dir
    )
    resolve_paths(config, run_id)

    if not cache:
        config.cache.type = CacheType.none

    enabled_logging, log_path = enable_logging_with_config(config, verbose)
    if enabled_logging:
        info(f"Logging enabled at {log_path}", True)
    else:
        info(
            f"Logging not enabled for config {redact(config.model_dump())}",
            True,
        )

    if skip_validation:
        validate_config_names(progress_logger, config)

    info(f"Starting pipeline run for: {run_id}, {dry_run=}", verbose)
    info(
        f"Using default configuration: {redact(config.model_dump())}",
        verbose,
    )

    if dry_run:
        info("Dry run complete, exiting...", True)
        sys.exit(0)

    _register_signal_handlers(progress_logger)

    outputs = asyncio.run(
        api.build_index(
            config=config,
            run_id=run_id,
            is_resume_run=bool(resume),
            memory_profile=memprofile,
            progress_logger=progress_logger,
        )
    )
    encountered_errors = any(
        output.errors and len(output.errors) > 0 for output in outputs
    )

    progress_logger.stop()
    if encountered_errors:
        error(
            "Errors occurred during the pipeline run, see logs for more details.", True
        )
    else:
        success("All workflows completed successfully.", True)

    sys.exit(1 if encountered_errors else 0)
