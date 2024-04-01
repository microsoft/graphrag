#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

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
