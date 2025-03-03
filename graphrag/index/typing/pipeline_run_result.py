# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the PipelineRunResult class."""

from dataclasses import dataclass
from typing import Any

from graphrag.index.typing.state import PipelineState


@dataclass
class PipelineRunResult:
    """Pipeline run result class definition."""

    workflow: str
    """The name of the workflow that was executed."""
    result: Any | None
    """The result of the workflow function. This can be anything - we use it only for logging downstream, and expect each workflow function to write official outputs to the provided storage."""
    state: PipelineState
    """Ongoing pipeline context state object."""
    errors: list[BaseException] | None
