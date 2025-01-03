# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Utility functions for the GraphRAG run module."""

from graphrag.cache.memory_pipeline_cache import InMemoryCache
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.progress_workflow_callbacks import ProgressWorkflowCallbacks
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.callbacks.workflow_callbacks_manager import WorkflowCallbacksManager
from graphrag.index.context import PipelineRunContext, PipelineRunStats
from graphrag.logger.base import ProgressLogger
from graphrag.storage.memory_pipeline_storage import MemoryPipelineStorage
from graphrag.storage.pipeline_storage import PipelineStorage


def create_run_context(
    storage: PipelineStorage | None,
    cache: PipelineCache | None,
    stats: PipelineRunStats | None,
) -> PipelineRunContext:
    """Create the run context for the pipeline."""
    return PipelineRunContext(
        stats=stats or PipelineRunStats(),
        cache=cache or InMemoryCache(),
        storage=storage or MemoryPipelineStorage(),
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
