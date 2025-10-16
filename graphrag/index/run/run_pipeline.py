# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Different methods to run the pipeline."""

import json
import logging
import re
import time
from collections.abc import AsyncIterable
from dataclasses import asdict
from typing import Any

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.run.utils import create_run_context
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.pipeline import Pipeline
from graphrag.index.typing.pipeline_run_result import PipelineRunResult
from graphrag.index.utils.llm_context import inject_llm_context
from graphrag.storage.pipeline_storage import PipelineStorage
from graphrag.utils.api import create_cache_from_config, create_storage_from_config
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

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
    root_dir = config.root_dir

    input_storage = create_storage_from_config(config.input.storage)
    output_storage = create_storage_from_config(config.output)
    cache = create_cache_from_config(config.cache, root_dir)

    # load existing state in case any workflows are stateful
    state_json = await output_storage.get("context.json")
    state = json.loads(state_json) if state_json else {}

    if additional_context:
        state.setdefault("additional_context", {}).update(additional_context)

    if is_update_run:
        logger.info("Running incremental indexing.")

        update_storage = create_storage_from_config(config.update_index_output)
        # we use this to store the new subset index, and will merge its content with the previous index
        update_timestamp = time.strftime("%Y%m%d-%H%M%S")
        timestamped_storage = update_storage.child(update_timestamp)
        delta_storage = timestamped_storage.child("delta")
        # copy the previous output to a backup folder, so we can replace it with the update
        # we'll read from this later when we merge the old and new indexes
        previous_storage = timestamped_storage.child("previous")
        await _copy_previous_output(output_storage, previous_storage)

        state["update_timestamp"] = update_timestamp

        # if the user passes in a df directly, write directly to storage so we can skip finding/parsing later
        if input_documents is not None:
            await write_table_to_storage(input_documents, "documents", delta_storage)
            pipeline.remove("load_update_documents")

        context = create_run_context(
            input_storage=input_storage,
            output_storage=delta_storage,
            previous_storage=previous_storage,
            cache=cache,
            callbacks=callbacks,
            state=state,
        )

    else:
        logger.info("Running standard indexing.")

        # if the user passes in a df directly, write directly to storage so we can skip finding/parsing later
        if input_documents is not None:
            await write_table_to_storage(input_documents, "documents", output_storage)
            pipeline.remove("load_input_documents")

        context = create_run_context(
            input_storage=input_storage,
            output_storage=output_storage,
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
            # Set current workflow for LLM usage tracking
            context.current_workflow = name

            # Inject pipeline context for LLM usage tracking
            inject_llm_context(context)

            context.callbacks.workflow_start(name, None)
            work_time = time.time()
            result = await workflow_function(config, context)
            context.callbacks.workflow_end(name, result)
            yield PipelineRunResult(
                workflow=name, result=result.result, state=context.state, errors=None
            )
            context.stats.workflows[name] = {"overall": time.time() - work_time}

            # Log LLM usage for this workflow if available
            if name in context.stats.llm_usage_by_workflow:
                usage = context.stats.llm_usage_by_workflow[name]
                retry_part = (
                    f", {usage['retries']} retries"
                    if usage.get("retries", 0) > 0
                    else ""
                )
                logger.info(
                    "Workflow %s LLM usage: %d calls, %d prompt tokens, %d completion tokens%s",
                    name,
                    usage["llm_calls"],
                    usage["prompt_tokens"],
                    usage["completion_tokens"],
                    retry_part,
                )

            if result.stop:
                logger.info("Halting pipeline at workflow request")
                break

        # Clear current workflow
        context.current_workflow = None
        context.stats.total_runtime = time.time() - start_time
        logger.info("Indexing pipeline complete.")

        # Log total LLM usage
        if context.stats.total_llm_calls > 0:
            retry_part = (
                f", {context.stats.total_llm_retries} retries"
                if context.stats.total_llm_retries > 0
                else ""
            )
            logger.info(
                "Total LLM usage: %d calls, %d prompt tokens, %d completion tokens%s",
                context.stats.total_llm_calls,
                context.stats.total_prompt_tokens,
                context.stats.total_completion_tokens,
                retry_part,
            )

        await _dump_json(context)

    except Exception as e:
        logger.exception("error running workflow %s", last_workflow)
        yield PipelineRunResult(
            workflow=last_workflow, result=None, state=context.state, errors=[e]
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
    storage: PipelineStorage,
    copy_storage: PipelineStorage,
):
    for file in storage.find(re.compile(r"\.parquet$")):
        base_name = file[0].replace(".parquet", "")
        table = await load_table_from_storage(base_name, storage)
        await write_table_to_storage(table, base_name, copy_storage)
