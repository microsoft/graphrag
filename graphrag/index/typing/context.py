# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

# isort: skip_file
"""A module containing the 'PipelineRunContext' models."""

from dataclasses import dataclass

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.typing.state import PipelineState
from graphrag.index.typing.stats import PipelineRunStats
from graphrag.storage.pipeline_storage import PipelineStorage


@dataclass
class PipelineRunContext:
    """Provides the context for the current pipeline run."""

    stats: PipelineRunStats
    input_storage: PipelineStorage
    "Storage for input documents."
    output_storage: PipelineStorage
    "Long-term storage for pipeline verbs to use. Items written here will be written to the storage provider."
    previous_storage: PipelineStorage
    "Storage for previous pipeline run when running in update mode."
    cache: PipelineCache
    "Cache instance for reading previous LLM responses."
    callbacks: WorkflowCallbacks
    "Callbacks to be called during the pipeline run."
    state: PipelineState
    "Arbitrary property bag for runtime state, persistent pre-computes, or experimental features."
    current_workflow: str | None = None
    "Current workflow being executed (for LLM usage tracking)."

    def record_llm_usage(
        self,
        llm_calls: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        """
        Record LLM usage for the current workflow.

        Args
        ----
            llm_calls: Number of LLM calls
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
        """
        if self.current_workflow is None:
            return

        # Update totals
        self.stats.total_llm_calls += llm_calls
        self.stats.total_prompt_tokens += prompt_tokens
        self.stats.total_completion_tokens += completion_tokens

        # Update workflow-specific stats
        if self.current_workflow not in self.stats.llm_usage_by_workflow:
            self.stats.llm_usage_by_workflow[self.current_workflow] = {
                "llm_calls": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "retries": 0,
            }

        workflow_stats = self.stats.llm_usage_by_workflow[self.current_workflow]
        workflow_stats["llm_calls"] += llm_calls
        workflow_stats["prompt_tokens"] += prompt_tokens
        workflow_stats["completion_tokens"] += completion_tokens

    def record_llm_retries(self, retry_count: int) -> None:
        """Record LLM retry attempts for the current workflow.

        Args
        ----
            retry_count: Number of retry attempts performed before a success.
        """
        if self.current_workflow is None or retry_count <= 0:
            return

        # Update totals
        self.stats.total_llm_retries += retry_count

        # Update workflow-specific stats
        if self.current_workflow not in self.stats.llm_usage_by_workflow:
            self.stats.llm_usage_by_workflow[self.current_workflow] = {
                "llm_calls": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "retries": 0,
            }
        workflow_stats = self.stats.llm_usage_by_workflow[self.current_workflow]
        workflow_stats["retries"] += retry_count
