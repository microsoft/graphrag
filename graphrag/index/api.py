# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Indexing API for GraphRAG.

WARNING: This API is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

import logging
from pathlib import Path

from graphrag.config.enums import CacheType, ReportingType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.resolve_timestamp_path import resolve_timestamp_path

from . import create_pipeline_config as cpc
from .cache.noop_pipeline_cache import NoopPipelineCache
from .emit.types import TableEmitterType
from .progress import (
    NullProgressReporter,
    PrintProgressReporter,
    ProgressReporter,
)
from .progress.rich import RichProgressReporter
from .run import run_pipeline_with_config
from .typing import PipelineRunResult

create_pipeline_config = cpc


def enable_logging(log_filepath: str | Path, verbose: bool = False) -> None:
    """Enable logging to a file.

    Parameters
    ----------
    log_filepath : str | Path
        The path to the log file.
    verbose : bool, default=False
        Whether to log debug messages.
    """
    log_filepath = Path(log_filepath)
    log_filepath.parent.mkdir(parents=True, exist_ok=True)
    log_filepath.touch(exist_ok=True)

    logging.basicConfig(
        filename=log_filepath,
        filemode="a",
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG if verbose else logging.INFO,
    )


def enable_logging_with_config(
    config: GraphRagConfig, timestamp_value: str, verbose: bool = False
) -> tuple[bool, str]:
    """Enable logging to a file based on the config.

    Parameters
    ----------
    config : GraphRagConfig
        The configuration.
    timestamp_value : str
        The timestamp value representing the directory to place the log files.
    verbose : bool, default=False
        Whether to log debug messages.

    Returns
    -------
    tuple[bool, str]
        A tuple of a boolean indicating if logging was enabled and the path to the log file.
        (False, "") if logging was not enabled.
        (True, str) if logging was enabled.
    """
    if config.reporting.type == ReportingType.file:
        log_path = resolve_timestamp_path(
            Path(config.root_dir) / config.reporting.base_dir / "indexing-engine.log",
            timestamp_value,
        )
        enable_logging(log_path, verbose)
        return (True, str(log_path))
    return (False, "")


def load_progress_reporter(reporter_type: str = "none") -> ProgressReporter:
    """Load a progress reporter.

    Parameters
    ----------
    reporter_type : {"rich", "print", "none"}, default=rich
        The type of progress reporter to load.

    Returns
    -------
    ProgressReporter
    """
    if reporter_type == "rich":
        return RichProgressReporter("GraphRAG Indexer ")
    if reporter_type == "print":
        return PrintProgressReporter("GraphRAG Indexer ")
    if reporter_type == "none":
        return NullProgressReporter()

    msg = f"Invalid progress reporter type: {reporter_type}"
    raise ValueError(msg)


async def build_index(
    config: GraphRagConfig,
    progress_reporter: ProgressReporter,
    run_id: str,
    memory_profile: bool,
    emit: list[str] | None,
) -> list[PipelineRunResult]:
    """Run the pipeline with the given configuration.

    Parameters
    ----------
    config : PipelineConfig
        The configuration.
    progress_reporter : ProgressReporter
        The progress reporter.
    run_id : str
        The run id. Creates a output directory with this name.
    memory_profile : bool
        Whether to enable memory profiling.
    emit : list[str] | None
        The list of emitter types to emit.
        Accepted values {"parquet", "csv"}.

    Returns
    -------
    list[PipelineRunResult]
        The list of pipeline run results
    """
    try:
        resolve_timestamp_path(config.storage.base_dir, run_id)
        resume = True
    except ValueError as _:
        resume = False
    pipeline_config = create_pipeline_config(config)
    pipeline_cache = (
        NoopPipelineCache() if config.cache.type == CacheType.none is None else None
    )
    outputs: list[PipelineRunResult] = []
    async for output in run_pipeline_with_config(
        pipeline_config,
        run_id=run_id,
        memory_profile=memory_profile,
        cache=pipeline_cache,
        progress_reporter=progress_reporter,
        emit=([TableEmitterType(e) for e in emit] if emit is not None else None),
        is_resume_run=resume,
    ):
        outputs.append(output)
        if output.errors and len(output.errors) > 0:
            progress_reporter.error(output.workflow)
        else:
            progress_reporter.success(output.workflow)
        progress_reporter.info(str(output.result))
    return outputs
