# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Metrics Store."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graphrag_llm.metrics.metrics_writer import MetricsWriter
    from graphrag_llm.types import Metrics


class MetricsStore(ABC):
    """Abstract base class for metrics stores."""

    @abstractmethod
    def __init__(
        self,
        *,
        id: str,
        metrics_writer: "MetricsWriter | None" = None,
        **kwargs: Any,
    ) -> None:
        """Initialize MetricsStore.

        Args
        ----
            id: str
                The ID of the metrics store.
                One metric store is created per ID so a good
                candidate is the model id (e.g., openai/gpt-4o).
                That way one store tracks and aggregates the metrics
                per model.
            metrics_writer: MetricsWriter
                The metrics writer to use for writing metrics.

        """
        raise NotImplementedError

    @property
    @abstractmethod
    def id(self) -> str:
        """Get the ID of the metrics store."""
        raise NotImplementedError

    @abstractmethod
    def update_metrics(self, *, metrics: "Metrics") -> None:
        """Update the store with multiple metrics.

        Args
        ----
            metrics: Metrics
                The metrics to merge into the store.

        Returns
        -------
            None
        """
        raise NotImplementedError

    @abstractmethod
    def get_metrics(self) -> "Metrics":
        """Get all metrics from the store.

        Returns
        -------
            Metrics:
                All metrics stored in the store.
        """
        raise NotImplementedError

    @abstractmethod
    def clear_metrics(self) -> None:
        """Clear all metrics from the store.

        Returns
        -------
            None
        """
        raise NotImplementedError
