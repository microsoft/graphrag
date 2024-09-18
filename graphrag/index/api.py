# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Indexing API for GraphRAG.

WARNING: This API is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

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
    emit: list[TableEmitterType] = [TableEmitterType.Parquet],  # noqa: B006
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
    emit : list[str]
        The list of emitter types to emit.
        Accepted values {"parquet", "csv"}.

    Returns
    -------
    list[PipelineRunResult]
        The list of pipeline run results
    """
    if is_resume_run and is_update_run:
        msg = "Cannot resume and update a run at the same time."
        raise ValueError(msg)

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
        emit=emit,
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
