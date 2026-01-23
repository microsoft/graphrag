# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Utility functions for the GraphRAG run module."""

from graphrag_cache import Cache
from graphrag_cache.memory_cache import MemoryCache
from graphrag_storage import ParquetTableProvider, Storage, create_storage
from graphrag_storage.memory_storage import MemoryStorage

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
    previous_storage: Storage | None = None,
    cache: Cache | None = None,
    callbacks: WorkflowCallbacks | None = None,
    stats: PipelineRunStats | None = None,
    state: PipelineState | None = None,
) -> PipelineRunContext:
    """Create the run context for the pipeline."""
    output_storage = output_storage or MemoryStorage()
    return PipelineRunContext(
        input_storage=input_storage or MemoryStorage(),
        output_storage=output_storage,
        output_table_provider=ParquetTableProvider(storage=output_storage),
        previous_storage=previous_storage or MemoryStorage(),
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


def get_update_storages(
    config: GraphRagConfig, timestamp: str
) -> tuple[Storage, Storage, Storage]:
    """Get storage objects for the update index run."""
    output_storage = create_storage(config.output)
    update_storage = create_storage(config.update_output_storage)
    timestamped_storage = update_storage.child(timestamp)
    delta_storage = timestamped_storage.child("delta")
    previous_storage = timestamped_storage.child("previous")

    return output_storage, previous_storage, delta_storage
