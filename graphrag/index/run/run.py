# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Different methods to run the pipeline."""

import gc
import logging
import time
import traceback
from collections.abc import AsyncIterable
from typing import cast

import pandas as pd
from datashaper import WorkflowCallbacks

from graphrag.index.cache import InMemoryCache, PipelineCache
from graphrag.index.config import (
    PipelineConfig,
    PipelineWorkflowReference,
    PipelineWorkflowStep,
)
from graphrag.index.context import PipelineRunStats
from graphrag.index.emit import TableEmitterType, create_table_emitters
from graphrag.index.load_pipeline_config import load_pipeline_config
from graphrag.index.progress import NullProgressReporter, ProgressReporter
from graphrag.index.reporting import (
    ConsoleWorkflowCallbacks,
)
from graphrag.index.run.cache import _create_cache
from graphrag.index.run.postprocess import (
    _create_postprocess_steps,
    _run_post_process_steps,
)
from graphrag.index.run.profiling import _dump_stats, _write_workflow_stats
from graphrag.index.run.storage import _create_storage
from graphrag.index.run.utils import (
    _apply_substitutions,
    _create_input,
    _create_run_context,
    _validate_dataset,
    _create_reporter,
)
from graphrag.index.run.workflow import (
    _create_callback_chain,
    _emit_workflow_output,
    _inject_workflow_data_dependencies,
)
from graphrag.index.storage import MemoryPipelineStorage, PipelineStorage
from graphrag.index.typing import PipelineRunResult

# Register all verbs
from graphrag.index.workflows import (
    VerbDefinitions,
    WorkflowDefinitions,
    load_workflows,
)

log = logging.getLogger(__name__)


async def run_pipeline_with_config(
    config_or_path: PipelineConfig | str,
    workflows: list[PipelineWorkflowReference] | None = None,
    dataset: pd.DataFrame | None = None,
    storage: PipelineStorage | None = None,
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
    storage = storage or _create_storage(config.storage, root_dir=root_dir)
    cache = cache or _create_cache(config.cache, root_dir)
    callbacks = callbacks or _create_reporter(config.reporting, root_dir)
    dataset = (
        dataset
        if dataset is not None
        else await _create_input(config.input, progress_reporter, root_dir)
    )

    if is_update_run:
        # TODO: Filter dataset to only include new data (this should be done in the input module)
        pass
    post_process_steps = input_post_process_steps or _create_postprocess_steps(
        config.input
    )
    workflows = workflows or config.workflows

    if dataset is None:
        msg = "No dataset provided!"
        raise ValueError(msg)

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
    stats = PipelineRunStats()
    storage = storage or MemoryPipelineStorage()
    cache = cache or InMemoryCache()
    progress_reporter = progress_reporter or NullProgressReporter()
    callbacks = callbacks or ConsoleWorkflowCallbacks()
    callbacks = _create_callback_chain(callbacks, progress_reporter)
    emit = emit or [TableEmitterType.Parquet]
    emitters = create_table_emitters(
        emit,
        storage,
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

    context = _create_run_context(storage, cache, stats)

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
    stats.num_documents = len(dataset)
    last_workflow = "input"

    try:
        await _dump_stats(stats, storage)

        for workflow_to_run in workflows_to_run:
            # Try to flush out any intermediate dataframes
            gc.collect()

            workflow = workflow_to_run.workflow
            workflow_name: str = workflow.name
            last_workflow = workflow_name

            log.info("Running workflow: %s...", workflow_name)

            if is_resume_run and await storage.has(
                f"{workflow_to_run.workflow.name}.parquet"
            ):
                log.info("Skipping %s because it already exists", workflow_name)
                continue

            stats.workflows[workflow_name] = {"overall": 0.0}
            await _inject_workflow_data_dependencies(
                workflow, workflow_dependencies, dataset, storage
            )

            workflow_start_time = time.time()
            result = await workflow.run(context, callbacks)
            await _write_workflow_stats(
                workflow, result, workflow_start_time, start_time, stats, storage
            )

            # Save the output from the workflow
            output = await _emit_workflow_output(workflow, emitters)
            yield PipelineRunResult(workflow_name, output, None)
            output = None
            workflow.dispose()
            workflow = None

        stats.total_runtime = time.time() - start_time
        await _dump_stats(stats, storage)
    except Exception as e:
        log.exception("error running workflow %s", last_workflow)
        cast(WorkflowCallbacks, callbacks).on_error(
            "Error running pipeline!", e, traceback.format_exc()
        )
        yield PipelineRunResult(last_workflow, None, [e])
