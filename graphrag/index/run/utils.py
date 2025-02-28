# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Utility functions for the GraphRAG run module."""

from graphrag.cache.memory_pipeline_cache import InMemoryCache
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.callbacks.progress_workflow_callbacks import ProgressWorkflowCallbacks
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.callbacks.workflow_callbacks_manager import WorkflowCallbacksManager
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.state import PipelineState
from graphrag.index.typing.stats import PipelineRunStats
from graphrag.logger.base import ProgressLogger
from graphrag.storage.memory_pipeline_storage import MemoryPipelineStorage
from graphrag.storage.pipeline_storage import PipelineStorage


def create_run_context(
    storage: PipelineStorage | None = None,
    cache: PipelineCache | None = None,
    callbacks: WorkflowCallbacks | None = None,
    stats: PipelineRunStats | None = None,
    state: PipelineState | None = None,
) -> PipelineRunContext:
    """Create the run context for the pipeline."""
    return PipelineRunContext(
        stats=stats or PipelineRunStats(),
        cache=cache or InMemoryCache(),
        storage=storage or MemoryPipelineStorage(),
        callbacks=callbacks or NoopWorkflowCallbacks(),
        state=state or {},
    )


def create_callback_chain(
    callbacks: list[WorkflowCallbacks] | None, progress: ProgressLogger | None
) -> WorkflowCallbacks:
    """Create a callback manager that encompasses multiple callbacks."""
    manager = WorkflowCallbacksManager()
    for callback in callbacks or []:
        manager.register(callback)
    if progress is not None:
        manager.register(ProgressWorkflowCallbacks(progress))
    return manager
