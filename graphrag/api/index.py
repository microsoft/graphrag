# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Indexing API for GraphRAG.

WARNING: This API is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

import logging

from graphrag.cache.noop_pipeline_cache import NoopPipelineCache
from graphrag.callbacks.factory import create_pipeline_reporter
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import CacheType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.run.run_workflows import run_workflows
from graphrag.index.typing import PipelineRunResult
from graphrag.logger.base import ProgressLogger

log = logging.getLogger(__name__)


async def build_index(
    config: GraphRagConfig,
    run_id: str = "",
    is_resume_run: bool = False,
    memory_profile: bool = False,
    callbacks: list[WorkflowCallbacks] | None = None,
    progress_logger: ProgressLogger | None = None,
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
    progress_logger : ProgressLogger | None default=None
        The progress logger.

    Returns
    -------
    list[PipelineRunResult]
        The list of pipeline run results
    """
    is_update_run = bool(config.update_index_storage)

    if is_resume_run and is_update_run:
        msg = "Cannot resume and update a run at the same time."
        raise ValueError(msg)

    pipeline_cache = (
        NoopPipelineCache() if config.cache.type == CacheType.none is None else None
    )
    # create a pipeline reporter and add to any additional callbacks
    # TODO: remove the type ignore once the new config engine has been refactored
    callbacks = callbacks or []
    callbacks.append(create_pipeline_reporter(config.reporting, None))  # type: ignore
    outputs: list[PipelineRunResult] = []

    if memory_profile:
        log.warning("New pipeline does not yet support memory profiling.")

    workflows = _get_workflows_list(config)

    async for output in run_workflows(
        workflows,
        config,
        cache=pipeline_cache,
        callbacks=callbacks,
        logger=progress_logger,
        run_id=run_id,
        is_update_run=is_update_run,
    ):
        outputs.append(output)
        if progress_logger:
            if output.errors and len(output.errors) > 0:
                progress_logger.error(output.workflow)
            else:
                progress_logger.success(output.workflow)
            progress_logger.info(str(output.result))

    return outputs


def _get_workflows_list(config: GraphRagConfig) -> list[str]:
    return [
        "create_base_text_units",
        "create_final_documents",
        "extract_graph",
        "compute_communities",
        "create_final_entities",
        "create_final_relationships",
        "create_final_nodes",
        "create_final_communities",
        *(["create_final_covariates"] if config.claim_extraction.enabled else []),
        "create_final_text_units",
        "create_final_community_reports",
        "generate_text_embeddings",
    ]
