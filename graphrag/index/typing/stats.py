# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Pipeline stats types."""

from dataclasses import dataclass, field


@dataclass
class PipelineRunStats:
    """Pipeline running stats."""

    total_runtime: float = field(default=0)
    """Float representing the total runtime."""

    num_documents: int = field(default=0)
    """Number of documents."""
    update_documents: int = field(default=0)
    """Number of update documents."""

    input_load_time: float = field(default=0)
    """Float representing the input load time."""

    workflows: dict[str, dict[str, float]] = field(default_factory=dict)
    """A dictionary of workflows."""

    total_llm_calls: int = field(default=0)
    """Total number of LLM calls across all workflows."""

    total_prompt_tokens: int = field(default=0)
    """Total prompt tokens used across all workflows."""

    total_completion_tokens: int = field(default=0)
    """Total completion tokens generated across all workflows."""

    total_llm_retries: int = field(default=0)
    """Total number of LLM retry attempts across all workflows (sum of failed attempts before each success)."""

    llm_usage_by_workflow: dict[str, dict[str, int]] = field(default_factory=dict)
    """LLM usage breakdown by workflow. Structure:
    {
        "extract_graph": {
            "llm_calls": 10,
            "prompt_tokens": 5000,
            "completion_tokens": 2000,
            "retries": 3
        },
        ...
    }
    """
