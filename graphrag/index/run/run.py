# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Different methods to run the pipeline."""

import gc
import logging
import time
import traceback
from collections.abc import AsyncIterable
from pathlib import Path
from typing import cast

import pandas as pd
from datashaper import NoopVerbCallbacks, WorkflowCallbacks

from graphrag.callbacks.console_workflow_callbacks import ConsoleWorkflowCallbacks
from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.config.pipeline import (
    PipelineConfig,
    PipelineWorkflowReference,
)
from graphrag.index.config.workflow import PipelineWorkflowStep
from graphrag.index.emit.factories import create_table_emitters
from graphrag.index.emit.types import TableEmitterType
from graphrag.index.load_pipeline_config import load_pipeline_config
from graphrag.index.run.cache import _create_cache
from graphrag.index.run.postprocess import (
    _create_postprocess_steps,
    _run_post_process_steps,
)
from graphrag.index.run.profiling import _dump_stats
from graphrag.index.run.utils import (
    _apply_substitutions,
    _create_input,
    _create_reporter,
    _validate_dataset,
    create_run_context,
)
from graphrag.index.run.workflow import (
    _create_callback_chain,
    _process_workflow,
)
from graphrag.index.storage.pipeline_storage import PipelineStorage
from graphrag.index.typing import PipelineRunResult
from graphrag.index.update.incremental_index import (
    get_delta_docs,
    update_dataframe_outputs,
)
from graphrag.index.workflows import (
    VerbDefinitions,
    WorkflowDefinitions,
    load_workflows,
)
from graphrag.logging.base import ProgressReporter
from graphrag.logging.null_progress import NullProgressReporter
from graphrag.utils.storage import _create_storage

log = logging.getLogger(__name__)


async def run_pipeline_with_config(
    config_or_path: PipelineConfig | str,
    workflows: list[PipelineWorkflowReference] | None = None,
    dataset: pd.DataFrame | None = None,
    storage: PipelineStorage | None = None,
    update_index_storage: PipelineStorage | None = None,
    cache: PipelineCache | None = None,
    callbacks: WorkflowCallbacks | None = None,
    progress_reporter: ProgressReporter | None = None,
    input_post_process_steps: list[PipelineWorkflowStep] | None = None,
    additional_verbs: VerbDefinitions | None = None,
    additional_workflows: WorkflowDefinitions | None = None,
    emit: list[TableEmitterType] | None = None,
    memory_profile: bool = False,
    run_id: str | None = None,
    is_resume_run: bool = False,
    is_update_run: bool = False,
    **_kwargs: dict,
) -> AsyncIterable[PipelineRunResult]:
    """Run a pipeline with the given config.

    Args:
        - config_or_path - The config to run the pipeline with
        - workflows - The workflows to run (this overrides the config)
        - dataset - The dataset to run the pipeline on (this overrides the config)
        - storage - The storage to use for the pipeline (this overrides the config)
        - cache - The cache to use for the pipeline (this overrides the config)
        - reporter - The reporter to use for the pipeline (this overrides the config)
        - input_post_process_steps - The post process steps to run on the input data (this overrides the config)
        - additional_verbs - The custom verbs to use for the pipeline.
        - additional_workflows - The custom workflows to use for the pipeline.
        - emit - The table emitters to use for the pipeline.
        - memory_profile - Whether or not to profile the memory.
        - run_id - The run id to start or resume from.
    """
    if isinstance(config_or_path, str):
        log.info("Running pipeline with config %s", config_or_path)
    else:
        log.info("Running pipeline")

    run_id = run_id or time.strftime("%Y%m%d-%H%M%S")
    config = load_pipeline_config(config_or_path)
    config = _apply_substitutions(config, run_id)
    root_dir = config.root_dir or ""

    progress_reporter = progress_reporter or NullProgressReporter()
    storage = storage or _create_storage(config.storage, root_dir=Path(root_dir))

    if is_update_run:
        update_index_storage = update_index_storage or _create_storage(
            config.update_index_storage, root_dir=Path(root_dir)
        )

    cache = cache or _create_cache(config.cache, root_dir)
    callbacks = callbacks or _create_reporter(config.reporting, root_dir)
    dataset = (
        dataset
        if dataset is not None
        else await _create_input(config.input, progress_reporter, root_dir)
    )

    post_process_steps = input_post_process_steps or _create_postprocess_steps(
        config.input
    )
    workflows = workflows or config.workflows

    if dataset is None:
        msg = "No dataset provided!"
        raise ValueError(msg)

    if is_update_run and update_index_storage:
        delta_dataset = await get_delta_docs(dataset, storage)

        # Fail on empty delta dataset
        if delta_dataset.new_inputs.empty:
            error_msg = "Incremental Indexing Error: No new documents to process."
            raise ValueError(error_msg)

        delta_storage = update_index_storage.child("delta")

        # Run the pipeline on the new documents
        tables_dict = {}
        async for table in run_pipeline(
            workflows=workflows,
            dataset=delta_dataset.new_inputs,
            storage=delta_storage,
            cache=cache,
            callbacks=callbacks,
            input_post_process_steps=post_process_steps,
            memory_profile=memory_profile,
            additional_verbs=additional_verbs,
            additional_workflows=additional_workflows,
            progress_reporter=progress_reporter,
            emit=emit,
            is_resume_run=False,
        ):
            tables_dict[table.workflow] = table.result

        progress_reporter.success("Finished running workflows on new documents.")
        await update_dataframe_outputs(
            dataframe_dict=tables_dict,
            storage=storage,
            update_storage=update_index_storage,
            config=config,
            cache=cache,
            callbacks=NoopVerbCallbacks(),
            progress_reporter=progress_reporter,
        )

    else:
        async for table in run_pipeline(
            workflows=workflows,
            dataset=dataset,
            storage=storage,
            cache=cache,
            callbacks=callbacks,
            input_post_process_steps=post_process_steps,
            memory_profile=memory_profile,
            additional_verbs=additional_verbs,
            additional_workflows=additional_workflows,
            progress_reporter=progress_reporter,
            emit=emit,
            is_resume_run=is_resume_run,
        ):
            yield table


async def run_pipeline(
    workflows: list[PipelineWorkflowReference],
    dataset: pd.DataFrame,
    storage: PipelineStorage | None = None,
    cache: PipelineCache | None = None,
    callbacks: WorkflowCallbacks | None = None,
    progress_reporter: ProgressReporter | None = None,
    input_post_process_steps: list[PipelineWorkflowStep] | None = None,
    additional_verbs: VerbDefinitions | None = None,
    additional_workflows: WorkflowDefinitions | None = None,
    emit: list[TableEmitterType] | None = None,
    memory_profile: bool = False,
    is_resume_run: bool = False,
    **_kwargs: dict,
) -> AsyncIterable[PipelineRunResult]:
    """Run the pipeline.

    Args:
        - workflows - The workflows to run
        - dataset - The dataset to run the pipeline on, specifically a dataframe with the following columns at a minimum:
            - id - The id of the document
            - text - The text of the document
            - title - The title of the document
            These must exist after any post process steps are run if there are any!
        - storage - The storage to use for the pipeline
        - cache - The cache to use for the pipeline
        - reporter - The reporter to use for the pipeline
        - input_post_process_steps - The post process steps to run on the input data
        - additional_verbs - The custom verbs to use for the pipeline
        - additional_workflows - The custom workflows to use for the pipeline
        - debug - Whether or not to run in debug mode
    Returns:
        - output - An iterable of workflow results as they complete running, as well as any errors that occur
    """
    start_time = time.time()

    context = create_run_context(storage=storage, cache=cache, stats=None)

    progress_reporter = progress_reporter or NullProgressReporter()
    callbacks = callbacks or ConsoleWorkflowCallbacks()
    callbacks = _create_callback_chain(callbacks, progress_reporter)
    # TODO: This default behavior is already defined at the API level. Update tests
    # of this function to pass in an emit type before removing this default setting.
    emit = emit or [TableEmitterType.Parquet]
    emitters = create_table_emitters(
        emit,
        context.storage,
        lambda e, s, d: cast(WorkflowCallbacks, callbacks).on_error(
            "Error emitting table", e, s, d
        ),
    )
    loaded_workflows = load_workflows(
        workflows,
        additional_verbs=additional_verbs,
        additional_workflows=additional_workflows,
        memory_profile=memory_profile,
    )
    workflows_to_run = loaded_workflows.workflows
    workflow_dependencies = loaded_workflows.dependencies

    if len(emitters) == 0:
        log.info(
            "No emitters provided. No table outputs will be generated. This is probably not correct."
        )

    dataset = await _run_post_process_steps(
        input_post_process_steps, dataset, context, callbacks
    )

    # Make sure the incoming data is valid
    _validate_dataset(dataset)

    log.info("Final # of rows loaded: %s", len(dataset))
    context.stats.num_documents = len(dataset)
    last_workflow = "input"

    try:
        await _dump_stats(context.stats, context.storage)

        for workflow_to_run in workflows_to_run:
            # Try to flush out any intermediate dataframes
            gc.collect()

            last_workflow = workflow_to_run.workflow.name
            result = await _process_workflow(
                workflow_to_run.workflow,
                context,
                callbacks,
                emitters,
                workflow_dependencies,
                dataset,
                start_time,
                is_resume_run,
            )
            if result:
                yield result

        context.stats.total_runtime = time.time() - start_time
        await _dump_stats(context.stats, context.storage)
    except Exception as e:
        log.exception("error running workflow %s", last_workflow)
        cast(WorkflowCallbacks, callbacks).on_error(
            "Error running pipeline!", e, traceback.format_exc()
        )
        yield PipelineRunResult(last_workflow, None, [e])
