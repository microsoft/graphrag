# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Indexing API for GraphRAG.

WARNING: This API is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

from pathlib import Path

from datashaper import WorkflowCallbacks

from graphrag.cache.noop_pipeline_cache import NoopPipelineCache
from graphrag.callbacks.factory import create_pipeline_reporter
from graphrag.config.enums import CacheType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.create_pipeline_config import create_pipeline_config
from graphrag.index.run import run_pipeline_with_config
from graphrag.index.typing import PipelineRunResult
from graphrag.logging.base import ProgressReporter
from graphrag.vector_stores.factory import VectorStoreType


async def build_index(
    config: GraphRagConfig,
    run_id: str = "",
    is_resume_run: bool = False,
    memory_profile: bool = False,
    callbacks: list[WorkflowCallbacks] | None = None,
    progress_reporter: ProgressReporter | None = None,
) -> list[PipelineRunResult]:
    """Run the pipeline with the given configuration.

    Parameters
    ----------
    config : GraphRagConfig
        The configuration.
    run_id : str
        The run id. Creates a output directory with this name.
    is_resume_run : bool default=False
        Whether to resume a previous index run.
    memory_profile : bool
        Whether to enable memory profiling.
    callbacks : list[WorkflowCallbacks] | None default=None
        A list of callbacks to register.
    progress_reporter : ProgressReporter | None default=None
        The progress reporter.

    Returns
    -------
    list[PipelineRunResult]
        The list of pipeline run results
    """
    is_update_run = bool(config.update_index_storage)

    if is_resume_run and is_update_run:
        msg = "Cannot resume and update a run at the same time."
        raise ValueError(msg)

    config = _patch_vector_config(config)

    pipeline_config = create_pipeline_config(config)
    pipeline_cache = (
        NoopPipelineCache() if config.cache.type == CacheType.none is None else None
    )
    # TODO: remove the type ignore once the new config engine has been refactored
    callbacks = (
        [create_pipeline_reporter(config.reporting, None)] if config.reporting else None  # type: ignore
    )  # type: ignore
    outputs: list[PipelineRunResult] = []
    async for output in run_pipeline_with_config(
        pipeline_config,
        run_id=run_id,
        memory_profile=memory_profile,
        cache=pipeline_cache,
        callbacks=callbacks,
        progress_reporter=progress_reporter,
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


def _patch_vector_config(config: GraphRagConfig):
    """Back-compat patch to ensure a default vector store configuration."""
    if not config.embeddings.vector_store:
        config.embeddings.vector_store = {
            "type": "lancedb",
            "db_uri": "output/lancedb",
            "container_name": "default",
            "overwrite": True,
        }
    # TODO: must update filepath of lancedb (if used) until the new config engine has been implemented
    # TODO: remove the type ignore annotations below once the new config engine has been refactored
    vector_store_type = config.embeddings.vector_store["type"]  # type: ignore
    if vector_store_type == VectorStoreType.LanceDB:
        db_uri = config.embeddings.vector_store["db_uri"]  # type: ignore
        lancedb_dir = Path(config.root_dir).resolve() / db_uri
        config.embeddings.vector_store["db_uri"] = str(lancedb_dir)  # type: ignore
    return config
