#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Main definition."""

import asyncio
import platform
import re
import sys
import warnings
from pathlib import Path

from graphrag.index.cache import NoopPipelineCache
from graphrag.index.config import PipelineConfig
from graphrag.index.default_config import (
    DefaultConfigParametersModel,
    default_config,
    default_config_parameters,
    default_config_parameters_from_env_vars,
)
from graphrag.index.progress import (
    NullProgressReporter,
    PrintProgressReporter,
    ProgressReporter,
)
from graphrag.index.progress.rich import RichProgressReporter
from graphrag.index.run import run_pipeline_with_config

# Ignore warnings from numba
warnings.filterwarnings("ignore", message=".*NumbaDeprecationWarning.*")


def redact(input: str) -> str:
    """Sanitize the config json."""
    # Redact any sensitive configuration
    result = re.sub(r'"api_key": ".*?"', '"api_key": "REDACTED"', input)
    result = re.sub(
        r'"connection_string": ".*?"', '"connection_string": "REDACTED"', result
    )
    result = re.sub(r'"organization": ".*?"', '"organization": "REDACTED"', result)
    return re.sub(r'"container_name": ".*?"', '"container_name": "REDACTED"', result)


def index_cli(
    root: str,
    verbose: bool,
    resume: str | None,
    memprofile: bool,
    nocache: bool,
    reporter: str | None,
    config: str | None,
    emit: str | None,
    cli: bool = False,
):
    """Run the pipeline with the given config."""
    progress_reporter = _get_progress_reporter(reporter)
    pipeline_config: str | PipelineConfig = config or _create_default_config(
        root, verbose, resume, progress_reporter
    )
    cache = NoopPipelineCache() if nocache else None
    pipeline_emit = emit.split(",") if emit else None

    encountered_errors = False

    def _run_workflow_async() -> None:
        import signal

        def handle_signal(signum, _):
            # Handle the signal here
            progress_reporter.info(f"Received signal {signum}, exiting...")
            progress_reporter.dispose()
            for task in asyncio.all_tasks():
                task.cancel()
            progress_reporter.info("All tasks cancelled. Exiting...")

        # Register signal handlers for SIGINT and SIGHUP
        signal.signal(signal.SIGINT, handle_signal)

        if sys.platform == "win32":
            signal.signal(signal.CTRL_C_EVENT, handle_signal)
            signal.signal(signal.SIGBREAK, handle_signal)
        else:
            signal.signal(signal.SIGHUP, handle_signal)

        async def execute():
            nonlocal encountered_errors
            async for output in await run_pipeline_with_config(
                pipeline_config,
                debug=verbose,
                resume=resume,  # type: ignore
                memory_profile=memprofile,
                cache=cache,
                progress_reporter=progress_reporter,
                emit=pipeline_emit,  # type: ignore
            ):
                if output.errors and len(output.errors) > 0:
                    encountered_errors = True
                    progress_reporter.error(output.workflow)
                else:
                    progress_reporter.success(output.workflow)

                progress_reporter.info(str(output.result))

        if platform.system() == "Windows":
            import nest_asyncio  # type: ignore Ignoring because out of windows this will cause an error

            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(execute())
        elif sys.version_info >= (3, 11):
            import uvloop  # type: ignore Ignoring because on windows this will cause an error

            with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:  # type: ignore Ignoring because minor versions this will throw an error
                runner.run(execute())
        else:
            import uvloop  # type: ignore Ignoring because on windows this will cause an error

            uvloop.install()
            asyncio.run(execute())

    _run_workflow_async()
    progress_reporter.stop()
    if encountered_errors:
        progress_reporter.error(
            "Errors occurred during the pipeline run, see logs for more details."
        )
    else:
        progress_reporter.success("All workflows completed successfully.")

    if cli:
        sys.exit(1 if encountered_errors else 0)


def _create_default_config(
    root: str, verbose: bool, resume: str | None, reporter: ProgressReporter
) -> PipelineConfig:
    """Create a default config if none is provided."""
    import json

    if not Path(root).exists():
        msg = f"Root directory {root} does not exist"
        raise ValueError(msg)

    parameters = _read_config_parameters(root, resume, reporter)
    if verbose:
        reporter.info(
            f"Using default configuration: {redact(json.dumps(parameters.to_dict(), indent=4))}"
        )
    result = default_config(parameters, verbose)
    if verbose:
        reporter.info(
            f"Final Config: {redact(json.dumps(result.model_dump(), indent=4))}"
        )
    return result


def _read_config_parameters(root: str, resume: str | None, reporter: ProgressReporter):
    _root = Path(root)
    settings_yaml = _root / "settings.yaml"
    if not settings_yaml.exists():
        settings_yaml = _root / "settings.yml"
    settings_json = _root / "settings.json"

    if settings_yaml.exists():
        reporter.success(f"Reading settings from {settings_yaml}")
        with settings_yaml.open("r") as file:
            import yaml

            data = yaml.safe_load(file)
            model = DefaultConfigParametersModel.model_validate(data)
            return default_config_parameters(model, root, resume)

    if settings_json.exists():
        reporter.success(f"Reading settings from {settings_json}")
        with settings_json.open("r") as file:
            import json

            data = json.loads(file.read())
            model = DefaultConfigParametersModel.model_validate(data)
            return default_config_parameters(data, root, resume)

    reporter.success("Reading settings from environment variables")
    return default_config_parameters_from_env_vars(root, resume)


def _get_progress_reporter(reporter_type: str | None) -> ProgressReporter:
    if reporter_type is None or reporter_type == "rich":
        return RichProgressReporter("Indexing Engine")
    if reporter_type == "print":
        return PrintProgressReporter("Indexing Engine")
    if reporter_type == "none":
        return NullProgressReporter()

    msg = f"Invalid progress reporter type: {reporter_type}"
    raise ValueError(msg)
