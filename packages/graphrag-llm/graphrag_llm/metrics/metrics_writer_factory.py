# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""Metrics writer factory."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from graphrag_common.factory import Factory

from graphrag_llm.config.types import MetricsWriterType
from graphrag_llm.metrics.metrics_writer import MetricsWriter

if TYPE_CHECKING:
    from graphrag_common.factory import ServiceScope

    from graphrag_llm.config import MetricsConfig


class MetricsWriterFactory(Factory[MetricsWriter]):
    """Metrics writer factory."""


metrics_writer_factory = MetricsWriterFactory()


def register_metrics_writer(
    metrics_writer_type: str,
    metrics_writer_initializer: Callable[..., MetricsWriter],
    scope: "ServiceScope" = "transient",
) -> None:
    """Register a custom metrics writer implementation.

    Args
    ----
        metrics_writer_type: str
            The metrics writer id to register.
        metrics_writer_initializer: Callable[..., MetricsWriter]
            The metrics writer initializer to register.
        scope: ServiceScope (default: "transient")
            The service scope for the metrics writer.
    """
    metrics_writer_factory.register(
        metrics_writer_type, metrics_writer_initializer, scope
    )


def create_metrics_writer(metrics_config: "MetricsConfig") -> MetricsWriter:
    """Create a MetricsWriter instance based on the configuration.

    Args
    ----
        metrics_config: MetricsConfig
            The configuration for the metrics writer.

    Returns
    -------
        MetricsWriter:
            An instance of a MetricsWriter subclass.
    """
    strategy = metrics_config.writer
    if not strategy:
        msg = "MetricsConfig.writer needs to be set to create a MetricsWriter."
        raise ValueError(msg)

    init_args = metrics_config.model_dump()

    if strategy not in metrics_writer_factory:
        match strategy:
            case MetricsWriterType.Log:
                from graphrag_llm.metrics.log_metrics_writer import LogMetricsWriter

                metrics_writer_factory.register(
                    strategy=MetricsWriterType.Log,
                    initializer=LogMetricsWriter,
                    scope="singleton",
                )
            case MetricsWriterType.File:
                from graphrag_llm.metrics.file_metrics_writer import FileMetricsWriter

                metrics_writer_factory.register(
                    strategy=MetricsWriterType.File,
                    initializer=FileMetricsWriter,
                    scope="singleton",
                )
            case _:
                msg = f"MetricsConfig.writer '{strategy}' is not registered in the MetricsWriterFactory. Registered strategies: {', '.join(metrics_writer_factory.keys())}"
                raise ValueError(msg)

    return metrics_writer_factory.create(strategy=strategy, init_args=init_args)
