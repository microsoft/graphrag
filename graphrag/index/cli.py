# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

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

from .emit import TableEmitterType
from .init_content import INIT_DOTENV, INIT_YAML
from .graph.extractors.graph.prompts import GRAPH_EXTRACTION_PROMPT
from .graph.extractors.summarize.prompts import SUMMARIZE_PROMPT
from .graph.extractors.claims.prompts import CLAIM_EXTRACTION_PROMPT
from .graph.extractors.community_reports.prompts import COMMUNITY_REPORT_PROMPT

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
    init: bool,
    verbose: bool,
    resume: str | None,
    memprofile: bool,
    nocache: bool,
    reporter: str | None,
    config: str | None,
    emit: str | None,
    dryrun: bool,
    cli: bool = False,
):
    """Run the pipeline with the given config."""
    progress_reporter = _get_progress_reporter(reporter)
    if init:
        _initialize_project_at(root, progress_reporter)
        sys.exit(0)
    pipeline_config: str | PipelineConfig = config or _create_default_config(
        root, verbose, dryrun or False, progress_reporter
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

        if sys.platform != "win32":
            signal.signal(signal.SIGHUP, handle_signal)

        async def execute():
            nonlocal encountered_errors
            async for output in run_pipeline_with_config(
                pipeline_config,
                debug=verbose,
                resume=resume,
                memory_profile=memprofile,
                cache=cache,
                progress_reporter=progress_reporter,
                enable_logging=True,
                emit=[TableEmitterType(e) for e in pipeline_emit]
                if pipeline_emit
                else None,
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


def _initialize_project_at(path: str, reporter: ProgressReporter) -> None:
    """Initialize the project at the given path."""
    reporter.info(f"Initializing project at {path}")
    root = Path(path)
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)

    
    settings_yaml = root / "settings.yaml"
    if settings_yaml.exists():
        msg = f"Project already initialized at {root}"
        raise ValueError(msg)

    dotenv = root / ".env"
    if not dotenv.exists():
        with settings_yaml.open("w") as file:
            file.write(INIT_YAML)

    with dotenv.open("w") as file:
        file.write(INIT_DOTENV)

    prompts_dir = root / "prompts"
    if not prompts_dir.exists():
        prompts_dir.mkdir(parents=True, exist_ok=True)

    entity_extraction = prompts_dir / "entity_extraction.txt"
    if not entity_extraction.exists():
        with entity_extraction.open("w") as file:
            file.write(GRAPH_EXTRACTION_PROMPT)

    summarize_descriptions = prompts_dir / "summarize_descriptions.txt"
    if not summarize_descriptions.exists():
        with summarize_descriptions.open("w") as file:
            file.write(SUMMARIZE_PROMPT)
            
    claim_extraction = prompts_dir / "claim_extraction.txt"
    if not claim_extraction.exists():
        with claim_extraction.open("w") as file:
            file.write(CLAIM_EXTRACTION_PROMPT)

    community_report = prompts_dir / "community_report.txt"
    if not community_report.exists():
        with community_report.open("w") as file:
            file.write(COMMUNITY_REPORT_PROMPT)


def _create_default_config(
    root: str, verbose: bool, dryrun: bool, reporter: ProgressReporter
) -> PipelineConfig:
    """Create a default config if none is provided."""
    import json

    if not Path(root).exists():
        msg = f"Root directory {root} does not exist"
        raise ValueError(msg)

    parameters = _read_config_parameters(root, reporter)
    if verbose or dryrun:
        reporter.info(
            f"Using default configuration: {redact(json.dumps(parameters.to_dict(), indent=4))}"
        )
    result = default_config(parameters, verbose)
    if verbose or dryrun:
        reporter.info(
            f"Final Config: {redact(json.dumps(result.model_dump(), indent=4))}"
        )

    if dryrun:
        reporter.info("dry run complete, exiting...")
        sys.exit(0)
    return result


def _read_config_parameters(root: str, reporter: ProgressReporter):
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
            return default_config_parameters(model, root)

    if settings_json.exists():
        reporter.success(f"Reading settings from {settings_json}")
        with settings_json.open("r") as file:
            import json

            data = json.loads(file.read())
            model = DefaultConfigParametersModel.model_validate(data)
            return default_config_parameters(data, root)

    reporter.success("Reading settings from environment variables")
    return default_config_parameters_from_env_vars(root)


def _get_progress_reporter(reporter_type: str | None) -> ProgressReporter:
    if reporter_type is None or reporter_type == "rich":
        return RichProgressReporter("Indexing Engine")
    if reporter_type == "print":
        return PrintProgressReporter("Indexing Engine")
    if reporter_type == "none":
        return NullProgressReporter()

    msg = f"Invalid progress reporter type: {reporter_type}"
    raise ValueError(msg)
