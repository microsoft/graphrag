# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'PipelineWorkflowReference' model."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

PipelineWorkflowConfig = dict[str, Any]
"""Represent a configuration for a workflow."""


class PipelineWorkflowReference(BaseModel):
    """Represent a reference to a workflow, and can optionally be the workflow itself."""

    name: str | None = Field(description="Name of the workflow.", default=None)
    """Name of the workflow."""

    config: PipelineWorkflowConfig | None = Field(
        description="The optional configuration for the workflow.", default=None
    )
    """The optional configuration for the workflow."""
