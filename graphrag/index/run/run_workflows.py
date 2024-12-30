# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Different methods to run the pipeline."""

import logging
import time
import traceback
from collections.abc import AsyncIterable
from typing import Any, cast

from datashaper import (
    DelegatingVerbCallbacks,
    ExecutionNode,
    VerbDetails,
    WorkflowCallbacks,
)
from datashaper.progress.types import Progress

from graphrag.cache.factory import CacheFactory
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.console_workflow_callbacks import ConsoleWorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.input.factory import create_input
from graphrag.index.run.profiling import _dump_stats
from graphrag.index.run.utils import create_run_context
from graphrag.index.run.workflow import create_callback_chain
from graphrag.index.typing import PipelineRunResult
from graphrag.index.workflows.default_workflows import basic_workflows
from graphrag.logger.base import ProgressLogger
from graphrag.logger.null_progress import NullProgressLogger
from graphrag.storage.factory import StorageFactory

log = logging.getLogger(__name__)


default_workflows = [
    "create_base_text_units",
    "create_final_documents",
    "extract_graph",
    "create_final_covariates",
    "compute_communities",
    "create_final_entities",
    "create_final_relationships",
    "create_final_nodes",
    "create_final_communities",
    "create_final_text_units",
    "create_final_community_reports",
    "generate_text_embeddings",
]


async def run_workflows(
    config: GraphRagConfig,
    cache: PipelineCache | None = None,
    callbacks: list[WorkflowCallbacks] | None = None,
    logger: ProgressLogger | None = None,
    run_id: str | None = None,
) -> AsyncIterable[PipelineRunResult]:
    """Run all workflows using a simplified pipeline."""
    log.info("RUNNING NEW WORKFLOWS WITHOUT DATASHAPER")
    start_time = time.time()

    run_id = run_id or time.strftime("%Y%m%d-%H%M%S")
    root_dir = config.root_dir or ""
    progress_logger = logger or NullProgressLogger()
    callbacks = callbacks or [ConsoleWorkflowCallbacks()]
    callback_chain = create_callback_chain(callbacks, progress_logger)
    storage_config = config.storage.model_dump()  # type: ignore
    storage = StorageFactory().create_storage(
        storage_type=storage_config["type"],  # type: ignore
        kwargs=storage_config,
    )
    cache_config = config.cache.model_dump()  # type: ignore
    cache = cache or CacheFactory().create_cache(
        cache_type=cache_config["type"],  # type: ignore
        root_dir=root_dir,
        kwargs=cache_config,
    )

    context = create_run_context(storage=storage, cache=cache, stats=None)

    dataset = await create_input(config.input, progress_logger, root_dir)

    log.info("Final # of rows loaded: %s", len(dataset))
    context.stats.num_documents = len(dataset)
    last_workflow = "input"

    try:
        await _dump_stats(context.stats, context.storage)
        await context.runtime_storage.set("input", dataset)

        for workflow in default_workflows:
            last_workflow = workflow
            run_workflow = basic_workflows[workflow]
            progress = progress_logger.child(workflow, transient=False)
            callback_chain.on_workflow_start(workflow, None)
            # TEMP: this structure is required for DataShaper downstream compliance
            node = cast(
                "Any",
                ExecutionNode(
                    node_id=workflow,
                    has_explicit_id=True,
                    verb=VerbDetails(
                        name=workflow,
                        func=lambda x: x,
                        treats_input_tables_as_immutable=False,
                    ),
                    node_input="",
                ),
            )
            verb_callbacks = DelegatingVerbCallbacks(node, callback_chain)
            work_time = time.time()
            result = await run_workflow(
                config,
                context,
                verb_callbacks,
            )
            progress(Progress(percent=1))
            callback_chain.on_workflow_end(workflow, None)
            yield PipelineRunResult(workflow, result, None)

            context.stats.workflows[workflow] = {"overall": time.time() - work_time}

        context.stats.total_runtime = time.time() - start_time
        await _dump_stats(context.stats, context.storage)
    except Exception as e:
        log.exception("error running workflow %s", last_workflow)
        cast("WorkflowCallbacks", callback_chain).on_error(
            "Error running pipeline!", e, traceback.format_exc()
        )
        yield PipelineRunResult(last_workflow, None, [e])
