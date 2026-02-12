# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Utility functions for the GraphRAG run module."""

from graphrag_cache import Cache
from graphrag_cache.memory_cache import MemoryCache
from graphrag_storage import Storage, create_storage
from graphrag_storage.memory_storage import MemoryStorage
from graphrag_storage.tables.parquet_table_provider import ParquetTableProvider
from graphrag_storage.tables.table_provider import TableProvider
from graphrag_storage.tables.table_provider_factory import create_table_provider

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.callbacks.workflow_callbacks_manager import WorkflowCallbacksManager
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.state import PipelineState
from graphrag.index.typing.stats import PipelineRunStats


def create_run_context(
    input_storage: Storage | None = None,
    output_storage: Storage | None = None,
    output_table_provider: TableProvider | None = None,
    previous_table_provider: TableProvider | None = None,
    cache: Cache | None = None,
    callbacks: WorkflowCallbacks | None = None,
    stats: PipelineRunStats | None = None,
    state: PipelineState | None = None,
) -> PipelineRunContext:
    """Create the run context for the pipeline."""
    input_storage = input_storage or MemoryStorage()
    output_storage = output_storage or MemoryStorage()
    return PipelineRunContext(
        input_storage=input_storage,
        output_storage=output_storage,
        output_table_provider=output_table_provider
        or ParquetTableProvider(storage=output_storage),
        previous_table_provider=previous_table_provider,
        cache=cache or MemoryCache(),
        callbacks=callbacks or NoopWorkflowCallbacks(),
        stats=stats or PipelineRunStats(),
        state=state or {},
    )


def create_callback_chain(
    callbacks: list[WorkflowCallbacks] | None,
) -> WorkflowCallbacks:
    """Create a callback manager that encompasses multiple callbacks."""
    manager = WorkflowCallbacksManager()
    for callback in callbacks or []:
        manager.register(callback)
    return manager


def get_update_table_providers(
    config: GraphRagConfig, timestamp: str
) -> tuple[TableProvider, TableProvider, TableProvider]:
    """Get table providers for the update index run."""
    output_storage = create_storage(config.output_storage)
    update_storage = create_storage(config.update_output_storage)
    timestamped_storage = update_storage.child(timestamp)
    delta_storage = timestamped_storage.child("delta")
    previous_storage = timestamped_storage.child("previous")

    output_table_provider = create_table_provider(config.table_provider, output_storage)
    previous_table_provider = create_table_provider(
        config.table_provider, previous_storage
    )
    delta_table_provider = create_table_provider(config.table_provider, delta_storage)

    return output_table_provider, previous_table_provider, delta_table_provider
