# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Metrics store factory."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from graphrag_common.factory import Factory

from graphrag_llm.config.types import MetricsStoreType
from graphrag_llm.metrics.metrics_store import MetricsStore

if TYPE_CHECKING:
    from graphrag_common.factory import ServiceScope

    from graphrag_llm.config import MetricsConfig
    from graphrag_llm.metrics.metrics_writer import MetricsWriter


class MetricsStoreFactory(Factory[MetricsStore]):
    """Factory for creating MetricsProcessor instances."""


metrics_store_factory = MetricsStoreFactory()


def register_metrics_store(
    store_type: str,
    store_initializer: Callable[..., MetricsStore],
    scope: "ServiceScope" = "transient",
) -> None:
    """Register a custom metrics store implementation.

    Args
    ----
        store_type: str
            The metrics store id to register.
        store_initializer: Callable[..., MetricsStore]
            The metrics store initializer to register.
    """
    metrics_store_factory.register(store_type, store_initializer, scope)


def create_metrics_store(config: "MetricsConfig", id: str) -> MetricsStore:
    """Create a MetricsStore instance based on the configuration.

    Args
    ----
        config: MetricsConfig
            The configuration for the metrics store.
        id: str
            The identifier for the metrics store.
            Example: openai/gpt-4o

    Returns
    -------
        MetricsStore:
            An instance of a MetricsStore subclass.
    """
    strategy = config.store
    metrics_writer: MetricsWriter | None = None
    if config.writer:
        from graphrag_llm.metrics.metrics_writer_factory import create_metrics_writer

        metrics_writer = create_metrics_writer(config)
    init_args: dict[str, Any] = config.model_dump()

    if strategy not in metrics_store_factory:
        match strategy:
            case MetricsStoreType.Memory:
                from graphrag_llm.metrics.memory_metrics_store import MemoryMetricsStore

                register_metrics_store(
                    store_type=strategy,
                    store_initializer=MemoryMetricsStore,
                    scope="singleton",
                )
            case _:
                msg = f"MetricsConfig.store '{strategy}' is not registered in the MetricsStoreFactory. Registered strategies: {', '.join(metrics_store_factory.keys())}"
                raise ValueError(msg)

    return metrics_store_factory.create(
        strategy=strategy,
        init_args={
            **init_args,
            "id": id,
            "metrics_config": config,
            "metrics_writer": metrics_writer,
        },
    )
