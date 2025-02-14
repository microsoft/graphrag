# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the 'PipelineRunResult' model."""

from collections.abc import Awaitable, Callable, Generator
from dataclasses import dataclass
from typing import Any

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext

ErrorHandlerFn = Callable[[BaseException | None, str | None, dict | None], None]


@dataclass
class WorkflowFunctionOutput:
    """Data container for Workflow function results."""

    result: Any | None
    """The result of the workflow function. This can be anything - we use it only for logging downstream, and expect each workflow function to write official outputs to the provided storage."""
    config: GraphRagConfig | None
    """If the config is mutated, return the mutated config here. This allows users to design workflows that tune config for downstream workflow use."""


WorkflowFunction = Callable[
    [GraphRagConfig, PipelineRunContext, WorkflowCallbacks],
    Awaitable[WorkflowFunctionOutput],
]
Workflow = tuple[str, WorkflowFunction]

Pipeline = Generator[Workflow]


@dataclass
class PipelineRunResult:
    """Pipeline run result class definition."""

    workflow: str
    """The name of the workflow that was executed."""
    result: Any | None
    """The result of the workflow function. This can be anything - we use it only for logging downstream, and expect each workflow function to write official outputs to the provided storage."""
    config: GraphRagConfig | None
    """Final config after running the workflow, which may have been mutated."""
    errors: list[BaseException] | None
