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

from graphrag.callbacks.progress_workflow_callbacks import ProgressWorkflowCallbacks
from graphrag.index.config.pipeline import PipelineConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.exporter import ParquetExporter
from graphrag.index.run.profiling import _write_workflow_stats
from graphrag.index.typing import PipelineRunResult
from graphrag.logging.base import ProgressReporter
from graphrag.storage.pipeline_storage import PipelineStorage
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
        try:
            table = await _load_table_from_storage(f"{id}.parquet", storage)
        except ValueError:
            # our workflows allow for transient tables, and we avoid putting those in storage
            # however, we need to keep the table in the dependency list for proper execution order.
            # this allows us to catch missing table errors and issue a warning for pipeline users who may genuinely have an error (which we expect to be very rare)
            # todo: this issue will resolve itself once we remove DataShaper completely
            log.warning(
                "Dependency table %s not found in storage: it may be a runtime-only in-memory table. If you see further errors, this may be an actual problem.",
                id,
            )
            table = pd.DataFrame()
        workflow.add_table(workflow_id, table)


async def _export_workflow_output(
    workflow: Workflow, exporter: ParquetExporter
) -> pd.DataFrame:
    """Export the output from each step of the workflow."""
    output = cast("pd.DataFrame", workflow.output())
    # only write final output that is not empty (i.e. has content)
    # NOTE: this design is intentional - it accounts for workflow steps with "side effects" that don't produce a formal output to save
    if not output.empty:
        await exporter.export(workflow.name, output)
    return output


def _create_callback_chain(
    callbacks: list[WorkflowCallbacks] | None, progress: ProgressReporter | None
) -> WorkflowCallbacks:
    """Create a callback manager that encompasses multiple callbacks."""
    manager = WorkflowCallbacksManager()
    for callback in callbacks or []:
        manager.register(callback)
    if progress is not None:
        manager.register(ProgressWorkflowCallbacks(progress))
    return manager


async def _process_workflow(
    workflow: Workflow,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
    exporter: ParquetExporter,
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
    output = await _export_workflow_output(workflow, exporter)
    workflow.dispose()
    return PipelineRunResult(workflow_name, output, None)


def _find_workflow_config(
    config: PipelineConfig, workflow_name: str, step: str | None = None
) -> dict:
    """Find a workflow in the pipeline configuration.

    Parameters
    ----------
    config : PipelineConfig
        The pipeline configuration.
    workflow_name : str
        The name of the workflow.
    step : str
        The step in the workflow.

    Returns
    -------
    dict
        The workflow configuration.
    """
    try:
        workflow = next(
            filter(lambda workflow: workflow.name == workflow_name, config.workflows)
        )
    except StopIteration as err:
        error_message = (
            f"Workflow {workflow_name} not found in the pipeline configuration."
        )
        raise ValueError(error_message) from err

    if not workflow.config:
        return {}
    return workflow.config if not step else workflow.config.get(step, {})
