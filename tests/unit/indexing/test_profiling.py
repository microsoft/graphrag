# Copyright (C) 2025 Microsoft
# Licensed under the MIT License

"""Unit tests for WorkflowProfiler."""

import time

from graphrag.index.run.profiling import WorkflowProfiler
from graphrag.index.typing.stats import WorkflowMetrics


class TestWorkflowProfiler:
    """Tests for the WorkflowProfiler context manager."""

    def test_captures_time(self):
        """Verify profiler captures elapsed time."""
        with WorkflowProfiler() as profiler:
            time.sleep(0.05)  # Sleep 50ms

        metrics = profiler.metrics
        assert metrics.overall >= 0.05
        assert metrics.overall < 0.5  # Should not take too long

    def test_captures_peak_memory(self):
        """Verify profiler captures peak memory from allocations."""
        with WorkflowProfiler() as profiler:
            # Allocate ~1MB of data
            data = [0] * (1024 * 1024 // 8)  # 1M integers ≈ 8MB on 64-bit
            _ = data  # Keep reference to prevent GC

        metrics = profiler.metrics
        assert metrics.peak_memory_bytes > 0

    def test_captures_memory_delta(self):
        """Verify profiler captures memory delta (current allocation)."""
        with WorkflowProfiler() as profiler:
            _data = [0] * 10000  # Keep allocation in scope

        metrics = profiler.metrics
        # Memory delta should be non-negative
        assert metrics.memory_delta_bytes >= 0

    def test_captures_tracemalloc_overhead(self):
        """Verify profiler captures tracemalloc's own memory overhead."""
        with WorkflowProfiler() as profiler:
            _ = list(range(1000))

        metrics = profiler.metrics
        assert metrics.tracemalloc_overhead_bytes > 0

    def test_returns_workflow_metrics_dataclass(self):
        """Verify profiler.metrics returns a WorkflowMetrics instance."""
        with WorkflowProfiler() as profiler:
            pass

        metrics = profiler.metrics
        assert isinstance(metrics, WorkflowMetrics)

    def test_all_metrics_populated(self):
        """Verify all four metrics are populated after profiling."""
        with WorkflowProfiler() as profiler:
            _ = list(range(100))

        metrics = profiler.metrics
        assert metrics.overall >= 0
        assert metrics.peak_memory_bytes >= 0
        assert metrics.memory_delta_bytes >= 0
        assert metrics.tracemalloc_overhead_bytes >= 0

    def test_handles_exception_in_context(self):
        """Verify profiler captures metrics even when exception is raised."""
        profiler: WorkflowProfiler | None = None
        try:
            with WorkflowProfiler() as profiler:
                _ = [0] * 1000
                msg = "Test exception"
                raise ValueError(msg)
        except ValueError:
            pass

        assert profiler is not None
        metrics = profiler.metrics
        assert metrics.overall > 0
        assert metrics.peak_memory_bytes > 0

    def test_multiple_profilers_independent(self):
        """Verify multiple profiler instances don't interfere."""
        with WorkflowProfiler() as profiler1:
            time.sleep(0.02)

        with WorkflowProfiler() as profiler2:
            time.sleep(0.04)

        # profiler2 should have longer time
        assert profiler2.metrics.overall > profiler1.metrics.overall
