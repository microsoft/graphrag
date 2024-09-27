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
    GraphRagConfig,
    create_graphrag_config,
)
from graphrag.config.enums import ContextSwitchType
from graphrag.common.utils.common_utils import is_valid_guid
from graphrag.index import PipelineConfig, create_pipeline_config
from graphrag.index.cache import NoopPipelineCache
from graphrag.common.progress import (
    NullProgressReporter,
    PrintProgressReporter,
    ProgressReporter,
)
from graphrag.common.progress.rich import RichProgressReporter
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
    community_level: int,
    context_operation: str | None,
    context_id: str | None,
    verbose: bool,
    resume: str | None,
    memprofile: bool,
    nocache: bool,
    config: str | None,
    emit: str | None,
    dryrun: bool,
    overlay_defaults: bool,
    cli: bool = False,
    use_kusto_community_reports: bool = False,
    optimized_search: bool = False,
    files:[str]=[],
    input_base_dir:str="",
    output_base_dir:str=""
):
    """Run the pipeline with the given config."""
    root = Path(__file__).parent.parent.parent.__str__() # accept from whatever coming from function app
    run_id = resume or time.strftime("%Y%m%d-%H%M%S")
    _enable_logging(root, run_id, verbose)
    progress_reporter = _get_progress_reporter("none")
    if init:
        _initialize_project_at(root, progress_reporter)
    if overlay_defaults:
        pipeline_config: str | PipelineConfig = _create_default_config(
            root, config, verbose, dryrun or False, progress_reporter
        )
    ############# Context Switching ################
    if context_id is not None:
        logging.info("Switching context1")
        _switch_context(root, config,  progress_reporter, context_operation, context_id, community_level, optimized_search, use_kusto_community_reports, files=files)
        return 0
    ################################################
    else:
        pipeline_config: str | PipelineConfig = config or _create_default_config(
            root, None, verbose, dryrun or False, progress_reporter
        )
    if input_base_dir is not None:
        logging.info(f"input_base_dir is {input_base_dir}, overwriting in config")
        pipeline_config.input.base_dir = input_base_dir
    
    if output_base_dir is not None:
        logging.info(f"input_base_dir is {output_base_dir}, overwriting in config")
        pipeline_config.storage.base_dir = output_base_dir
        pipeline_config.cache.base_dir = output_base_dir
        pipeline_config.reporting.base_dir = output_base_dir
    cache = NoopPipelineCache() if nocache else None
    pipeline_emit = emit.split(",") if emit else None
    encountered_errors = False
    logging.info("Loaded the pipeline successfully")
    def _run_workflow_async() -> None:
        import signal
        logging.info("Step1")
        def handle_signal(signum, _):
            # Handle the signal here
            progress_reporter.info(f"Received signal {signum}, exiting...")
            progress_reporter.dispose()
            for task in asyncio.all_tasks():
                task.cancel()
            progress_reporter.info("All tasks cancelled. Exiting...")

        # Register signal handlers for SIGINT and SIGHUP
        logging.info("Step2")
        #signal.signal(signal.SIGINT, handle_signal)
        
        logging.info("Step3")
        #if sys.platform != "win32":
        #    signal.signal(signal.SIGHUP, handle_signal)

        logging.info("Step4")
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
                context_id=context_id,
            ):
                if output.errors and len(output.errors) > 0:
                    encountered_errors = True
                    progress_reporter.error(output.workflow)
                else:
                    progress_reporter.success(output.workflow)

                progress_reporter.info(str(output.result))

        if platform.system() == "Windows":
            logging.info("All set to execute the workflows on Windows")
            import nest_asyncio  # type: ignore Ignoring because out of windows this will cause an error

            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(execute())
        elif sys.version_info >= (3, 11):
            logging.info("Step6")
            import uvloop  # type: ignore Ignoring because on windows this will cause an error

            with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:  # type: ignore Ignoring because minor versions this will throw an error
                runner.run(execute())
        else:
            logging.info("Step 6")
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
        #sys.exit(1 if encountered_errors else 0)
        return 0

def _switch_context(root: str, config: str,
                    reporter: ProgressReporter, context_operation: str | None,
                    context_id: str, community_level: int, optimized_search: bool,
                    use_kusto_community_reports: bool, files:[str]) -> None:
    """Switch the context to the given context."""
    reporter.info(f"Switching context to {context_id} using operation {context_operation}")
    logging.info("Switching context to {context_id}")
    from graphrag.index.context_switch.contextSwitcher import ContextSwitcher
    context_switcher = ContextSwitcher(
        root_dir=root,
        config_dir=config,
        reporter=reporter,
        context_id=context_id,
        community_level=community_level,
        data_dir=None,
        optimized_search=optimized_search,
        use_kusto_community_reports=use_kusto_community_reports)
    if context_operation == ContextSwitchType.Activate:
        context_switcher.activate(files=files)
    elif context_operation == ContextSwitchType.Deactivate:
        context_switcher.deactivate()
    else:
        msg = f"Invalid context operation {context_operation}"
        raise ValueError(msg)

def _initialize_project_at(path: str, reporter: ProgressReporter) -> None:
    """Initialize the project at the given path."""
    reporter.info(f"Initializing project at {path}")
    root = Path(path)
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)

    settings_yaml = root / "settings/settings.yaml"
    
    dotenv = root / ".env"
    

    

    prompts_dir = root / "prompts"
    

    entity_extraction = prompts_dir / "entity_extraction.txt"
    

    summarize_descriptions = prompts_dir / "summarize_descriptions.txt"

    claim_extraction = prompts_dir / "claim_extraction.txt"
    

    community_report = prompts_dir / "community_report.txt"
    


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
        return
    return result


def _read_config_parameters(root: str, config: str | None, reporter: ProgressReporter):
    _root = Path(root)
    settings_yaml = (
        Path(config)
        if config and Path(config).suffix in [".yaml", ".yml"]
        else _root / "settings/settings.yaml"
    )
    if not settings_yaml.exists():
        settings_yaml = _root / "settings/settings.yml"
    settings_json = (
        Path(config)
        if config and Path(config).suffix == ".json"
        else _root / "settings/settings.json"
    )

    if settings_yaml.exists():
        reporter.success(f"Reading settings from {settings_yaml}")
        with settings_yaml.open("rb") as file:
            import yaml

            data = yaml.safe_load(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    if settings_json.exists():
        reporter.success(f"Reading settings from {settings_json}")
        with settings_json.open("rb") as file:
            import json

            data = json.loads(file.read().decode(encoding="utf-8", errors="strict"))
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
    #logging_file.parent.mkdir(parents=True, exist_ok=True)

    #logging_file.touch(exist_ok=True)
    handler = logging.StreamHandler(stream=sys.stdout)
    #fileHandler = logging.FileHandler(logging_file, mode="a")
    logging.basicConfig(
        #filename=str(logging_file),
        #filemode="a",
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG if verbose else logging.INFO,
        handlers=[handler]
    )
