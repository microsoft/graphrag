# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Noop metrics store."""

from typing import Any

from graphrag_llm.metrics.metrics_store import MetricsStore
from graphrag_llm.types import Metrics


class NoopMetricsStore(MetricsStore):
    """Noop store for metrics."""

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """Initialize NoopMetricsStore."""

    @property
    def id(self) -> str:
        """Get the ID of the metrics store."""
        return ""

    def update_metrics(self, *, metrics: Metrics) -> None:
        """Noop update."""
        return

    def get_metrics(self) -> Metrics:
        """Noop get all metrics from the store."""
        return {}

    def clear_metrics(self) -> None:
        """Clear all metrics from the store.

        Returns
        -------
            None
        """
        return
