# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the 'PipelineRunResult' model."""

from collections.abc import Awaitable, Callable, Generator
from dataclasses import dataclass

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext

ErrorHandlerFn = Callable[[BaseException | None, str | None, dict | None], None]

WorkflowFunction = Callable[
    [GraphRagConfig, PipelineRunContext, WorkflowCallbacks],
    Awaitable[pd.DataFrame | None],
]
Workflow = tuple[str, WorkflowFunction]

Pipeline = Generator[Workflow]


@dataclass
class PipelineRunResult:
    """Pipeline run result class definition."""

    workflow: str
    result: pd.DataFrame | None
    errors: list[BaseException] | None
