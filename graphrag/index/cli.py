# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Main definition."""

import asyncio
import json
import logging
import platform
import sys
import time
import warnings
from pathlib import Path

from graphrag.config import (
    create_graphrag_config,
)
from graphrag.index import PipelineConfig, create_pipeline_config
from graphrag.index.cache import NoopPipelineCache
from graphrag.index.progress import (
    NullProgressReporter,
    PrintProgressReporter,
    ProgressReporter,
)
from graphrag.index.progress.rich import RichProgressReporter
from graphrag.index.run import run_pipeline_with_config

from .emit import TableEmitterType
from .graph.extractors.claims.prompts import CLAIM_EXTRACTION_PROMPT
from .graph.extractors.community_reports.prompts import COMMUNITY_REPORT_PROMPT
from .graph.extractors.graph.prompts import GRAPH_EXTRACTION_PROMPT
from .graph.extractors.summarize.prompts import SUMMARIZE_PROMPT
from .init_content import INIT_DOTENV, INIT_YAML

# Ignore warnings from numba
warnings.filterwarnings("ignore", message=".*NumbaDeprecationWarning.*")

log = logging.getLogger(__name__)


def redact(input: dict) -> str:
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
                    result[key] = f"REDACTED, length {len(value)}"
            elif isinstance(value, dict):
                result[key] = redact_dict(value)
            elif isinstance(value, list):
                result[key] = [redact_dict(i) for i in value]
            else:
                result[key] = value
        return result

    redacted_dict = redact_dict(input)
    return json.dumps(redacted_dict, indent=4)


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
    overlay_defaults: bool,
    cli: bool = False,
):
    """Run the pipeline with the given config."""
    run_id = resume or time.strftime("%Y%m%d-%H%M%S")
    _enable_logging(root, run_id, verbose)
    progress_reporter = _get_progress_reporter(reporter)
    if init:
        _initialize_project_at(root, progress_reporter)
        sys.exit(0)
    if overlay_defaults:
        pipeline_config: str | PipelineConfig = _create_default_config(
            root, config, verbose, dryrun or False, progress_reporter
        )
    else:
        pipeline_config: str | PipelineConfig = config or _create_default_config(
            root, None, verbose, dryrun or False, progress_reporter
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
                run_id=run_id,
                memory_profile=memprofile,
                cache=cache,
                progress_reporter=progress_reporter,
                emit=(
                    [TableEmitterType(e) for e in pipeline_emit]
                    if pipeline_emit
                    else None
                ),
                is_resume_run=bool(resume),
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
    root: str,
    config: str | None,
    verbose: bool,
    dryrun: bool,
    reporter: ProgressReporter,
) -> PipelineConfig:
    """Overlay default values on an existing config or create a default config if none is provided."""
    if config and not Path(config).exists():
        msg = f"Configuration file {config} does not exist"
        raise ValueError

    if not Path(root).exists():
        msg = f"Root directory {root} does not exist"
        raise ValueError(msg)

    parameters = _read_config_parameters(root, config, reporter)
    log.info(
        "using default configuration: %s",
        redact(parameters.model_dump()),
    )

    if verbose or dryrun:
        reporter.info(f"Using default configuration: {redact(parameters.model_dump())}")
    result = create_pipeline_config(parameters, verbose)
    if verbose or dryrun:
        reporter.info(f"Final Config: {redact(result.model_dump())}")

    if dryrun:
        reporter.info("dry run complete, exiting...")
        sys.exit(0)
    return result


def _read_config_parameters(root: str, config: str | None, reporter: ProgressReporter):
    _root = Path(root)
    settings_yaml = (
        Path(config)
        if config and Path(config).suffix in [".yaml", ".yml"]
        else _root / "settings.yaml"
    )
    if not settings_yaml.exists():
        settings_yaml = _root / "settings.yml"
    settings_json = (
        Path(config)
        if config and Path(config).suffix == ".json"
        else _root / "settings.json"
    )

    if settings_yaml.exists():
        reporter.success(f"Reading settings from {settings_yaml}")
        with settings_yaml.open("r") as file:
            import yaml

            data = yaml.safe_load(file)
            return create_graphrag_config(data, root)

    if settings_json.exists():
        reporter.success(f"Reading settings from {settings_json}")
        with settings_json.open("r") as file:
            import json

            data = json.loads(file.read())
            return create_graphrag_config(data, root)

    reporter.success("Reading settings from environment variables")
    return create_graphrag_config(root_dir=root)


def _get_progress_reporter(reporter_type: str | None) -> ProgressReporter:
    if reporter_type is None or reporter_type == "rich":
        return RichProgressReporter("GraphRAG Indexer ")
    if reporter_type == "print":
        return PrintProgressReporter("GraphRAG Indexer ")
    if reporter_type == "none":
        return NullProgressReporter()

    msg = f"Invalid progress reporter type: {reporter_type}"
    raise ValueError(msg)


def _enable_logging(root_dir: str, run_id: str, verbose: bool) -> None:
    logging_file = (
        Path(root_dir) / "output" / run_id / "reports" / "indexing-engine.log"
    )
    logging_file.parent.mkdir(parents=True, exist_ok=True)

    logging_file.touch(exist_ok=True)

    logging.basicConfig(
        filename=str(logging_file),
        filemode="a",
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG if verbose else logging.INFO,
    )
