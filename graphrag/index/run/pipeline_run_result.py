# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the PipelineRunResult class."""

from dataclasses import dataclass
from typing import Any

from graphrag.config.models.graph_rag_config import GraphRagConfig


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
