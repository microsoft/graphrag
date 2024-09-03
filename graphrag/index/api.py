# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Indexing API for GraphRAG.

WARNING: This API is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

from pathlib import Path

from graphrag.config import CacheType, GraphRagConfig

from .cache.noop_pipeline_cache import NoopPipelineCache
from .create_pipeline_config import create_pipeline_config
from .emit.types import TableEmitterType
from .progress import (
    ProgressReporter,
)
from .run import run_pipeline_with_config
from .typing import PipelineRunResult


async def build_index(
    config: GraphRagConfig,
    run_id: str = "",
    is_resume_run: bool = False,
    is_update_run: bool = False,
    memory_profile: bool = False,
    progress_reporter: ProgressReporter | None = None,
    emit: list[str] | None = None,
) -> list[PipelineRunResult]:
    """Run the pipeline with the given configuration.

    Parameters
    ----------
    config : PipelineConfig
        The configuration.
    run_id : str
        The run id. Creates a output directory with this name.
    is_resume_run : bool default=False
        Whether to resume a previous index run.
    is_update_run : bool default=False
        Whether to update a previous index run.
    memory_profile : bool
        Whether to enable memory profiling.
    progress_reporter : ProgressReporter | None default=None
        The progress reporter.
    emit : list[str] | None default=None
        The list of emitter types to emit.
        Accepted values {"parquet", "csv"}.

    Returns
    -------
    list[PipelineRunResult]
        The list of pipeline run results
    """

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
        is_resume_run=is_resume_run,
        is_update_run=is_update_run,
    ):
        outputs.append(output)
        if progress_reporter:
            if output.errors and len(output.errors) > 0:
                progress_reporter.error(output.workflow)
            else:
                progress_reporter.success(output.workflow)
            progress_reporter.info(str(output.result))
    return outputs


async def update_index(  # noqa: RUF029
    config: GraphRagConfig,  # noqa: ARG001
    run_id: str,  # noqa: ARG001
    memory_profile: bool,  # noqa: ARG001
    update_index_id: str,  # noqa: ARG001
    progress_reporter: ProgressReporter | None = None,  # noqa: ARG001
    emit: list[str] | None = None,  # noqa: ARG001
) -> list[PipelineRunResult]:
    """Run the pipeline with the given configuration.

    Parameters
    ----------
    config : PipelineConfig
        The configuration.
    run_id : str
        The run id. Creates a output directory with this name.
    memory_profile : bool
        Whether to enable memory profiling.
    update_index_id : str
        The index id to update in incremental runs.
    progress_reporter : ProgressReporter | None default=None
        The progress reporter.
    emit : list[str] | None default=None
        The list of emitter types to emit.
        Accepted values {"parquet", "csv"}.

    Returns
    -------
    list[PipelineRunResult]
        The list of pipeline run results
    """
    # Basic init

    # TODO: Review input folder to check if update is viable or if should run index

    # TODO: Get new files to process from input

    # TODO: Execute pipeline over delta
    # TODO: Update index
    # TODO: Write drift report
    # TODO: Return results

    # TODO: After the above steps are implemented, read drift report and run full index if drift is above threshold
    msg = "This function is not implemented yet."
    raise NotImplementedError(msg)
