# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of the index subcommand."""

import asyncio
import logging
import sys
import warnings
from pathlib import Path

import graphrag.api as api
from graphrag.config.enums import CacheType, IndexingMethod, ReportingType
from graphrag.config.load_config import load_config
from graphrag.index.validate_config import validate_config_names
from graphrag.utils.cli import redact

# Ignore warnings from numba
warnings.filterwarnings("ignore", message=".*NumbaDeprecationWarning.*")

logger = logging.getLogger(__name__)


def _logger_helper(progress_logger: logging.Logger):
    def info(msg: str, verbose: bool = False):
        logger.info(msg)
        if verbose:
            progress_logger.info(msg)

    def error(msg: str, verbose: bool = False):
        logger.error(msg)
        if verbose:
            progress_logger.error(msg)

    def success(msg: str, verbose: bool = False):
        logger.info(msg)
        if verbose:
            progress_logger.info(msg)

    return info, error, success


def _register_signal_handlers(progress_logger: logging.Logger):
    import signal

    def handle_signal(signum, _):
        # Handle the signal here
        progress_logger.info(f"Received signal {signum}, exiting...")  # noqa: G004
        for task in asyncio.all_tasks():
            task.cancel()
        progress_logger.info("All tasks cancelled. Exiting...")

    # Register signal handlers for SIGINT and SIGHUP
    signal.signal(signal.SIGINT, handle_signal)

    if sys.platform != "win32":
        signal.signal(signal.SIGHUP, handle_signal)


def index_cli(
    root_dir: Path,
    method: IndexingMethod,
    verbose: bool,
    memprofile: bool,
    cache: bool,
    log_level: str,
    config_filepath: Path | None,
    dry_run: bool,
    skip_validation: bool,
    output_dir: Path | None,
):
    """Run the pipeline with the given config."""
    cli_overrides = {}
    if output_dir:
        cli_overrides["output.base_dir"] = str(output_dir)
        cli_overrides["reporting.base_dir"] = str(output_dir)
        cli_overrides["update_index_output.base_dir"] = str(output_dir)
    config = load_config(root_dir, config_filepath, cli_overrides)

    _run_index(
        config=config,
        method=method,
        is_update_run=False,
        verbose=verbose,
        memprofile=memprofile,
        cache=cache,
        log_level=log_level,
        dry_run=dry_run,
        skip_validation=skip_validation,
    )


def update_cli(
    root_dir: Path,
    method: IndexingMethod,
    verbose: bool,
    memprofile: bool,
    cache: bool,
    log_level: str,
    config_filepath: Path | None,
    skip_validation: bool,
    output_dir: Path | None,
):
    """Run the pipeline with the given config."""
    cli_overrides = {}
    if output_dir:
        cli_overrides["output.base_dir"] = str(output_dir)
        cli_overrides["reporting.base_dir"] = str(output_dir)
        cli_overrides["update_index_output.base_dir"] = str(output_dir)

    config = load_config(root_dir, config_filepath, cli_overrides)

    _run_index(
        config=config,
        method=method,
        is_update_run=True,
        verbose=verbose,
        memprofile=memprofile,
        cache=cache,
        log_level=log_level,
        dry_run=False,
        skip_validation=skip_validation,
    )


def _run_index(
    config,
    method,
    is_update_run,
    verbose,
    memprofile,
    cache,
    log_level,
    dry_run,
    skip_validation,
):
    # Configure the root logger with the specified log level
    from graphrag.logger.standard_logging import init_loggers

    # Initialize loggers with console output enabled (CLI usage) and reporting config
    init_loggers(
        config=config.reporting,
        root_dir=str(config.root_dir) if config.root_dir else None,
        log_level=log_level,
        enable_console=True,
    )

    progress_logger = logging.getLogger(__name__).getChild("progress")
    info, error, success = _logger_helper(progress_logger)

    if not cache:
        config.cache.type = CacheType.none

    # Log the configuration details
    if config.reporting.type == ReportingType.file:
        log_dir = Path(config.root_dir or "") / (config.reporting.base_dir or "")
        log_path = log_dir / "logs.txt"
        info(f"Logging enabled at {log_path}", True)
    else:
        info(
            f"Logging not enabled for config {redact(config.model_dump())}",
            True,
        )

    if not skip_validation:
        validate_config_names(progress_logger, config)

    info(f"Starting pipeline run. {dry_run=}", verbose)
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
            method=method,
            is_update_run=is_update_run,
            memory_profile=memprofile,
        )
    )
    encountered_errors = any(
        output.errors and len(output.errors) > 0 for output in outputs
    )

    if encountered_errors:
        error(
            "Errors occurred during the pipeline run, see logs for more details.", True
        )
    else:
        success("All workflows completed successfully.", True)

    sys.exit(1 if encountered_errors else 0)
