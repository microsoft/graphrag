# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Different methods to run the pipeline."""

import json
import logging
import time
import traceback
from collections.abc import AsyncIterable
from dataclasses import asdict

import pandas as pd

from graphrag.cache.factory import CacheFactory
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.console_workflow_callbacks import ConsoleWorkflowCallbacks
from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunStats
from graphrag.index.input.factory import create_input
from graphrag.index.run.utils import create_callback_chain, create_run_context
from graphrag.index.typing import Pipeline, PipelineRunResult
from graphrag.index.update.incremental_index import (
    get_delta_docs,
    update_dataframe_outputs,
)
from graphrag.logger.base import ProgressLogger
from graphrag.logger.null_progress import NullProgressLogger
from graphrag.logger.progress import Progress
from graphrag.storage.factory import StorageFactory
from graphrag.storage.pipeline_storage import PipelineStorage
from graphrag.utils.storage import delete_table_from_storage, write_table_to_storage

log = logging.getLogger(__name__)


# these are transient outputs written to storage for downstream workflow use
# they are not required after indexing, so we'll clean them up at the end for clarity
# (unless snapshots.transient is set!)
transient_outputs = [
    "input",
    "base_communities",
    "base_entity_nodes",
    "base_relationship_edges",
    "create_base_text_units",
]


async def run_pipeline(
    pipeline: Pipeline,
    config: GraphRagConfig,
    cache: PipelineCache | None = None,
    callbacks: list[WorkflowCallbacks] | None = None,
    logger: ProgressLogger | None = None,
    is_update_run: bool = False,
) -> AsyncIterable[PipelineRunResult]:
    """Run all workflows using a simplified pipeline."""
    root_dir = config.root_dir
    progress_logger = logger or NullProgressLogger()
    callbacks = callbacks or [ConsoleWorkflowCallbacks()]
    callback_chain = create_callback_chain(callbacks, progress_logger)
    storage_config = config.output.model_dump()  # type: ignore
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

    dataset = await create_input(config.input, logger, root_dir)

    if is_update_run:
        progress_logger.info("Running incremental indexing.")

        update_storage_config = config.update_index_output.model_dump()  # type: ignore
        update_index_storage = StorageFactory().create_storage(
            storage_type=update_storage_config["type"],  # type: ignore
            kwargs=update_storage_config,
        )

        delta_dataset = await get_delta_docs(dataset, storage)

        # Fail on empty delta dataset
        if delta_dataset.new_inputs.empty:
            error_msg = "Incremental Indexing Error: No new documents to process."
            raise ValueError(error_msg)

        delta_storage = update_index_storage.child("delta")

        # Run the pipeline on the new documents
        tables_dict = {}
        async for table in _run_pipeline(
            pipeline=pipeline,
            config=config,
            dataset=delta_dataset.new_inputs,
            cache=cache,
            storage=delta_storage,
            callbacks=callback_chain,
            logger=progress_logger,
        ):
            tables_dict[table.workflow] = table.result

        progress_logger.success("Finished running workflows on new documents.")

        await update_dataframe_outputs(
            dataframe_dict=tables_dict,
            storage=storage,
            update_storage=update_index_storage,
            config=config,
            cache=cache,
            callbacks=NoopWorkflowCallbacks(),
            progress_logger=progress_logger,
        )

    else:
        progress_logger.info("Running standard indexing.")

        async for table in _run_pipeline(
            pipeline=pipeline,
            config=config,
            dataset=dataset,
            cache=cache,
            storage=storage,
            callbacks=callback_chain,
            logger=progress_logger,
        ):
            yield table


async def _run_pipeline(
    pipeline: Pipeline,
    config: GraphRagConfig,
    dataset: pd.DataFrame,
    cache: PipelineCache,
    storage: PipelineStorage,
    callbacks: WorkflowCallbacks,
    logger: ProgressLogger,
) -> AsyncIterable[PipelineRunResult]:
    start_time = time.time()

    context = create_run_context(storage=storage, cache=cache, stats=None)

    log.info("Final # of rows loaded: %s", len(dataset))
    context.stats.num_documents = len(dataset)
    last_workflow = "input"

    try:
        await _dump_stats(context.stats, context.storage)
        await write_table_to_storage(dataset, "input", context.storage)

        for name, fn in pipeline:
            last_workflow = name
            progress = logger.child(name, transient=False)
            callbacks.workflow_start(name, None)
            work_time = time.time()
            result = await fn(
                config,
                context,
                callbacks,
            )
            progress(Progress(percent=1))
            callbacks.workflow_end(name, result)
            yield PipelineRunResult(name, result, None)

            context.stats.workflows[name] = {"overall": time.time() - work_time}

        context.stats.total_runtime = time.time() - start_time
        await _dump_stats(context.stats, context.storage)

        if not config.snapshots.transient:
            for output in transient_outputs:
                await delete_table_from_storage(output, context.storage)

    except Exception as e:
        log.exception("error running workflow %s", last_workflow)
        callbacks.error("Error running pipeline!", e, traceback.format_exc())
        yield PipelineRunResult(last_workflow, None, [e])


async def _dump_stats(stats: PipelineRunStats, storage: PipelineStorage) -> None:
    """Dump the stats to the storage."""
    await storage.set(
        "stats.json", json.dumps(asdict(stats), indent=4, ensure_ascii=False)
    )
