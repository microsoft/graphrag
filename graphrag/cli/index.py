# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of index subcommand."""

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
from graphrag.index.emit.types import TableEmitterType
from graphrag.index.validate_config import validate_config_names
from graphrag.logging.base import ProgressReporter
from graphrag.logging.factories import create_progress_reporter
from graphrag.logging.types import ReporterType
from graphrag.utils.cli import redact

# Ignore warnings from numba
warnings.filterwarnings("ignore", message=".*NumbaDeprecationWarning.*")

log = logging.getLogger(__name__)


def _logger(reporter: ProgressReporter):
    def info(msg: str, verbose: bool = False):
        log.info(msg)
        if verbose:
            reporter.info(msg)

    def error(msg: str, verbose: bool = False):
        log.error(msg)
        if verbose:
            reporter.error(msg)

    def success(msg: str, verbose: bool = False):
        log.info(msg)
        if verbose:
            reporter.success(msg)

    return info, error, success


def _register_signal_handlers(reporter: ProgressReporter):
    import signal

    def handle_signal(signum, _):
        # Handle the signal here
        reporter.info(f"Received signal {signum}, exiting...")
        reporter.dispose()
        for task in asyncio.all_tasks():
            task.cancel()
        reporter.info("All tasks cancelled. Exiting...")

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
    reporter: ReporterType,
    config_filepath: Path | None,
    emit: list[TableEmitterType],
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
        reporter=reporter,
        emit=emit,
        dry_run=dry_run,
        skip_validation=skip_validation,
        output_dir=output_dir,
    )


def update_cli(
    root_dir: Path,
    verbose: bool,
    memprofile: bool,
    cache: bool,
    reporter: ReporterType,
    config_filepath: Path | None,
    emit: list[TableEmitterType],
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
        reporter=reporter,
        emit=emit,
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
    reporter,
    emit,
    dry_run,
    skip_validation,
    output_dir,
):
    progress_reporter = create_progress_reporter(reporter)
    info, error, success = _logger(progress_reporter)
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
        validate_config_names(progress_reporter, config)

    info(f"Starting pipeline run for: {run_id}, {dry_run=}", verbose)
    info(
        f"Using default configuration: {redact(config.model_dump())}",
        verbose,
    )

    if dry_run:
        info("Dry run complete, exiting...", True)
        sys.exit(0)

    _register_signal_handlers(progress_reporter)

    outputs = asyncio.run(
        api.build_index(
            config=config,
            run_id=run_id,
            is_resume_run=bool(resume),
            memory_profile=memprofile,
            progress_reporter=progress_reporter,
            emit=emit,
        )
    )
    encountered_errors = any(
        output.errors and len(output.errors) > 0 for output in outputs
    )

    progress_reporter.stop()
    if encountered_errors:
        error(
            "Errors occurred during the pipeline run, see logs for more details.", True
        )
    else:
        success("All workflows completed successfully.", True)

    sys.exit(1 if encountered_errors else 0)
