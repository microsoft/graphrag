# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

# isort: skip_file
"""A module containing the 'PipelineRunContext' models."""

from dataclasses import dataclass

from graphrag_cache import Cache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.typing.state import PipelineState
from graphrag.index.typing.stats import PipelineRunStats
from graphrag_storage import Storage, TableProvider


@dataclass
class PipelineRunContext:
    """Provides the context for the current pipeline run."""

    stats: PipelineRunStats
    input_storage: Storage
    "Storage for reading input documents."
    output_storage: Storage
    "Long-term storage for pipeline verbs to use. Items written here will be written to the storage provider."
    output_table_provider: TableProvider
    "Table provider for reading and writing output tables."
    previous_table_provider: TableProvider | None
    "Table provider for reading previous pipeline run when running in update mode."
    cache: Cache
    "Cache instance for reading previous LLM responses."
    callbacks: WorkflowCallbacks
    "Callbacks to be called during the pipeline run."
    state: PipelineState
    "Arbitrary property bag for runtime state, persistent pre-computes, or experimental features."
