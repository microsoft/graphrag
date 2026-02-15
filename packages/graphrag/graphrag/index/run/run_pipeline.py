# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Different methods to run the pipeline."""

import json
import logging
import time
from collections.abc import AsyncIterable
from dataclasses import asdict
from typing import Any

import pandas as pd
from graphrag_cache import create_cache
from graphrag_storage import create_storage
from graphrag_storage.tables.table_provider import TableProvider
from graphrag_storage.tables.table_provider_factory import create_table_provider

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.run.profiling import WorkflowProfiler
from graphrag.index.run.utils import create_run_context
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.pipeline import Pipeline
from graphrag.index.typing.pipeline_run_result import PipelineRunResult

logger = logging.getLogger(__name__)


async def run_pipeline(
    pipeline: Pipeline,
    config: GraphRagConfig,
    callbacks: WorkflowCallbacks,
    is_update_run: bool = False,
    additional_context: dict[str, Any] | None = None,
    input_documents: pd.DataFrame | None = None,
) -> AsyncIterable[PipelineRunResult]:
    """Run all workflows using a simplified pipeline."""
    input_storage = create_storage(config.input_storage)

    output_storage = create_storage(config.output_storage)

    output_table_provider = create_table_provider(config.table_provider, output_storage)

    cache = create_cache(config.cache)

    # load existing state in case any workflows are stateful
    state_json = await output_storage.get("context.json")
    state = json.loads(state_json) if state_json else {}

    if additional_context:
        state.setdefault("additional_context", {}).update(additional_context)

    if is_update_run:
        logger.info("Running incremental indexing.")

        update_storage = create_storage(config.update_output_storage)
        # we use this to store the new subset index, and will merge its content with the previous index
        update_timestamp = time.strftime("%Y%m%d-%H%M%S")
        timestamped_storage = update_storage.child(update_timestamp)
        delta_storage = timestamped_storage.child("delta")
        delta_table_provider = create_table_provider(
            config.table_provider, delta_storage
        )
        # copy the previous output to a backup folder, so we can replace it with the update
        # we'll read from this later when we merge the old and new indexes
        previous_storage = timestamped_storage.child("previous")
        previous_table_provider = create_table_provider(
            config.table_provider, previous_storage
        )

        await _copy_previous_output(output_table_provider, previous_table_provider)

        state["update_timestamp"] = update_timestamp

        # if the user passes in a df directly, write directly to storage so we can skip finding/parsing later
        if input_documents is not None:
            await delta_table_provider.write_dataframe("documents", input_documents)
            pipeline.remove("load_update_documents")

        context = create_run_context(
            input_storage=input_storage,
            output_storage=delta_storage,
            output_table_provider=delta_table_provider,
            previous_table_provider=previous_table_provider,
            cache=cache,
            callbacks=callbacks,
            state=state,
        )

    else:
        logger.info("Running standard indexing.")

        # if the user passes in a df directly, write directly to storage so we can skip finding/parsing later
        if input_documents is not None:
            await output_table_provider.write_dataframe("documents", input_documents)
            pipeline.remove("load_input_documents")

        context = create_run_context(
            input_storage=input_storage,
            output_storage=output_storage,
            output_table_provider=output_table_provider,
            cache=cache,
            callbacks=callbacks,
            state=state,
        )

    async for table in _run_pipeline(
        pipeline=pipeline,
        config=config,
        context=context,
    ):
        yield table


async def _run_pipeline(
    pipeline: Pipeline,
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> AsyncIterable[PipelineRunResult]:
    start_time = time.time()

    last_workflow = "<startup>"

    try:
        await _dump_json(context)

        logger.info("Executing pipeline...")
        for name, workflow_function in pipeline.run():
            last_workflow = name
            context.callbacks.workflow_start(name, None)

            with WorkflowProfiler() as profiler:
                result = await workflow_function(config, context)

            context.callbacks.workflow_end(name, result)
            yield PipelineRunResult(
                workflow=name, result=result.result, state=context.state, error=None
            )
            context.stats.workflows[name] = profiler.metrics
            if result.stop:
                logger.info("Halting pipeline at workflow request")
                break

        context.stats.total_runtime = time.time() - start_time
        logger.info("Indexing pipeline complete.")
        await _dump_json(context)

    except Exception as e:
        logger.exception("error running workflow %s", last_workflow)
        yield PipelineRunResult(
            workflow=last_workflow, result=None, state=context.state, error=e
        )


async def _dump_json(context: PipelineRunContext) -> None:
    """Dump the stats and context state to the storage."""
    await context.output_storage.set(
        "stats.json", json.dumps(asdict(context.stats), indent=4, ensure_ascii=False)
    )
    # Dump context state, excluding additional_context
    temp_context = context.state.pop(
        "additional_context", None
    )  # Remove reference only, as object size is uncertain
    try:
        state_blob = json.dumps(context.state, indent=4, ensure_ascii=False)
    finally:
        if temp_context:
            context.state["additional_context"] = temp_context

    await context.output_storage.set("context.json", state_blob)


async def _copy_previous_output(
    output_table_provider: TableProvider,
    previous_table_provider: TableProvider,
) -> None:
    """Copy all parquet tables from output to previous storage for backup."""
    for table_name in output_table_provider.list():
        table = await output_table_provider.read_dataframe(table_name)
        await previous_table_provider.write_dataframe(table_name, table)
