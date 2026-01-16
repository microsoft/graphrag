# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Metrics writer abstract base class."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graphrag_llm.types import Metrics


class MetricsWriter(ABC):
    """Abstract base class for metrics writers."""

    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        """Initialize MetricsWriter."""
        raise NotImplementedError

    @abstractmethod
    def write_metrics(self, *, id: str, metrics: "Metrics") -> None:
        """Write the given metrics.

        Args
        ----
            id : str
                The identifier for the metrics.
            metrics : Metrics
                The metrics data to write.
        """
        raise NotImplementedError
