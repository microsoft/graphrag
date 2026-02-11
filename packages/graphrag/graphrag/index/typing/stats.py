# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Pipeline stats types."""

from dataclasses import dataclass, field


@dataclass
class WorkflowMetrics:
    """Metrics collected for a single workflow execution."""

    overall: float
    """Wall-clock time in seconds."""

    peak_memory_bytes: int
    """Peak memory usage during workflow execution (tracemalloc)."""

    memory_delta_bytes: int
    """Net memory change after workflow completion (tracemalloc)."""

    tracemalloc_overhead_bytes: int
    """Memory used by tracemalloc itself for tracking allocations."""


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

    workflows: dict[str, WorkflowMetrics] = field(default_factory=dict)
    """Metrics for each workflow execution."""
