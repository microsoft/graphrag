# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Workflow functions for the GraphRAG update module."""

import logging
import time
from typing import cast

import pandas as pd
from datashaper import (
    DEFAULT_INPUT_NAME,
    Workflow,
    WorkflowCallbacks,
    WorkflowCallbacksManager,
)

from graphrag.index.context import PipelineRunContext
from graphrag.index.emit.table_emitter import TableEmitter
from graphrag.index.progress.types import ProgressReporter
from graphrag.index.reporting.progress_workflow_callbacks import (
    ProgressWorkflowCallbacks,
)
from graphrag.index.run.profiling import _write_workflow_stats
from graphrag.index.storage.typing import PipelineStorage
from graphrag.index.typing import PipelineRunResult
from graphrag.utils.storage import _load_table_from_storage

log = logging.getLogger(__name__)


async def _inject_workflow_data_dependencies(
    workflow: Workflow,
    workflow_dependencies: dict[str, list[str]],
    dataset: pd.DataFrame,
    storage: PipelineStorage,
) -> None:
    """Inject the data dependencies into the workflow."""
    workflow.add_table(DEFAULT_INPUT_NAME, dataset)
    deps = workflow_dependencies[workflow.name]
    log.info("dependencies for %s: %s", workflow.name, deps)
    for id in deps:
        workflow_id = f"workflow:{id}"
        table = await _load_table_from_storage(f"{id}.parquet", storage)
        workflow.add_table(workflow_id, table)


async def _emit_workflow_output(
    workflow: Workflow, emitters: list[TableEmitter]
) -> pd.DataFrame:
    """Emit the workflow output."""
    output = cast(pd.DataFrame, workflow.output())
    for emitter in emitters:
        await emitter.emit(workflow.name, output)
    return output


def _create_callback_chain(
    callbacks: WorkflowCallbacks | None, progress: ProgressReporter | None
) -> WorkflowCallbacks:
    """Create a callbacks manager."""
    manager = WorkflowCallbacksManager()
    if callbacks is not None:
        manager.register(callbacks)
    if progress is not None:
        manager.register(ProgressWorkflowCallbacks(progress))
    return manager


async def _process_workflow(
    workflow: Workflow,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
    emitters: list[TableEmitter],
    workflow_dependencies: dict[str, list[str]],
    dataset: pd.DataFrame,
    start_time: float,
    is_resume_run: bool,
):
    workflow_name = workflow.name
    if is_resume_run and await context.storage.has(f"{workflow_name}.parquet"):
        log.info("Skipping %s because it already exists", workflow_name)
        return None

    context.stats.workflows[workflow_name] = {"overall": 0.0}
    await _inject_workflow_data_dependencies(
        workflow, workflow_dependencies, dataset, context.storage
    )

    workflow_start_time = time.time()
    result = await workflow.run(context, callbacks)
    await _write_workflow_stats(
        workflow,
        result,
        workflow_start_time,
        start_time,
        context.stats,
        context.storage,
    )

    # Save the output from the workflow
    output = await _emit_workflow_output(workflow, emitters)
    workflow.dispose()
    return PipelineRunResult(workflow_name, output, None)
