# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Workflow functions for the GraphRAG update module."""

import logging
from typing import cast

import pandas as pd
from datashaper import (
    DEFAULT_INPUT_NAME,
    Workflow,
    WorkflowCallbacks,
    WorkflowCallbacksManager,
)

from graphrag.index.emit.table_emitter import TableEmitter
from graphrag.index.progress.types import ProgressReporter
from graphrag.index.reporting.progress_workflow_callbacks import (
    ProgressWorkflowCallbacks,
)
from graphrag.index.run.storage import _load_table_from_storage
from graphrag.index.storage.typing import PipelineStorage

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
