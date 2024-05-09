# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'WorkflowToRun' model."""

from collections.abc import Callable
from dataclasses import dataclass as dc_dataclass
from typing import Any

from datashaper import TableContainer, Workflow

StepDefinition = dict[str, Any]
"""A step definition."""

VerbDefinitions = dict[str, Callable[..., TableContainer]]
"""A mapping of verb names to their implementations."""

WorkflowConfig = dict[str, Any]
"""A workflow configuration."""

WorkflowDefinitions = dict[str, Callable[[WorkflowConfig], list[StepDefinition]]]
"""A mapping of workflow names to their implementations."""

VerbTiming = dict[str, float]
"""The timings of verbs by id."""


@dc_dataclass
class WorkflowToRun:
    """Workflow to run class definition."""

    workflow: Workflow
    config: dict[str, Any]
