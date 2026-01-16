# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Metrics processor factory."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from graphrag_common.factory import Factory

from graphrag_llm.config.types import MetricsProcessorType
from graphrag_llm.metrics.metrics_processor import MetricsProcessor

if TYPE_CHECKING:
    from graphrag_llm.config import MetricsConfig


class MetricsProcessorFactory(Factory[MetricsProcessor]):
    """Factory for creating MetricsProcessor instances."""


metrics_processor_factory = MetricsProcessorFactory()


def register_metrics_processor(
    processor_type: str,
    processor_initializer: Callable[..., MetricsProcessor],
) -> None:
    """Register a custom metrics processor implementation.

    Args
    ----
        processor_type: str
            The metrics processor id to register.
        processor_initializer: Callable[..., MetricsProcessor]
            The metrics processor initializer to register.
    """
    metrics_processor_factory.register(processor_type, processor_initializer)


def create_metrics_processor(metrics_config: "MetricsConfig") -> MetricsProcessor:
    """Create a MetricsProcessor instance based on the configuration.

    Args
    ----
        metrics_config: MetricsConfig
            The configuration for the metrics processor.

    Returns
    -------
        MetricsProcessor:
            An instance of a MetricsProcessor subclass.
    """
    strategy = metrics_config.type
    init_args = metrics_config.model_dump()

    if strategy not in metrics_processor_factory:
        match strategy:
            case MetricsProcessorType.Default:
                from graphrag_llm.metrics.default_metrics_processor import (
                    DefaultMetricsProcessor,
                )

                metrics_processor_factory.register(
                    strategy=MetricsProcessorType.Default,
                    initializer=DefaultMetricsProcessor,
                    scope="singleton",
                )
            case _:
                msg = f"MetricsConfig.processor '{strategy}' is not registered in the MetricsProcessorFactory. Registered strategies: {', '.join(metrics_processor_factory.keys())}"
                raise ValueError(msg)

    return metrics_processor_factory.create(
        strategy=strategy,
        init_args={
            **init_args,
            "metrics_config": metrics_config,
        },
    )
