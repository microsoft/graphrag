# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Command line interface for index module."""

import asyncio
import json
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

# Ignore warnings from numba
warnings.filterwarnings("ignore", message=".*NumbaDeprecationWarning.*")

log = logging.getLogger(__name__)


def _redact(input: dict) -> str:
    """Sanitize the config json."""

    # Redact any sensitive configuration
    def redact_dict(input: dict) -> dict:
        if not isinstance(input, dict):
            return input

        result = {}
        for key, value in input.items():
            if key in {
                "api_key",
                "connection_string",
                "container_name",
                "organization",
            }:
                if value is not None:
                    result[key] = "==== REDACTED ===="
            elif isinstance(value, dict):
                result[key] = redact_dict(value)
            elif isinstance(value, list):
                result[key] = [redact_dict(i) for i in value]
            else:
                result[key] = value
        return result

    redacted_dict = redact_dict(input)
    return json.dumps(redacted_dict, indent=4)


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
    root_dir: str,
    verbose: bool,
    resume: str,
    update_index_id: str | None,
    memprofile: bool,
    nocache: bool,
    reporter: ReporterType,
    config_filepath: str | None,
    emit: list[TableEmitterType],
    dryrun: bool,
    skip_validations: bool,
    output_dir: str | None,
):
    """Run the pipeline with the given config."""
    progress_reporter = create_progress_reporter(reporter)
    info, error, success = _logger(progress_reporter)
    run_id = resume or update_index_id or time.strftime("%Y%m%d-%H%M%S")

    root = Path(root_dir).resolve()
    config = load_config(root, config_filepath)

    config.storage.base_dir = output_dir or config.storage.base_dir
    config.reporting.base_dir = output_dir or config.reporting.base_dir
    resolve_paths(config, run_id)

    if nocache:
        config.cache.type = CacheType.none

    enabled_logging, log_path = enable_logging_with_config(config, verbose)
    if enabled_logging:
        info(f"Logging enabled at {log_path}", True)
    else:
        info(
            f"Logging not enabled for config {_redact(config.model_dump())}",
            True,
        )

    if skip_validations:
        validate_config_names(progress_reporter, config)

    info(f"Starting pipeline run for: {run_id}, {dryrun=}", verbose)
    info(
        f"Using default configuration: {_redact(config.model_dump())}",
        verbose,
    )

    if dryrun:
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
