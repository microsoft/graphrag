# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Default metrics store."""

import atexit
import threading
from typing import TYPE_CHECKING, Any

from graphrag_llm.metrics.metrics_aggregator import metrics_aggregator
from graphrag_llm.metrics.metrics_store import MetricsStore

if TYPE_CHECKING:
    from graphrag_llm.metrics.metrics_writer import MetricsWriter
    from graphrag_llm.types import Metrics

_default_sort_order: list[str] = [
    "attempted_request_count",
    "successful_response_count",
    "failed_response_count",
    "failure_rate",
    "requests_with_retries",
    "retries",
    "retry_rate",
    "compute_duration_seconds",
    "compute_duration_per_response_seconds",
    "runtime_duration_seconds",
    "cached_responses",
    "cache_hit_rate",
    "streaming_responses",
    "responses_with_tokens",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "tokens_per_response",
    "responses_with_cost",
    "input_cost",
    "output_cost",
    "total_cost",
    "cost_per_response",
]


class MemoryMetricsStore(MetricsStore):
    """Store for metrics."""

    _metrics_writer: "MetricsWriter | None" = None
    _id: str
    _sort_order: list[str]
    _thread_lock: threading.Lock
    _metrics: "Metrics"

    def __init__(
        self,
        *,
        id: str,
        metrics_writer: "MetricsWriter | None" = None,
        sort_order: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize MemoryMetricsStore."""
        self._id = id
        self._sort_order = sort_order or _default_sort_order
        self._thread_lock = threading.Lock()
        self._metrics = {}

        if metrics_writer:
            self._metrics_writer = metrics_writer
            atexit.register(self._on_exit_)

    def _on_exit_(self) -> None:
        if self._metrics_writer:
            self._metrics_writer.write_metrics(id=self._id, metrics=self.get_metrics())

    @property
    def id(self) -> str:
        """Get the ID of the metrics store."""
        return self._id

    def update_metrics(self, *, metrics: "Metrics") -> None:
        """Update the store with multiple metrics."""
        with self._thread_lock:
            for name, value in metrics.items():
                if name in self._metrics:
                    self._metrics[name] += value
                else:
                    self._metrics[name] = value

    def _sort_metrics(self) -> "Metrics":
        """Sort metrics based on the predefined sort order."""
        sorted_metrics: Metrics = {}
        for key in self._sort_order:
            if key in self._metrics:
                sorted_metrics[key] = self._metrics[key]
        for key in self._metrics:
            if key not in sorted_metrics:
                sorted_metrics[key] = self._metrics[key]
        return sorted_metrics

    def get_metrics(self) -> "Metrics":
        """Get all metrics from the store."""
        metrics_aggregator.aggregate(self._metrics)
        return self._sort_metrics()

    def clear_metrics(self) -> None:
        """Clear all metrics from the store.

        Returns
        -------
            None
        """
        self._metrics = {}
