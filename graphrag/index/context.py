# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

# isort: skip_file
"""A module containing the 'PipelineRunStats' and 'PipelineRunContext' models."""

from dataclasses import dataclass as dc_dataclass
from dataclasses import field

from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.storage.pipeline_storage import PipelineStorage


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
    "Long-term storage for pipeline verbs to use. Items written here will be written to the storage provider."
    cache: PipelineCache
    "Cache instance for reading previous LLM responses."
    runtime_storage: PipelineStorage
    "Runtime only storage for pipeline verbs to use. Items written here will only live in memory during the current run."


# TODO: For now, just has the same props available to it
VerbRunContext = PipelineRunContext
"""Provides the context for the current verb run."""
