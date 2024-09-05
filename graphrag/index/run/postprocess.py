# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Post Processing functions for the GraphRAG run module."""

from typing import cast

import pandas as pd
from datashaper import DEFAULT_INPUT_NAME, WorkflowCallbacks

from graphrag.index.config.input import PipelineInputConfigTypes
from graphrag.index.config.workflow import PipelineWorkflowStep
from graphrag.index.context import PipelineRunContext
from graphrag.index.workflows.load import create_workflow


def _create_postprocess_steps(
    config: PipelineInputConfigTypes | None,
) -> list[PipelineWorkflowStep] | None:
    """Retrieve the post process steps for the pipeline."""
    return config.post_process if config is not None else None


async def _run_post_process_steps(
    post_process: list[PipelineWorkflowStep] | None,
    dataset: pd.DataFrame,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
) -> pd.DataFrame:
    """Run the pipeline.

    Args:
        - post_process - The post process steps to run
        - dataset - The dataset to run the steps on
        - context - The pipeline run context
    Returns:
        - output - The dataset after running the post process steps
    """
    if post_process:
        input_workflow = create_workflow(
            "Input Post Process",
            post_process,
        )
        input_workflow.add_table(DEFAULT_INPUT_NAME, dataset)
        await input_workflow.run(
            context=context,
            callbacks=callbacks,
        )
        dataset = cast(pd.DataFrame, input_workflow.output())
    return dataset
