# Copyright (C) 2025 Microsoft
# Licensed under the MIT License

"""Workflow profiling utilities."""

import time
import tracemalloc
from types import TracebackType
from typing import Self

from graphrag.index.typing.stats import WorkflowMetrics


class WorkflowProfiler:
    """Context manager for profiling workflow execution.

    Captures timing and memory metrics using tracemalloc. Designed to wrap
    workflow execution in run_pipeline with minimal code intrusion.

    Example
    -------
        with WorkflowProfiler() as profiler:
            result = await workflow_function(config, context)
        metrics = profiler.metrics
    """

    def __init__(self) -> None:
        self._start_time: float = 0.0
        self._elapsed: float = 0.0
        self._peak_memory: int = 0
        self._current_memory: int = 0
        self._tracemalloc_overhead: int = 0

    def __enter__(self) -> Self:
        """Start profiling: begin tracemalloc and record start time."""
        tracemalloc.start()
        self._start_time = time.time()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Stop profiling: capture metrics and stop tracemalloc."""
        self._elapsed = time.time() - self._start_time
        self._current_memory, self._peak_memory = tracemalloc.get_traced_memory()
        self._tracemalloc_overhead = tracemalloc.get_tracemalloc_memory()
        tracemalloc.stop()

    @property
    def metrics(self) -> WorkflowMetrics:
        """Return collected metrics as a WorkflowMetrics dataclass."""
        return WorkflowMetrics(
            overall=self._elapsed,
            peak_memory_bytes=self._peak_memory,
            memory_delta_bytes=self._current_memory,
            tracemalloc_overhead_bytes=self._tracemalloc_overhead,
        )
