# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Pipeline workflow types."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.typing.context import PipelineRunContext


@dataclass
class WorkflowFunctionOutput:
    """Data container for Workflow function results."""

    result: Any | None
    """The result of the workflow function. This can be anything - we use it only for logging downstream, and expect each workflow function to write official outputs to the provided storage."""


WorkflowFunction = Callable[
    [GraphRagConfig, PipelineRunContext],
    Awaitable[WorkflowFunctionOutput],
]
Workflow = tuple[str, WorkflowFunction]
