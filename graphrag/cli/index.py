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
from graphrag.config import (
    CacheType,
    enable_logging_with_config,
    load_config,
    resolve_paths,
)
from graphrag.index.emit.types import TableEmitterType
from graphrag.index.validate_config import validate_config_names
from graphrag.logging import ProgressReporter, ReporterType, create_progress_reporter
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
    update_index_id: str | None,
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
    progress_reporter = create_progress_reporter(reporter)
    info, error, success = _logger(progress_reporter)
    run_id = resume or update_index_id or time.strftime("%Y%m%d-%H%M%S")

    config = load_config(root_dir, config_filepath)
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
            is_update_run=bool(update_index_id),
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
