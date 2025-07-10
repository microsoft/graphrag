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
    memprofile: bool,
    cache: bool,
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
        dry_run=dry_run,
        skip_validation=skip_validation,
    )


def update_cli(
    root_dir: Path,
    method: IndexingMethod,
    verbose: bool,
    memprofile: bool,
    cache: bool,
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
    dry_run,
    skip_validation,
):
    # Configure the root logger with the specified log level
    from graphrag.logger.standard_logging import init_loggers

    # Initialize loggers and reporting config
    init_loggers(
        config=config,
        root_dir=str(config.root_dir) if config.root_dir else None,
        verbose=verbose,
    )

    if not cache:
        config.cache.type = CacheType.none

    # Log the configuration details
    if config.reporting.type == ReportingType.file:
        log_dir = Path(config.root_dir or "") / (config.reporting.base_dir or "")
        log_path = log_dir / "logs.txt"
        logger.info("Logging enabled at %s", log_path)
    else:
        logger.info(
            "Logging not enabled for config %s",
            redact(config.model_dump()),
        )

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
            memory_profile=memprofile,
        )
    )
    encountered_errors = any(
        output.errors and len(output.errors) > 0 for output in outputs
    )

    if encountered_errors:
        logger.error(
            "Errors occurred during the pipeline run, see logs for more details."
        )
    else:
        logger.info("All workflows completed successfully.")

    sys.exit(1 if encountered_errors else 0)
