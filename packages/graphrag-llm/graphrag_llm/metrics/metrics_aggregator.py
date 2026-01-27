# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Metrics aggregator module."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

from typing_extensions import Self

if TYPE_CHECKING:
    from graphrag_llm.types.types import Metrics


class MetricsAggregator:
    """Metrics Aggregator."""

    _instance: ClassVar["Self | None"] = None
    _aggregate_functions: dict[str, Callable[["Metrics"], None]]

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        """Create a new instance of MetricsAggregator if it does not exist."""
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._aggregate_functions = {}

    def register(self, name: str, func: Callable[["Metrics"], None]) -> None:
        """Register an aggregate function.

        Args
        ----
            name: str
                The name of the aggregate function.
            func: Callable[[Metrics], None]
                The aggregate function to register. It should take a Metrics
                dictionary as input and return None, modifying the Metrics in place.
        """
        self._aggregate_functions[name] = func

    def clear(self, name: str | None = None) -> None:
        """Clear registered aggregate functions.

        Args
        ----
            name: str | None
                The name of the aggregate function to clear. If None, clears all
                registered aggregate functions.

        """
        if name:
            self._aggregate_functions.pop(name, None)
        else:
            self._aggregate_functions.clear()

    def aggregate(self, metrics: "Metrics") -> None:
        """Aggregate metrics using registered aggregate functions.

        Args
        ----
            metrics: Metrics
                The metrics dictionary to aggregate.
        """
        for func in self._aggregate_functions.values():
            func(metrics)


def _failure_rate(metrics: "Metrics") -> None:
    """Calculate failure rate metric."""
    attempted = metrics.get("attempted_request_count", 0)
    failed = metrics.get("failed_response_count", 0)
    if attempted > 0:
        metrics["failure_rate"] = failed / attempted
    else:
        metrics["failure_rate"] = 0.0


def _retry_rate(metrics: "Metrics") -> None:
    """Calculate failure rate metric."""
    attempted = metrics.get("attempted_request_count", 0)
    retries = metrics.get("retries", 0)
    if attempted > 0 and "retries" in metrics:
        metrics["retry_rate"] = retries / (retries + attempted)
    elif "retries" in metrics:
        metrics["retry_rate"] = 0.0


def _tokens_per_response(metrics: "Metrics") -> None:
    """Calculate tokens per response metric."""
    responses = metrics.get("responses_with_tokens", 0)
    total_tokens = metrics.get("total_tokens", 0)
    if responses > 0:
        metrics["tokens_per_response"] = total_tokens / responses
    else:
        metrics["tokens_per_response"] = 0.0


def _cost_per_response(metrics: "Metrics") -> None:
    """Calculate cost per response metric."""
    responses = metrics.get("responses_with_cost", 0)
    total_cost = metrics.get("total_cost", 0)
    if responses > 0:
        metrics["cost_per_response"] = total_cost / responses
    else:
        metrics["cost_per_response"] = 0.0


def _compute_duration_per_response(metrics: "Metrics") -> None:
    """Calculate compute duration per response metric."""
    responses = metrics.get("successful_response_count", 0)
    streaming_responses = metrics.get("streaming_responses", 0)
    responses = responses - streaming_responses
    compute_duration = metrics.get("compute_duration_seconds", 0)
    if responses > 0:
        metrics["compute_duration_per_response_seconds"] = compute_duration / responses
    else:
        metrics["compute_duration_per_response_seconds"] = 0.0


def _cache_hit_rate(metrics: "Metrics") -> None:
    """Calculate cache hit rate metric."""
    responses = metrics.get("successful_response_count", 0)
    cached = metrics.get("cached_responses", 0)
    if responses > 0:
        metrics["cache_hit_rate"] = cached / responses
    else:
        metrics["cache_hit_rate"] = 0.0


metrics_aggregator = MetricsAggregator()
metrics_aggregator.register("failure_rate", _failure_rate)
metrics_aggregator.register("retry_rate", _retry_rate)
metrics_aggregator.register("tokens_per_response", _tokens_per_response)
metrics_aggregator.register("cost_per_response", _cost_per_response)
metrics_aggregator.register(
    "compute_duration_per_response", _compute_duration_per_response
)
metrics_aggregator.register("cache_hit_rate", _cache_hit_rate)
