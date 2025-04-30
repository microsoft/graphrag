# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Different methods to run the pipeline."""

import json
import logging
import re
import time
import traceback
from collections.abc import AsyncIterable
from dataclasses import asdict

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.input.factory import create_input
from graphrag.index.run.utils import create_run_context
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.pipeline import Pipeline
from graphrag.index.typing.pipeline_run_result import PipelineRunResult
from graphrag.index.update.incremental_index import get_delta_docs
from graphrag.logger.base import ProgressLogger
from graphrag.logger.progress import Progress
from graphrag.storage.pipeline_storage import PipelineStorage
from graphrag.utils.api import create_cache_from_config, create_storage_from_config
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

log = logging.getLogger(__name__)


async def run_pipeline(
    pipeline: Pipeline,
    config: GraphRagConfig,
    callbacks: WorkflowCallbacks,
    logger: ProgressLogger,
    is_update_run: bool = False,
) -> AsyncIterable[PipelineRunResult]:
    """Run all workflows using a simplified pipeline."""
    root_dir = config.root_dir

    storage = create_storage_from_config(config.output)
    cache = create_cache_from_config(config.cache, root_dir)

    dataset = await create_input(config.input, logger, root_dir)

    # load existing state in case any workflows are stateful
    state_json = await storage.get("context.json")
    state = json.loads(state_json) if state_json else {}

    if is_update_run:
        logger.info("Running incremental indexing.")

        delta_dataset = await get_delta_docs(dataset, storage)

        # warn on empty delta dataset
        if delta_dataset.new_inputs.empty:
            warning_msg = "Incremental indexing found no new documents, exiting."
            logger.warning(warning_msg)
        else:
            update_storage = create_storage_from_config(config.update_index_output)
            # we use this to store the new subset index, and will merge its content with the previous index
            update_timestamp = time.strftime("%Y%m%d-%H%M%S")
            timestamped_storage = update_storage.child(update_timestamp)
            delta_storage = timestamped_storage.child("delta")
            # copy the previous output to a backup folder, so we can replace it with the update
            # we'll read from this later when we merge the old and new indexes
            previous_storage = timestamped_storage.child("previous")
            await _copy_previous_output(storage, previous_storage)

            state["update_timestamp"] = update_timestamp

            context = create_run_context(
                storage=delta_storage, cache=cache, callbacks=callbacks, state=state
            )

            # Run the pipeline on the new documents
            async for table in _run_pipeline(
                pipeline=pipeline,
                config=config,
                dataset=delta_dataset.new_inputs,
                logger=logger,
                context=context,
            ):
                yield table

            logger.success("Finished running workflows on new documents.")

    else:
        logger.info("Running standard indexing.")

        context = create_run_context(
            storage=storage, cache=cache, callbacks=callbacks, state=state
        )

        async for table in _run_pipeline(
            pipeline=pipeline,
            config=config,
            dataset=dataset,
            logger=logger,
            context=context,
        ):
            yield table


async def _run_pipeline(
    pipeline: Pipeline,
    config: GraphRagConfig,
    dataset: pd.DataFrame,
    logger: ProgressLogger,
    context: PipelineRunContext,
) -> AsyncIterable[PipelineRunResult]:
    start_time = time.time()

    log.info("Final # of rows loaded: %s", len(dataset))
    context.stats.num_documents = len(dataset)
    last_workflow = "starting documents"

    try:
        await _dump_json(context)
        await write_table_to_storage(dataset, "documents", context.storage)

        for name, workflow_function in pipeline.run():
            last_workflow = name
            progress = logger.child(name, transient=False)
            context.callbacks.workflow_start(name, None)
            work_time = time.time()
            result = await workflow_function(config, context)
            progress(Progress(percent=1))
            context.callbacks.workflow_end(name, result)
            yield PipelineRunResult(
                workflow=name, result=result.result, state=context.state, errors=None
            )

            context.stats.workflows[name] = {"overall": time.time() - work_time}

        context.stats.total_runtime = time.time() - start_time
        await _dump_json(context)

    except Exception as e:
        log.exception("error running workflow %s", last_workflow)
        context.callbacks.error("Error running pipeline!", e, traceback.format_exc())
        yield PipelineRunResult(
            workflow=last_workflow, result=None, state=context.state, errors=[e]
        )


async def _dump_json(context: PipelineRunContext) -> None:
    """Dump the stats and context state to the storage."""
    await context.storage.set(
        "stats.json", json.dumps(asdict(context.stats), indent=4, ensure_ascii=False)
    )
    await context.storage.set(
        "context.json", json.dumps(context.state, indent=4, ensure_ascii=False)
    )


async def _copy_previous_output(
    storage: PipelineStorage,
    copy_storage: PipelineStorage,
):
    for file in storage.find(re.compile(r"\.parquet$")):
        base_name = file[0].replace(".parquet", "")
        table = await load_table_from_storage(base_name, storage)
        await write_table_to_storage(table, base_name, copy_storage)
