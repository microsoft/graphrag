# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

# isort: skip_file
"""A module containing the 'PipelineRunStats' and 'PipelineRunContext' models."""

from dataclasses import dataclass as dc_dataclass
from dataclasses import field

from .cache import PipelineCache
from .storage.typing import PipelineStorage


@dc_dataclass
class PipelineRunStats:
    """Pipeline running stats."""

    total_runtime: float = field(default=0)
    """Float representing the total runtime."""

    num_documents: int = field(default=0)
    """Number of documents."""

    input_load_time: float = field(default=0)
    """Float representing the input load time."""

    workflows: dict[str, dict[str, float]] = field(default_factory=dict)
    """A dictionary of workflows."""


@dc_dataclass
class PipelineRunContext:
    """Provides the context for the current pipeline run."""

    stats: PipelineRunStats
    storage: PipelineStorage
    cache: PipelineCache


# TODO: For now, just has the same props available to it
VerbRunContext = PipelineRunContext
"""Provides the context for the current verb run."""
