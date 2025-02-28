# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for pipeline state passthrough."""

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.run.utils import create_run_context
from graphrag.index.typing import WorkflowFunctionOutput
from graphrag.index.workflows.factory import PipelineFactory
from tests.verbs.util import DEFAULT_MODEL_CONFIG


async def run_workflow_1(  # noqa: RUF029
    _config: GraphRagConfig, context: PipelineRunContext, _callbacks: WorkflowCallbacks
):
    context.state["count"] = 1
    return WorkflowFunctionOutput(result=None)


async def run_workflow_2(  # noqa: RUF029
    _config: GraphRagConfig, context: PipelineRunContext, _callbacks: WorkflowCallbacks
):
    context.state["count"] += 1
    return WorkflowFunctionOutput(result=None)


async def test_pipeline_state():
    # checks that we can update the arbitrary state block within the pipeline run context
    PipelineFactory.register("workflow_1", run_workflow_1)
    PipelineFactory.register("workflow_2", run_workflow_2)

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})
    config.workflows = ["workflow_1", "workflow_2"]
    callbacks = NoopWorkflowCallbacks()
    context = await create_run_context(None, None, None, None)

    for _, fn in PipelineFactory.create_pipeline(config).run():
        await fn(config, context, callbacks)

    assert context.state["count"] == 2
